#!/usr/bin/env python3
"""soutu_http_probe.py — 免浏览器的以图搜源 HTTP 探针（纯标准库）

把五个搜图 provider 的 HTTP 协议收进一个可跑脚本，浏览器只在「需要登录态 / 过
Cloudflare 挑战」时才出场：

    yandex     multipart 直传 → SSR data-state 解析 → 来源质量三级分选 + 域名去重
    soutubot   搜图Bot酱 schema 2.2（factor/阈值/标题回退链/链接回退链）
    saucenao   output_type=2 + dbmask 位掩码 + 配额感知
    ascii2d    /search/file（color）→ 可切 /bovw/ 特征检索；纯 HTML 解析
    safebooru  DAPI 关键词检索（免 Key）

典型用法::

    # 单源
    python soutu_http_probe.py yandex --image F:/x.jpg
    python soutu_http_probe.py soutubot --image F:/x.jpg --factor 1.4
    python soutu_http_probe.py saucenao --image F:/x.jpg --dbmask 0
    python soutu_http_probe.py safebooru --tags "cat_ears 1girl"

    # 一次跑完（yandex + soutubot [+ saucenao]，各自成段）
    python soutu_http_probe.py auto --image F:/x.jpg --json

    # 复用 turnstile-bypass 导出的 cf_clearance（UA 必须与解挑战时一致）
    python soutu_http_probe.py soutubot --image F:/x.jpg \
        --cookie-jar <HERMES_HOME>/cache/scratch/soutubot_jar.txt \
        --ua "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:152.0) Gecko/20100101 Firefox/152.0"

    # 走代理（本机 v2rayN 一般 127.0.0.1:10808）
    python soutu_http_probe.py yandex --image F:/x.jpg --proxy http://127.0.0.1:10808

    python soutu_http_probe.py --self-test     # 离线自检，不联网

约定：
- 只读、只查，不下载原图、不写库。
- 输出里「相似图」永远不冒称「来源」：Yandex 结果里没有高价值域名时会显式告警。
- 撞 Cloudflare 时抛可读错误（非 JSON = 挑战页），不静默当 0 命中。
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import socket
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Any, Iterable

# Windows 控制台默认 cp936，日文标题会直接抛 UnicodeEncodeError
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except Exception:  # noqa: BLE001
        pass

VERSION = "1.0.0"

# Camoufox 默认 UA —— 复用 cf_clearance 时**必须**与解挑战时一致，否则 403
CAMOUFOX_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:152.0) Gecko/20100101 Firefox/152.0"
)
BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)

DEFAULT_TIMEOUT = 30
MAX_IMAGE_BYTES = 20 * 1024 * 1024


# ---------------------------------------------------------------------------
# 数据模型
# ---------------------------------------------------------------------------
@dataclass
class SourceLevel:
    HIGH = "high"
    NEUTRAL = "neutral"
    LOW = "low"


LEVEL_LABEL = {
    SourceLevel.HIGH: "图库/来源",
    SourceLevel.NEUTRAL: "相关",
    SourceLevel.LOW: "相似图",
}
LEVEL_RANK = {SourceLevel.HIGH: 0, SourceLevel.NEUTRAL: 1, SourceLevel.LOW: 2}


@dataclass
class Result:
    title: str = ""
    source: str = ""
    url: str = ""
    thumbnail: str | None = None
    score: float | None = None
    extra: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "title": self.title,
            "source": self.source,
            "url": self.url,
            "thumbnail": self.thumbnail,
            "score": self.score,
            "extra": self.extra,
        }


@dataclass
class Outcome:
    provider: str
    results: list[Result] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    meta: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "provider": self.provider,
            "results": [r.as_dict() for r in self.results],
            "warnings": self.warnings,
            "meta": self.meta,
        }


class HttpError(RuntimeError):
    """网络层/协议层失败，带可读中文原因。"""


# ---------------------------------------------------------------------------
# Cookie jar（turnstile-bypass human_click.py 导出的 Netscape 格式）
# ---------------------------------------------------------------------------
def load_netscape_cookies(path: str) -> list[dict]:
    cookies: list[dict] = []
    if not path:
        return cookies
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            lines = fh.readlines()
    except OSError as exc:
        raise HttpError(f"读取 cookie jar 失败: {exc}") from exc
    now = time.time()
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#HttpOnly_"):
            line = line[len("#HttpOnly_") :]
        elif line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) < 7:
            continue
        domain, _flag, cpath, secure, expires, name, value = parts[:7]
        try:
            exp = int(float(expires))
        except ValueError:
            exp = 0
        if exp and exp < now:
            continue  # 过期的不发
        cookies.append(
            {
                "domain": domain.lstrip(".").lower(),
                "path": cpath or "/",
                "secure": str(secure).upper() == "TRUE",
                "name": name,
                "value": value,
            }
        )
    return cookies


def cookie_header_for(cookies: Iterable[dict], host: str) -> str:
    host = (host or "").lower()
    picked = []
    for ck in cookies or []:
        dom = ck["domain"]
        if host == dom or host.endswith("." + dom):
            picked.append(f"{ck['name']}={ck['value']}")
    return "; ".join(picked)


# ---------------------------------------------------------------------------
# HTTP 层
# ---------------------------------------------------------------------------
class Http:
    def __init__(
        self,
        *,
        timeout: int = DEFAULT_TIMEOUT,
        proxy: str | None = None,
        cookie_jar: str | None = None,
        ua: str | None = None,
    ) -> None:
        self.timeout = max(5, int(timeout))
        self.proxy = proxy or None
        self.cookies = load_netscape_cookies(cookie_jar) if cookie_jar else []
        self.ua_override = ua or None
        self.ctx = ssl.create_default_context()
        handlers: list[Any] = []
        if self.proxy:
            handlers.append(urllib.request.ProxyHandler({"http": self.proxy, "https": self.proxy}))
        handlers.append(urllib.request.HTTPSHandler(context=self.ctx))
        self.opener = urllib.request.build_opener(*handlers)

    def request(
        self,
        url: str,
        *,
        method: str = "GET",
        body: bytes | None = None,
        headers: dict | None = None,
        ua: str | None = None,
        referer: str | None = None,
        accept: str | None = None,
    ) -> tuple[int, bytes, str, dict]:
        """返回 (status, body_bytes, final_url, resp_headers)。非 2xx 也返回，由调用方判定。"""
        host = urllib.parse.urlparse(url).hostname or ""
        hdrs: dict[str, str] = {
            "User-Agent": ua or self.ua_override or BROWSER_UA,
            "Accept-Language": "zh-CN,zh;q=0.9,ja;q=0.8,en;q=0.7",
        }
        if accept:
            hdrs["Accept"] = accept
        if referer:
            hdrs["Referer"] = referer
        ck = cookie_header_for(self.cookies, host)
        if ck:
            hdrs["Cookie"] = ck
        for k, v in (headers or {}).items():
            if v is None:
                continue
            hdrs[k] = v
        req = urllib.request.Request(url, data=body, headers=hdrs, method=method)
        try:
            with self.opener.open(req, timeout=self.timeout) as resp:
                raw = resp.read()
                return resp.status, raw, resp.geturl(), dict(resp.headers.items())
        except urllib.error.HTTPError as exc:
            raw = b""
            try:
                raw = exc.read()
            except Exception:  # noqa: BLE001
                pass
            return exc.code, raw, url, dict(exc.headers.items()) if exc.headers else {}
        except (urllib.error.URLError, socket.timeout, TimeoutError) as exc:
            reason = getattr(exc, "reason", exc)
            raise HttpError(f"网络错误: {reason}（{url}）") from exc
        except ssl.SSLError as exc:
            raise HttpError(f"TLS 失败: {exc}（{url}）") from exc


def build_multipart(
    fields: dict[str, str] | None = None,
    files: list[tuple[str, str, str, bytes]] | None = None,
) -> tuple[bytes, str]:
    """手工拼 multipart body：显式长度（避免 chunked 触发部分站点的 413）。

    files: [(field_name, filename, mime, bytes)]
    """
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    chunks: list[bytes] = []
    for name, value in (fields or {}).items():
        chunks.append(
            (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
                f"{value}\r\n"
            ).encode("utf-8")
        )
    for name, filename, mime, data in files or []:
        chunks.append(
            (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'
                f"Content-Type: {mime}\r\n\r\n"
            ).encode("utf-8")
        )
        chunks.append(data)
        chunks.append(b"\r\n")
    chunks.append(f"--{boundary}--\r\n".encode("utf-8"))
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def sniff_mime(data: bytes) -> str | None:
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    if data[:2] == b"BM":
        return "image/bmp"
    return None


def ext_for(mime: str) -> str:
    return {
        "image/png": "png",
        "image/jpeg": "jpg",
        "image/gif": "gif",
        "image/webp": "webp",
        "image/bmp": "bmp",
    }.get(mime, "jpg")


def load_image(http: Http, *, image: str | None, url: str | None) -> tuple[bytes, str, str]:
    """返回 (bytes, mime, filename)。"""
    if image:
        try:
            with open(image, "rb") as fh:
                data = fh.read(MAX_IMAGE_BYTES + 1)
        except OSError as exc:
            raise HttpError(f"读取图片失败: {exc}") from exc
        if len(data) > MAX_IMAGE_BYTES:
            raise HttpError(f"图片过大（>{MAX_IMAGE_BYTES} 字节）")
        mime = sniff_mime(data)
        if mime is None:
            raise HttpError("不是可识别的图片（魔数校验失败：JPEG/PNG/GIF/WEBP/BMP）")
        name = os.path.basename(image) or f"query.{ext_for(mime)}"
        return data, mime, name
    if url:
        status, raw, final, _hdrs = http.request(
            url, accept="image/avif,image/webp,image/*,*/*;q=0.8"
        )
        if status != 200 or not raw:
            raise HttpError(f"图片直链下载失败 HTTP {status}: {url}")
        mime = sniff_mime(raw)
        if mime is None:
            raise HttpError(f"直链不是图片（魔数校验失败）: {final}")
        name = os.path.basename(urllib.parse.urlparse(final).path) or f"query.{ext_for(mime)}"
        return raw, mime, name
    raise HttpError("缺少 --image 或 --url")


# ---------------------------------------------------------------------------
# Yandex：来源质量分级
# ---------------------------------------------------------------------------
HIGH_SUFFIXES: frozenset[str] = frozenset(
    {
        # booru / 图库
        "danbooru.donmai.us", "donmai.us", "donmai.moe", "safebooru.org",
        "safebooru.donmai.us", "yande.re", "konachan.net", "konachan.com",
        "gelbooru.com", "e-shuushuu.net", "zerochan.net", "anime-pictures.net",
        "nhentai.net", "e-hentai.org", "exhentai.org", "hitomi.la",
        # 二次元画师 / 官方 / 创作平台
        "pixiv.net", "twitter.com", "x.com", "skeb.jp", "artstation.com",
        "fanbox.cc", "fantia.jp", "misskey.io", "nico.ms", "nicovideo.jp",
        "dlsite.com", "melonbooks.co.jp", "toranoana.jp", "booth.pm",
        "patreon.com", "gumroad.com",
        # 资料 / 百科
        "wikipedia.org", "fandom.com", "anidb.net", "myanimelist.net",
        "bangumi.tv", "bgm.tv", "vndb.org", "annict.jp",
        # 三次元 / 求物帖 / 视频源（本机实战常用）
        "telegra.ph", "t.me", "telegram.me", "bbs.spring-plus.net",
        "threads.com", "threads.net", "weibo.com", "weibo.cn",
        "bilibili.com", "youtube.com", "youtu.be", "instagram.com",
        "tiktok.com", "bad.news", "fxtwitter.com", "vxtwitter.com",
        # 三次元资料站 / 番号站
        "javdb.com", "javbus.com", "missav.ws", "jable.tv",
    }
)

LOW_SUFFIXES: frozenset[str] = frozenset(
    {
        "tumblr.com", "reactor.cc", "joyreactor.cc", "wattpad.com",
        "seputarundip.com", "i-model.org",
    }
)

# 品牌标签匹配：通杀所有国别/TLD 变体（pinterest.com / .ru / .co.uk / za.pinterest.com …）
LOW_BRANDS: frozenset[str] = frozenset({"pinterest", "pinimg", "duitang", "huaban"})
# 去重时把这些品牌全系聚成一个桶
FAMILY_BRANDS: frozenset[str] = frozenset({"pinterest", "pinimg"})

SIMILAR_ONLY_WARNING = (
    "未找到包含该图的图库来源，以下为视觉相似图（可尝试 SauceNAO 精确反查）"
)


def _norm_domain(value: str) -> str:
    text = str(value or "").strip().lower()
    if "://" in text:
        text = text.split("://", 1)[1]
    if "@" in text:
        text = text.split("@", 1)[1]
    for sep in ("/", "?", ":"):
        text = text.split(sep, 1)[0]
    return text.strip(".")


def _match_suffix(host: str, suffix: str) -> bool:
    return host == suffix or host.endswith("." + suffix)


def _match_brand(host: str, brand: str) -> bool:
    return brand in host.split(".")


def classify(domain: str) -> str:
    host = _norm_domain(domain)
    if not host:
        return SourceLevel.NEUTRAL
    for suffix in HIGH_SUFFIXES:
        if _match_suffix(host, suffix):
            return SourceLevel.HIGH
    for suffix in LOW_SUFFIXES:
        if _match_suffix(host, suffix):
            return SourceLevel.LOW
    for brand in LOW_BRANDS:
        if _match_brand(host, brand):
            return SourceLevel.LOW
    return SourceLevel.NEUTRAL


def _dedup_key(domain: str) -> str:
    host = _norm_domain(domain)
    if not host:
        return ""
    for brand in FAMILY_BRANDS:
        if _match_brand(host, brand):
            return brand
    return host


def clean_url(raw: str) -> str:
    if not raw:
        return ""
    try:
        parsed = urllib.parse.urlparse(raw)
        query = [(k, v) for k, v in urllib.parse.parse_qsl(parsed.query) if not k.lower().startswith("utm_")]
        return urllib.parse.urlunparse(parsed._replace(query=urllib.parse.urlencode(query)))
    except Exception:  # noqa: BLE001
        return raw


def _extract_initial_state(html_text: str) -> dict | None:
    if not html_text:
        return None
    for raw in re.findall(r'data-state="([^"]{300,})"', html_text):
        try:
            obj = json.loads(_html_unescape(raw))
        except Exception:  # noqa: BLE001
            continue
        if isinstance(obj, dict) and isinstance(obj.get("initialState"), dict):
            return obj["initialState"]
    return None


def _html_unescape(text: str) -> str:
    import html as _html

    return _html.unescape(text)


def parse_yandex_html(
    html_text: str, *, base_url: str = "https://yandex.ru", top_k: int = 5,
    max_per_domain: int = 2,
) -> Outcome:
    outcome = Outcome(provider="yandex")
    state = _extract_initial_state(html_text)
    if state is None:
        outcome.warnings.append("结果页里没有可解析的 initialState（可能被拦截、或页面结构已变）")
        return outcome

    sites = state.get("cbirSites")
    sites = sites.get("sites", []) if isinstance(sites, dict) else []
    candidates: list[tuple[int, int, Result, str]] = []
    seen: set[str] = set()
    for index, site in enumerate(sites if isinstance(sites, list) else []):
        if not isinstance(site, dict):
            continue
        url = clean_url(site.get("url") or "")
        if not url or url in seen:
            continue
        seen.add(url)
        title = str(site.get("title") or site.get("description") or "未知标题").strip() or "未知标题"
        domain = str(site.get("domain") or "网页来源").strip() or "网页来源"
        thumb = site.get("thumb")
        thumb_url = ""
        if isinstance(thumb, dict) and isinstance(thumb.get("url"), str):
            thumb_url = thumb["url"]
            if thumb_url.startswith("//"):
                thumb_url = "https:" + thumb_url
        level = classify(domain)
        results = Result(
            title=title, source=domain, url=url,
            thumbnail=thumb_url or None, score=None,
            extra={"source_level": level},
        )
        candidates.append((LEVEL_RANK[level], index, results, _dedup_key(domain)))

    outcome.meta["sites_total"] = len(sites) if isinstance(sites, list) else 0
    if not candidates:
        # 兜底：视觉相似图
        similar = state.get("cbirSimilar")
        thumbs = similar.get("thumbs", []) if isinstance(similar, dict) else []
        seen_s: set[str] = set()
        for thumb in thumbs if isinstance(thumbs, list) else []:
            if not isinstance(thumb, dict):
                continue
            raw = thumb.get("linkUrl") or thumb.get("imageUrl") or ""
            if not isinstance(raw, str) or not raw:
                continue
            if raw.startswith("/"):
                raw = base_url.rstrip("/") + raw
            url = clean_url(raw)
            if not url or url in seen_s:
                continue
            seen_s.add(url)
            outcome.results.append(
                Result(
                    title=str(thumb.get("title") or "相似图片").strip() or "相似图片",
                    source="yandex-similar", url=url, score=None,
                    extra={"source_level": SourceLevel.LOW},
                )
            )
            if len(outcome.results) >= max(1, top_k):
                break
        if outcome.results:
            outcome.warnings.append(SIMILAR_ONLY_WARNING)
        return outcome

    candidates.sort(key=lambda item: (item[0], item[1]))
    per_domain: dict[str, int] = {}
    limit = max(1, int(top_k))
    for _rank, _index, result, key in candidates:
        if per_domain.get(key, 0) >= max_per_domain:
            continue
        per_domain[key] = per_domain.get(key, 0) + 1
        outcome.results.append(result)
        if len(outcome.results) >= limit:
            break

    if not any(r.extra.get("source_level") == SourceLevel.HIGH for r in outcome.results):
        outcome.warnings.append(SIMILAR_ONLY_WARNING)
    outcome.meta["high_count"] = sum(
        1 for r in outcome.results if r.extra.get("source_level") == SourceLevel.HIGH
    )
    return outcome


def yandex_search(
    http: Http, image: bytes, *, filename: str, mime: str,
    base_url: str = "https://yandex.ru", top_k: int = 5, max_per_domain: int = 2,
    dump_html: str | None = None,
) -> Outcome:
    body, ctype = build_multipart(
        {"prg": "1"}, [("upfile", filename, mime, image)]
    )
    params = {
        "rpt": "imageview",
        "format": "json",
        "request": '{"blocks":[{"block":"b-page_type_search-by-image__link"}]}',
    }
    url = f"{base_url}/images/search?{urllib.parse.urlencode(params)}"
    status, raw, _final, _hdrs = http.request(
        url,
        method="POST",
        body=body,
        headers={"Content-Type": ctype, "Origin": base_url, "Referer": f"{base_url}/images/"},
        accept="text/html,application/json,*/*",
    )
    if status != 200:
        raise HttpError(f"Yandex 返回 HTTP {status}：{_cf_hint(raw)}")
    text = raw.decode("utf-8", "replace")

    if "<html" in text.lower():
        html_text = text
    else:
        # JSON 分支：再 GET 结果页
        try:
            payload = json.loads(text)
        except ValueError as exc:
            raise HttpError("Yandex 响应既非 HTML 也非 JSON（可能被挑战页拦截）") from exc
        blocks = payload.get("blocks") or [{}]
        cbir_id = ""
        if isinstance(blocks, list) and blocks and isinstance(blocks[0], dict):
            cbir_id = (blocks[0].get("params") or {}).get("cbirId") or ""
        if not cbir_id:
            raise HttpError("未能从 Yandex 响应中获取 cbirId")
        get_url = (
            f"{base_url}/images/search?rpt=imageview"
            f"&cbir_id={urllib.parse.quote(str(cbir_id))}&cbir_page=sites"
        )
        status2, raw2, _f2, _h2 = http.request(get_url, referer=f"{base_url}/images/")
        if status2 != 200:
            raise HttpError(f"Yandex 结果页 HTTP {status2}")
        html_text = raw2.decode("utf-8", "replace")

    if dump_html:
        try:
            with open(dump_html, "w", encoding="utf-8") as fh:
                fh.write(html_text)
        except OSError:
            pass
    return parse_yandex_html(
        html_text, base_url=base_url, top_k=top_k, max_per_domain=max_per_domain
    )


# ---------------------------------------------------------------------------
# soutubot.moe：schema 2.2
# ---------------------------------------------------------------------------
SOUTU_SOURCE_NAMES = {
    "nhentai": "NH本子", "ehentai": "E站", "jmcomic": "禁漫",
    "manhuacat": "漫画猫", "gelbooru": "Gelbooru", "yande": "Yande.re",
    "panda": "熊猫图库", "zerochan": "Zerochan", "pixiv": "Pixiv",
    "danbooru": "Danbooru", "konachan": "Konachan", "safebooru": "Safebooru",
}


def _to_float(value: Any, default: float | None = None) -> float | None:
    if value is None or isinstance(value, bool):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def soutubot_threshold(factor: str) -> float:
    return 35.0 if str(factor).strip().startswith("1.4") else 45.0


def soutubot_title(metadata: dict) -> str:
    title = metadata.get("title")
    if isinstance(title, str):
        return title.strip()
    if isinstance(title, dict):
        for key in ("japanese_or_alias", "primary"):
            value = title.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return ""


def parse_soutubot(payload: Any, *, factor: str = "1.2", min_score: float = 28.0) -> Outcome:
    outcome = Outcome(provider="soutubot")
    if not isinstance(payload, dict):
        outcome.warnings.append("接口返回数据格式异常")
        return outcome

    outcome.meta["schema_version"] = payload.get("schema_version")
    partial = bool(payload.get("partial")) or str(payload.get("status", "")).lower() == "partial"
    outcome.meta["partial"] = partial
    if partial:
        outcome.warnings.append("站点返回部分结果（partial），命中可能不完整，可重发一次")

    threshold = soutubot_threshold(factor)
    outcome.meta["threshold"] = threshold

    raw_results = payload.get("results")
    if not isinstance(raw_results, list):
        raw_results = []

    hits = 0
    for item in raw_results:
        if not isinstance(item, dict):
            continue
        segments = item.get("path_segments")
        if not isinstance(segments, list) or not segments:
            continue  # 无 path_segments = 未命中
        hits += 1
        score = _to_float(item.get("score"))
        for seg in segments:
            if not isinstance(seg, dict):
                continue
            metadata = seg.get("metadata") if isinstance(seg.get("metadata"), dict) else {}
            source_key = seg.get("source_key")
            if not source_key and isinstance(metadata.get("source"), dict):
                source_key = metadata["source"].get("key")
            source_key = str(source_key or "").strip()
            url = ""
            for key in ("page_url", "chapter_url", "source_url"):
                value = seg.get(key)
                if isinstance(value, str) and value.strip():
                    url = value.strip()
                    break
            if not url and isinstance(metadata.get("source"), dict):
                value = metadata["source"].get("url")
                if isinstance(value, str) and value.strip():
                    url = value.strip()
            if score is not None and score < min_score:
                continue
            outcome.results.append(
                Result(
                    title=soutubot_title(metadata) or "(无标题)",
                    source=SOUTU_SOURCE_NAMES.get(source_key.lower(), source_key or "未知来源"),
                    url=url,
                    thumbnail=seg.get("thumbnail_url") or None,
                    score=score,
                    extra={
                        "source_key": source_key,
                        "page_no": seg.get("page_no"),
                        "chapter_no": seg.get("chapter_no"),
                        "language": seg.get("language"),
                        "tags": metadata.get("tags"),
                        "low_confidence": score is None or score < threshold,
                        "tier": "main" if (score is not None and score >= min_score) else "low",
                    },
                )
            )
            if len(outcome.results) >= 25:
                break

    outcome.results.sort(key=lambda r: (r.score is not None, r.score or 0.0), reverse=True)
    outcome.meta["hit_count"] = hits
    outcome.meta["shown"] = len(outcome.results)
    if outcome.results and all(r.extra.get("low_confidence") for r in outcome.results):
        outcome.warnings.append(f"最佳相似度低于置信阈值（{threshold:.0f}），结果仅供参考")
    if hits and not outcome.results:
        outcome.warnings.append("有命中但分数均低于 min-score，已全部过滤")
    return outcome


def _cf_hint(raw: bytes) -> str:
    """识别 Cloudflare 挑战页，返回可读提示（不把整页 HTML 糊到输出里）。"""
    text = raw[:4000].decode("utf-8", "replace")
    low = text.lower()
    if "just a moment" in low or "challenge-platform" in low or "cf-browser-verification" in low:
        return "Cloudflare 挑战页（Just a moment）"
    if "<html" in low:
        return "返回了 HTML 而非接口数据（可能被拦截或接口已变更）"
    return text.strip()[:160]


def soutubot_search(
    http: Http, image: bytes, *, filename: str, mime: str,
    base_url: str = "https://soutubot.moe", factor: str = "1.2",
    top_k: int = 25, min_score: float = 28.0,
) -> Outcome:
    factor = "1.4" if str(factor).strip().startswith("1.4") else "1.2"
    body, ctype = build_multipart(
        {"factor": factor, "metadata_mode": "display", "top_k": str(max(1, int(top_k)))},
        [("file", filename, mime, image)],
    )
    status, raw, _final, _hdrs = http.request(
        f"{base_url}/api/search",
        method="POST",
        body=body,
        headers={"Content-Type": ctype, "Origin": base_url, "Referer": f"{base_url}/"},
        accept="application/json",
        ua=http.ua_override or CAMOUFOX_UA,  # cf_clearance 绑定 Camoufox UA
    )
    if status != 200:
        hint = "（先跑 turnstile-bypass/scripts/human_click.py 导出 jar，再带 --cookie-jar + --ua）" if status in (403, 503) else ""
        raise HttpError(f"soutubot 返回 HTTP {status}：{_cf_hint(raw)}{hint}")
    try:
        payload = json.loads(raw.decode("utf-8", "replace"))
    except (ValueError, TypeError) as exc:
        raise HttpError(
            "soutubot 返回非 JSON（可能被 Cloudflare 拦截或接口已变更）；"
            "先过挑战再重试，别当成「没搜到」"
        ) from exc
    return parse_soutubot(payload, factor=factor, min_score=min_score)


# ---------------------------------------------------------------------------
# SauceNAO
# ---------------------------------------------------------------------------
SAUCENAO_INDEX = {
    0: "h-mags", 2: "hcg", 5: "pixiv", 6: "pixivhistorical", 8: "seiga_illust",
    9: "danbooru", 12: "yande.re", 16: "FAKKU", 18: "H-MISC (nhentai)",
    25: "gelbooru", 26: "konachan", 38: "H-Misc (ehentai)", 41: "Twitter", 44: "Skeb",
}
DB_MASKS = {
    "pixiv": 0x20, "pixivhistorical": 0x40, "danbooru": 0x200,
    "yandere": 0x1000, "twitter": 0x10000000000, "nhentai": 0x20000,
    "gelbooru": 0x1000000, "konachan": 0x2000000, "ehentai": 0x2000000000,
}


def _coerce_int(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value) if value.is_integer() else None
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return int(text, 0)
        except ValueError:
            try:
                return int(text)
            except ValueError:
                return None
    return None


def parse_saucenao(payload: Any, *, min_similarity: int = 50) -> Outcome:
    outcome = Outcome(provider="saucenao")
    if not isinstance(payload, dict):
        outcome.warnings.append("接口返回数据格式异常")
        return outcome
    header = payload.get("header") if isinstance(payload.get("header"), dict) else {}
    status = _coerce_int(header.get("status"))
    outcome.meta["status"] = status
    if status not in (None, 0):
        outcome.meta["status_error"] = True
        outcome.warnings.append(
            f"SauceNAO 返回错误状态码 {status}（检查 API Key / 配额，或稍后重试）"
        )
        return outcome

    quota = {
        "short_remaining": _coerce_int(header.get("short_remaining")),
        "long_remaining": _coerce_int(header.get("long_remaining")),
        "short_limit": _coerce_int(header.get("short_limit")),
        "long_limit": _coerce_int(header.get("long_limit")),
    }
    outcome.meta["quota"] = quota
    if quota["long_remaining"] is not None and quota["long_remaining"] <= 0:
        outcome.warnings.append("今日配额已用完（免费账户 150 次/天），明天再试")
    if quota["short_remaining"] is not None and quota["short_remaining"] <= 0:
        outcome.warnings.append("触发限流（免费账户 4 次/30 秒），等约 30 秒再试")

    raw_results = payload.get("results")
    if not isinstance(raw_results, list):
        raw_results = []
    for item in raw_results:
        if not isinstance(item, dict):
            continue
        head = item.get("header") if isinstance(item.get("header"), dict) else {}
        data = item.get("data") if isinstance(item.get("data"), dict) else {}
        similarity = _to_float(head.get("similarity"))
        if similarity is not None and similarity < min_similarity:
            continue
        index_id = _coerce_int(head.get("index_id"))
        library = head.get("index_name") if isinstance(head.get("index_name"), str) else ""
        library = library.strip() or SAUCENAO_INDEX.get(index_id or -1, f"库#{index_id}" if index_id is not None else "")

        raw_ext = data.get("ext_urls")
        ext_urls = [u.strip() for u in raw_ext if isinstance(u, str) and u.strip()] if isinstance(raw_ext, list) else []
        pixiv_id = data.get("pixiv_id")
        pixiv_str = str(pixiv_id).strip() if isinstance(pixiv_id, (int, str)) and not isinstance(pixiv_id, bool) else ""
        url = ext_urls[0] if ext_urls else (
            f"https://www.pixiv.net/artworks/{pixiv_str}" if pixiv_str else str(data.get("source") or "").strip()
        )
        artist = ""
        for key in ("creator", "author_name"):
            value = data.get(key)
            if isinstance(value, str) and value.strip():
                artist = value.strip()
                break
        member = data.get("member")
        member_str = str(member).strip() if isinstance(member, (int, str)) and not isinstance(member, bool) else ""
        artist_url = data.get("author_url") if isinstance(data.get("author_url"), str) else ""
        if not artist and member_str:
            artist = member_str
        if not artist_url and member_str:
            artist_url = f"https://www.pixiv.net/users/{member_str}"
        title = ""
        for key in ("title", "eng_name", "jp_name"):
            value = data.get(key)
            if isinstance(value, str) and value.strip():
                title = value.strip()
                break
        outcome.results.append(
            Result(
                title=title or "(无标题)",
                source=f"来自 {library} 库" if library else "SauceNAO",
                url=url,
                thumbnail=head.get("thumbnail") if isinstance(head.get("thumbnail"), str) else None,
                score=similarity,
                extra={
                    "library": library,
                    "pixiv_id": pixiv_str or None,
                    "member": member_str or None,
                    "artist": artist or None,
                    "artist_url": artist_url or None,
                    "ext_urls": ext_urls,
                    "year": data.get("year"),
                    "part": data.get("part"),
                    "low_confidence": similarity is None or similarity < min_similarity,
                },
            )
        )
    outcome.results.sort(key=lambda r: (r.score is not None, r.score or 0.0), reverse=True)
    outcome.meta["shown"] = len(outcome.results)
    if not outcome.results:
        outcome.warnings.append("SauceNAO 无命中（或全部低于 min-similarity）")
    return outcome


def saucenao_search(
    http: Http, image: bytes, *, filename: str, mime: str, api_key: str,
    base_url: str = "https://saucenao.com", dbmask: int = 0, numres: int = 15,
    minsim: int = 50, hide: int = 0,
) -> Outcome:
    if not api_key:
        raise HttpError("缺少 SauceNAO API Key（--api-key 或环境变量 SAUCENAO_API_KEY）")
    params = {
        "output_type": "2",
        "numres": str(max(1, min(40, int(numres)))),
        "minsim": str(max(0, min(100, int(minsim)))),
        "hide": str(hide if hide in (0, 1, 2, 3) else 0),
        "api_key": api_key,
    }
    # 位掩码 0 = 「不启用任何库」的惯例语义，故全库时应**省略** dbmask 而不是发 0
    if int(dbmask) > 0:
        params["dbmask"] = str(int(dbmask))
    url = f"{base_url}/search.php?{urllib.parse.urlencode(params)}"
    body, ctype = build_multipart({}, [("file", filename, mime, image)])
    status, raw, _final, _hdrs = http.request(
        url,
        method="POST",
        body=body,
        headers={"Content-Type": ctype, "Referer": f"{base_url}/"},
        accept="application/json, text/javascript, */*;q=0.1",
    )
    if status != 200:
        sample = raw[:200].decode("utf-8", "replace").strip()
        raise HttpError(f"SauceNAO 返回 HTTP {status}: {sample}（大陆通常需要代理）")
    try:
        payload = json.loads(raw.decode("utf-8", "replace"))
    except (ValueError, TypeError) as exc:
        raise HttpError("SauceNAO 返回非 JSON（可能被拦截或接口已变更）") from exc
    outcome = parse_saucenao(payload, min_similarity=minsim)
    if outcome.meta.get("status_error"):
        raise HttpError(outcome.warnings[-1] if outcome.warnings else "SauceNAO 状态码错误")
    return outcome


# ---------------------------------------------------------------------------
# ascii2d
# ---------------------------------------------------------------------------
A2D_SOURCE_MARKS = ("fanbox", "fantia", "misskey", "pixiv", "twitter", "ニコニコ静画", "ニジエ")
A2D_DISPLAY = {
    "pixiv": "Pixiv", "twitter": "Twitter/X", "fanbox": "Fanbox", "fantia": "Fantia",
    "misskey": "Misskey", "ニコニコ静画": "NicoNico静画", "ニジエ": "Nijie",
}
A2D_TITLE_NOISE = ("詳細掲示板のログ", "2ちゃんねるのログ")
_VOID_TAGS = frozenset(
    {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
)
_WS = re.compile(r"\s+")


def _clean(text: Any) -> str:
    return _WS.sub(" ", str(text)).strip() if text is not None else ""


class _Ascii2dParser(HTMLParser):
    """按 item-box 作用域抽取 h6 / 外部链接 / small 来源标记 / img。"""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.items: list[dict] = []
        self.stack: list[tuple[str, set]] = []
        self.cur: dict | None = None
        self.box_depth = 0
        self.caps: list[dict] = []

    def handle_starttag(self, tag, attrs):
        tag = (tag or "").lower()
        attr_map = {k.lower(): (v or "") for k, v in attrs or [] if k}
        classes = set(str(attr_map.get("class", "")).split())
        if tag == "div" and "item-box" in classes and self.cur is None:
            self.cur = {"h6": "", "smalls": [], "img": "", "links": []}
            self.box_depth = len(self.stack) + 1
        if tag in _VOID_TAGS:
            if self.cur is not None and tag == "img" and not self.cur["img"]:
                src = _clean(attr_map.get("src"))
                if src:
                    self.cur["img"] = src
            return
        self.stack.append((tag, classes))
        if self.cur is None:
            return
        if tag in ("h6", "small", "a"):
            frame = {"kind": tag, "buf": []}
            if tag == "a":
                frame["href"] = _clean(attr_map.get("href"))
                self.cur["links"].append(frame)
            self.caps.append(frame)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        tag = (tag or "").lower()
        if tag in _VOID_TAGS:
            return
        if self.stack:
            self.stack.pop()
        if self.cur is not None and self.caps:
            # 关掉与当前 tag 对应的捕获帧（容错：找最后一个同名帧）
            for idx in range(len(self.caps) - 1, -1, -1):
                if self.caps[idx]["kind"] == tag:
                    frame = self.caps.pop(idx)
                    text = _clean("".join(frame["buf"]))
                    if tag == "h6" and not self.cur["h6"]:
                        self.cur["h6"] = text
                    elif tag == "small":
                        self.cur["smalls"].append(text)
                    elif tag == "a":
                        frame["text"] = text
                    break
        if self.cur is not None and len(self.stack) < self.box_depth:
            self.items.append(self.cur)
            self.cur = None
            self.caps.clear()
            self.box_depth = 0

    def handle_data(self, data):
        if not data or not self.caps:
            return
        for frame in self.caps:
            frame["buf"].append(data)


def parse_ascii2d_html(html_text: str, *, base_url: str = "https://ascii2d.net", top_k: int = 10) -> Outcome:
    outcome = Outcome(provider="ascii2d")
    if not (html_text or "").strip():
        outcome.warnings.append("站点返回空响应（可能被拦截或接口已变更）")
        return outcome
    parser = _Ascii2dParser()
    try:
        parser.feed(html_text)
        parser.close()
    except Exception:  # noqa: BLE001
        pass
    if parser.cur is not None:
        parser.items.append(parser.cur)
    outcome.meta["raw_count"] = len(parser.items)

    base_host = urllib.parse.urlparse(base_url).hostname or "ascii2d.net"
    for raw in parser.items:
        mark = ""
        detail = ""
        for small in raw.get("smalls", []):
            low = small.lower()
            for candidate in A2D_SOURCE_MARKS:
                if low == candidate.lower() and not mark:
                    mark = candidate
                    break
            if not mark and not detail and small:
                detail = small
        external = []
        for link in raw.get("links", []):
            href = link.get("href") or ""
            if href.startswith(("http://", "https://")) and base_host not in href:
                external.append(link)
        title = raw.get("h6") or (external[0].get("text") if external else "") or detail
        if any(noise in title for noise in A2D_TITLE_NOISE):
            title = ""
        url = external[0].get("href") if external else ""
        author = external[1].get("text") if len(external) > 1 else ""
        author_url = external[1].get("href") if len(external) > 1 else ""
        thumb = raw.get("img") or ""
        if thumb.startswith("/"):
            thumb = base_url.rstrip("/") + thumb
        outcome.results.append(
            Result(
                title=title or "(无标题)",
                source=A2D_DISPLAY.get(mark, "ascii2d"),
                url=url or "",
                thumbnail=thumb or None,
                score=None,  # ascii2d 不给分数，也**不要**套 SauceNAO 的阈值过滤
                extra={
                    "source_mark": mark or None,
                    "detail": detail or None,
                    "author": author or None,
                    "author_url": author_url or None,
                },
            )
        )
        if len(outcome.results) >= max(1, top_k):
            break
    if not outcome.results:
        outcome.warnings.append("未解析到任何 item-box（0 条）")
    return outcome


def ascii2d_search(
    http: Http, image: bytes, *, filename: str, mime: str,
    base_url: str = "https://ascii2d.net", bovw: bool = False,
    top_k: int = 10, dump_html: str | None = None,
) -> Outcome:
    body, ctype = build_multipart({}, [("file", filename, mime, image)])
    status, raw, final_url, _hdrs = http.request(
        f"{base_url}/search/file",
        method="POST",
        body=body,
        headers={
            "Content-Type": ctype,
            "Origin": base_url,
            "Referer": f"{base_url}/",
            "Accept-Language": "ja,en;q=0.8",  # 日本站，覆盖全局的 zh-CN 优先
        },
        accept="text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    )
    if status != 200:
        raise HttpError(
            f"ascii2d 返回 HTTP {status}：{_cf_hint(raw)}"
            "（近期 Cloudflare WAF 严，需先过挑战或换日本住宅代理）"
        )
    text = raw.decode("utf-8", "replace")
    if bovw and "/color/" in final_url:
        bovw_url = final_url.replace("/color/", "/bovw/")
        status2, raw2, _f2, _h2 = http.request(bovw_url, referer=f"{base_url}/")
        if status2 == 200 and raw2.strip():
            text = raw2.decode("utf-8", "replace")
            final_url = bovw_url
    if dump_html:
        try:
            with open(dump_html, "w", encoding="utf-8") as fh:
                fh.write(text)
        except OSError:
            pass
    outcome = parse_ascii2d_html(text, base_url=base_url, top_k=top_k)
    outcome.meta["final_url"] = final_url
    outcome.meta["bovw"] = bovw
    return outcome


# ---------------------------------------------------------------------------
# Safebooru
# ---------------------------------------------------------------------------
SAFE_RATINGS = {"safe", "general", "s"}


def parse_safebooru(text: str, *, base_url: str = "https://safebooru.org", rating_filter: str = "safe", top_k: int = 5) -> Outcome:
    outcome = Outcome(provider="safebooru")
    if text is None or not str(text).strip():
        outcome.warnings.append("关键词无匹配结果（站点返回空响应）")
        return outcome
    try:
        data = json.loads(text)
    except (ValueError, TypeError):
        outcome.warnings.append("关键词无匹配结果（站点返回非 JSON，可能被限流）")
        return outcome
    if not isinstance(data, list):
        outcome.warnings.append("站点返回数据结构异常")
        return outcome
    outcome.meta["raw_count"] = len(data)
    filtered = 0
    for post in data:
        if not isinstance(post, dict):
            continue
        rating = str(post.get("rating") or "").strip().lower()
        if rating_filter != "all" and rating and rating not in SAFE_RATINGS:
            filtered += 1
            continue
        post_id = post.get("id")
        outcome.results.append(
            Result(
                title=_clean(post.get("tags"))[:120] or "(无标题)",
                source="Safebooru",
                url=f"{base_url.rstrip('/')}/index.php?page=post&s=view&id={post_id}" if post_id else base_url,
                thumbnail=post.get("preview_url") or post.get("sample_url") or post.get("file_url"),
                score=_to_float(post.get("score")),
                extra={
                    "rating": rating or None,
                    "tags": post.get("tags"),
                    "width": post.get("width"),
                    "height": post.get("height"),
                    "file_url": post.get("file_url"),
                },
            )
        )
        if len(outcome.results) >= max(1, top_k):
            break
    outcome.meta["filtered_by_rating"] = filtered
    if not outcome.results and filtered:
        outcome.warnings.append(f"{filtered} 条结果因评级过滤被隐藏（--rating all 可放开）")
    return outcome


def safebooru_search(
    http: Http, tags: str, *, base_url: str = "https://safebooru.org",
    limit: int = 5, page: int = 1, rating: str = "safe",
) -> Outcome:
    keyword = " ".join(str(tags or "").split()).strip()
    if not keyword:
        raise HttpError("Safebooru 需要 --tags（关键词）")
    query = urllib.parse.quote(keyword.replace(" ", "+"), safe="+")
    url = (
        f"{base_url}/index.php?page=dapi&s=post&q=index"
        f"&tags={query}&limit={int(limit)}&pid={max(0, int(page) - 1)}&json=1"
    )
    status, raw, _final, _hdrs = http.request(
        url, referer=f"{base_url}/", accept="application/json, text/javascript, */*;q=0.1"
    )
    if status != 200:
        raise HttpError(f"Safebooru 返回 HTTP {status}")
    return parse_safebooru(
        raw.decode("utf-8", "replace"), base_url=base_url,
        rating_filter="all" if str(rating).lower() == "all" else "safe", top_k=limit,
    )


# ---------------------------------------------------------------------------
# 输出
# ---------------------------------------------------------------------------
def render(outcome: Outcome) -> str:
    lines: list[str] = []
    head = f"【{outcome.provider}】"
    if not outcome.results:
        lines.append(f"{head}😥 无结果")
    else:
        lines.append(f"{head}命中 {len(outcome.results)} 条")
        for idx, res in enumerate(outcome.results, 1):
            line = f"{idx}. 【{res.source}】{res.title}"
            if res.score is not None:
                line += f" | 相似度 {res.score:.1f}%"
            level = res.extra.get("source_level")
            if isinstance(level, str) and level in LEVEL_LABEL:
                line += f" | {LEVEL_LABEL[level]}"
            page_no = res.extra.get("page_no")
            if page_no:
                line += f" | 第{page_no}页"
            artist = res.extra.get("artist") or res.extra.get("author")
            if artist:
                line += f" | 画师 {artist}"
            if res.extra.get("low_confidence"):
                line += " ⚠️低置信度"
            lines.append(line)
            if res.url:
                lines.append(f"   🔗 {res.url}")
    for warning in outcome.warnings:
        lines.append(f"⚠️ {warning}")
    quota = outcome.meta.get("quota")
    if isinstance(quota, dict) and quota.get("long_remaining") is not None:
        lines.append(
            f"ℹ️ 配额：短窗剩 {quota.get('short_remaining')}，今日剩 {quota.get('long_remaining')}"
        )
    return "\n".join(lines)


def build_http(args) -> Http:
    return Http(
        timeout=args.timeout,
        proxy=args.proxy,
        cookie_jar=args.cookie_jar,
        ua=args.ua,
    )


# ---------------------------------------------------------------------------
# 自检（离线）
# ---------------------------------------------------------------------------
SAMPLE_YANDEX_HTML = (
    '<html><body><div data-state="'
    # 注意：**不要**在这里 html.unescape —— data-state 的值本身必须是转义形态
    # （真实页面就是这样），解析侧负责 unescape。
    + json.dumps({
        "initialState": {
            "cbirSites": {
                "sites": [
                    {"url": "https://www.pixiv.net/artworks/1?utm_source=x", "title": "pixiv 原帖", "domain": "pixiv.net"},
                    {"url": "https://ru.pinterest.com/pin/1", "title": "pin a", "domain": "ru.pinterest.com"},
                    {"url": "https://pinterest.co.uk/pin/2", "title": "pin b", "domain": "pinterest.co.uk"},
                    {"url": "https://pinterest.ca/pin/3", "title": "pin c", "domain": "pinterest.ca"},
                    {"url": "https://danbooru.donmai.us/posts/2", "title": "booru", "domain": "danbooru.donmai.us"},
                ]
            }
        }
    }, ensure_ascii=False).replace('"', "&quot;")
    + '"></div></body></html>'
)


def self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool) -> None:
        print(("  ✅ " if ok else "  ❌ ") + name)
        if not ok:
            failures.append(name)

    print("== 1. 来源分级 ==")
    check("pixiv → high", classify("pixiv.net") == SourceLevel.HIGH)
    check("子域 danbooru.donmai.us → high", classify("danbooru.donmai.us") == SourceLevel.HIGH)
    check("x.com → high", classify("x.com") == SourceLevel.HIGH)
    check("telegra.ph → high", classify("telegra.ph") == SourceLevel.HIGH)
    check("pinterest.ru → low", classify("ru.pinterest.com") == SourceLevel.LOW)
    check("pinterest.co.uk → low", classify("pinterest.co.uk") == SourceLevel.LOW)
    check("notpinterest.com → neutral", classify("notpinterest.com") == SourceLevel.NEUTRAL)
    check("未知站 → neutral", classify("example.org") == SourceLevel.NEUTRAL)

    print("== 2. 域名去重桶 ==")
    pid_a = _dedup_key("pinterest.com")
    pid_b = _dedup_key("za.pinterest.com")
    check("pinterest 全系同桶", pid_a == pid_b == "pinterest")
    check("donmai.moe / donmai.us 不同桶", _dedup_key("donmai.moe") != _dedup_key("donmai.us"))

    print("== 3. Yandex 解析（Pinterest 刷屏 → 高价值优先） ==")
    out = parse_yandex_html(SAMPLE_YANDEX_HTML, top_k=3, max_per_domain=2)
    check("有高价值来源", any(r.extra.get("source_level") == SourceLevel.HIGH for r in out.results))
    check("首条是 pixiv 且去掉 utm_", out.results and "pixiv.net" in out.results[0].url and "utm_" not in out.results[0].url)
    check("pinterest 最多 2 条", sum(1 for r in out.results if "pinterest" in r.source) <= 2)
    empty = parse_yandex_html("<html></html>")
    check("空页面 → 有告警不抛异常", bool(empty.warnings))

    print("== 4. soutubot schema 2.2 ==")
    payload = {
        "schema_version": "2.2",
        "results": [{
            "score": 91.5,
            "path_segments": [{
                "source_key": "nhentai",
                "page_no": 31,
                "page_url": "https://nhentai.net/g/1/",
                "metadata": {"title": {"japanese_or_alias": "リオ", "primary": "Rio"}, "tags": ["a", "b"]},
            }],
        }],
    }
    so = parse_soutubot(payload, factor="1.2")
    check("命中 1 条", len(so.results) == 1)
    check("日文标题优先", so.results and so.results[0].title == "リオ")
    check("中文来源名", so.results and so.results[0].source == "NH本子")
    check("阈值 1.2 → 45", soutubot_threshold("1.2") == 45.0)
    check("阈值 1.4 → 35", soutubot_threshold("1.4") == 35.0)
    low = parse_soutubot({"results": [{"score": 30, "path_segments": [{"metadata": {}}]}]})
    check("低分标低置信度", low.results and low.results[0].extra["low_confidence"] is True)

    print("== 5. SauceNAO ==")
    sn = {
        "header": {"status": 0, "short_remaining": 3, "long_remaining": 100},
        "results": [
            {"header": {"similarity": "95.42", "index_id": 5, "index_name": "Pixiv"},
             "data": {"pixiv_id": 12345, "member": 678, "creator": "画师A", "title": "作品"}},
            {"header": {"similarity": "12.0", "index_id": 5}, "data": {"pixiv_id": 9}},
        ],
    }
    sa = parse_saucenao(sn, min_similarity=50)
    check("低于阈值被过滤", len(sa.results) == 1)
    check("ext_urls 缺失时用 pixiv_id 拼链", sa.results and sa.results[0].url.endswith("/artworks/12345"))
    check("画师取 creator", sa.results and sa.results[0].extra["artist"] == "画师A")
    check("配额解析", sa.meta["quota"]["long_remaining"] == 100)
    err = parse_saucenao({"header": {"status": -1}})
    check("status != 0 标错", err.meta.get("status_error") is True)

    print("== 6. ascii2d HTML 解析 ==")
    html = (
        '<div class="row item-box"><div class="col-xs-2"><img src="/thumb/1.jpg"></div>'
        '<div class="col-xs-10"><h6>作品名</h6><p>detail</p><small>pixiv</small>'
        '<div class="gray-link"><a href="https://www.pixiv.net/artworks/9">作品名</a>'
        '<a href="https://www.pixiv.net/users/8">作者</a></div></div></div>'
    )
    a2 = parse_ascii2d_html(html)
    check("解析 1 条", len(a2.results) == 1)
    check("来源标记 Pixiv", a2.results and a2.results[0].source == "Pixiv")
    check("链接/画师", a2.results and a2.results[0].url.endswith("/9") and a2.results[0].extra["author"] == "作者")
    check("缩略图补全为绝对地址", a2.results and str(a2.results[0].thumbnail).startswith("https://ascii2d.net/thumb/"))

    print("== 7. Safebooru ==")
    sb = parse_safebooru(json.dumps([{"id": 1, "rating": "safe", "tags": "cat_ears", "score": 5},
                                     {"id": 2, "rating": "explicit", "tags": "x"}]))
    check("safe 过滤生效", len(sb.results) == 1)
    check("空响应不抛", bool(parse_safebooru("").warnings))

    print("== 8. cookie jar（cf_clearance 复用） ==")
    import tempfile

    jar_text = (
        "# Netscape HTTP Cookie File\n"
        ".soutubot.moe\tTRUE\t/\tTRUE\t4102444800\tcf_clearance\tabc123\n"
        ".example.com\tTRUE\t/\tFALSE\t1000000000\tstale\tzzz\n"
    )
    tmp = os.path.join(tempfile.gettempdir(), "soutu_probe_jar_selftest.txt")
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(jar_text)
    try:
        jar = load_netscape_cookies(tmp)
        check("读 jar：只留未过期项", len(jar) == 1 and jar[0]["name"] == "cf_clearance")
        check("按域匹配发 Cookie", cookie_header_for(jar, "soutubot.moe") == "cf_clearance=abc123")
        check("跨域不发 Cookie", cookie_header_for(jar, "pixiv.net") == "")
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass

    print("== 9. 其它 ==")
    body, ctype = build_multipart({"a": "1"}, [("file", "q.jpg", "image/jpeg", b"IMG")])
    boundary = ctype.split("boundary=")[-1].encode()
    check("multipart 是 bytes", isinstance(body, bytes))
    check("multipart 含字段与文件字节", b'name="a"' in body and b"IMG" in body)
    check("multipart 有结束 boundary", body.endswith(b"--" + boundary + b"--\r\n"))
    check("multipart 自成完整 body（可算 Content-Length）", len(body) > len(b"IMG") + 100)
    check("魔数识别 PNG", sniff_mime(b"\x89PNG\r\n\x1a\nxxxx") == "image/png")
    check("非图片返回 None", sniff_mime(b"hello") is None)

    print()
    if failures:
        print(f"❌ 自检失败 {len(failures)} 项：" + "; ".join(failures))
        return 1
    print("✅ 自检全部通过（本自检不联网）")
    return 0


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def run_provider(args, http: Http, image_info: tuple[bytes, str, str] | None) -> Outcome:
    name = args.provider
    if name == "safebooru":
        return safebooru_search(
            http, args.tags or "", limit=args.top_k, page=args.page, rating=args.rating
        )
    if image_info is None:
        raise HttpError(f"{name} 需要 --image 或 --url")
    data, mime, filename = image_info

    if name == "yandex":
        return yandex_search(
            http, data, filename=filename, mime=mime, top_k=args.top_k,
            max_per_domain=args.max_per_domain, dump_html=args.dump_html,
        )
    if name == "soutubot":
        return soutubot_search(
            http, data, filename=filename, mime=mime, factor=args.factor,
            top_k=args.soutu_top_k, min_score=args.min_score,
        )
    if name == "saucenao":
        key = args.api_key or os.environ.get("SAUCENAO_API_KEY", "")
        return saucenao_search(
            http, data, filename=filename, mime=mime, api_key=key,
            dbmask=args.dbmask, numres=args.numres, minsim=args.minsim, hide=args.hide,
        )
    if name == "ascii2d":
        return ascii2d_search(
            http, data, filename=filename, mime=mime, bovw=args.bovw,
            top_k=max(args.top_k, 10), dump_html=args.dump_html,
        )
    raise HttpError(f"未知 provider: {name}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="免浏览器的以图搜源 HTTP 探针（yandex/soutubot/saucenao/ascii2d/safebooru）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("provider", nargs="?", default="auto",
                        choices=["auto", "yandex", "soutubot", "saucenao", "ascii2d", "safebooru"],
                        help="搜图源；auto = yandex + soutubot [+ saucenao 有 key 时]")
    parser.add_argument("--image", help="本地图片路径")
    parser.add_argument("--url", help="图片直链（http/https）")
    parser.add_argument("--tags", help="safebooru 关键词（空格分隔，多标签 AND）")
    parser.add_argument("--page", type=int, default=1, help="safebooru 页码（1 起）")
    parser.add_argument("--rating", default="safe", choices=["safe", "all"], help="safebooru 评级过滤")
    parser.add_argument("--top-k", type=int, default=5,
                        help="展示条数（yandex/safebooru 默认 5；ascii2d 无分数、内部最少取 10）")
    parser.add_argument("--max-per-domain", type=int, default=2, help="yandex 同名域最多几条（默认 2）")
    parser.add_argument("--factor", default="1.2", choices=["1.2", "1.4"], help="soutubot 模式（1.4=严格）")
    parser.add_argument("--soutu-top-k", type=int, default=25, help="soutubot 请求候选数")
    parser.add_argument("--min-score", type=float, default=28.0, help="soutubot 低于此分丢弃（默认 28）")
    parser.add_argument("--dbmask", type=int, default=0,
                        help="SauceNAO 位掩码：0=全库(省略参数) 96=Pixiv+历史 32=Pixiv 仅 4096=yande.re")
    parser.add_argument("--numres", type=int, default=15, help="SauceNAO 返回条数 1-40")
    parser.add_argument("--minsim", type=int, default=50, help="SauceNAO 最低相似度 0-100")
    parser.add_argument("--hide", type=int, default=0, choices=[0, 1, 2, 3], help="SauceNAO 内容过滤")
    parser.add_argument("--api-key", help="SauceNAO API Key（默认读 SAUCENAO_API_KEY）")
    parser.add_argument("--bovw", action="store_true", help="ascii2d 特征检索（裁剪/旋转/调色图更有效）")
    parser.add_argument("--cookie-jar", help="Netscape cookie jar（turnstile-bypass human_click.py --cookie-out）")
    parser.add_argument("--ua", help="覆盖 UA（复用 cf_clearance 时必须与解挑战时一致）")
    parser.add_argument("--proxy", help="HTTP 代理，如 http://127.0.0.1:10808")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="超时秒（默认 30）")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    parser.add_argument("--dump-html", help="把原始 HTML 落盘（排障用）")
    parser.add_argument("--self-test", action="store_true", help="离线自检，不联网")
    args = parser.parse_args(argv)

    if args.self_test:
        return self_test()

    t0 = time.perf_counter()
    http = build_http(args)
    # SauceNAO 没有 key：取图之前就退出（不下载、不读盘、不发请求）
    if args.provider == "saucenao" and not (args.api_key or os.environ.get("SAUCENAO_API_KEY")):
        print(
            "❌ 缺少 SauceNAO API Key（--api-key 或环境变量 SAUCENAO_API_KEY）；"
            "已跳过取图与请求",
            file=sys.stderr,
        )
        return 2
    try:
        image_info = None
        if args.provider != "safebooru" or args.image or args.url:
            image_info = load_image(http, image=args.image, url=args.url)
    except HttpError as exc:
        print(f"❌ {exc}", file=sys.stderr)
        return 2

    providers = ["yandex", "soutubot"] if args.provider == "auto" else [args.provider]
    if args.provider == "auto" and (args.api_key or os.environ.get("SAUCENAO_API_KEY")):
        providers.append("saucenao")

    outcomes: list[Outcome] = []
    errors: list[dict] = []
    for name in providers:
        sub = argparse.Namespace(**vars(args))
        sub.provider = name
        started = time.perf_counter()
        try:
            outcome = run_provider(sub, http, image_info)
            outcome.meta["elapsed"] = round(time.perf_counter() - started, 2)
            outcomes.append(outcome)
            if not args.json:
                print(render(outcome))
                print()
        except HttpError as exc:
            errors.append({"provider": name, "error": str(exc)})
            if not args.json:
                print(f"【{name}】❌ {exc}\n")
        except Exception as exc:  # noqa: BLE001 - 单源异常不影响其它源
            errors.append({"provider": name, "error": f"{type(exc).__name__}: {exc}"})
            if not args.json:
                print(f"【{name}】❌ 未预期错误: {type(exc).__name__}: {exc}\n")

    if args.json:
        print(json.dumps(
            {
                "ok": not errors,
                "elapsed": round(time.perf_counter() - t0, 2),
                "outcomes": [o.as_dict() for o in outcomes],
                "errors": errors,
            },
            ensure_ascii=False,
            indent=2,
        ))
    else:
        print(f"— 用时 {time.perf_counter() - t0:.3f}s —")
    return 0 if not errors or outcomes else 1


if __name__ == "__main__":
    sys.exit(main())
