#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""iwara_snapshot.py — Iwara 整站快照工具（纯标准库，无第三方依赖）

子命令：
  update    拉取 / 增量更新整站快照（断点续拉，默认 32 并发）
  search    在快照上做多语言文本匹配（多词 OR；标题/简介/标签/作者）
  verify    逐条核验视频 id（/video/{id} → active / 拿不到 两张清单）
  playlist  拉取 playlist 全量 → JSON（可作 search --exclude-ids 输入）
  info      查看快照状态（条数 / 日期范围 / 断点）

设计目标：给 Hermes agent（含本地小模型）直接调用——命令固定、输出简短、
出错给下一步建议、绝不静默跳数据。用法细则见 ../references/site-snapshot.md
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36")
API = "https://api.iwara.tv"
PAGE_LIMIT = 50
MAX_WORKERS = 64


def _default_dir():
    env = os.environ.get("IWARA_SNAPSHOT_DIR")
    if env:
        return env
    return str(Path.home() / "iwara-snapshot")


DEFAULT_DIR = _default_dir()

try:  # 保证 Windows 控制台/管道下 UTF-8 输出
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def log(*args):
    print(*args)
    sys.stdout.flush()


def now_iso():
    return time.strftime("%Y-%m-%d %H:%M:%S")


# ---------------------------------------------------------------- HTTP 层
class FetchError(Exception):
    def __init__(self, msg, retryable=False, cooldown=0.0):
        super().__init__(msg)
        self.retryable = retryable
        self.cooldown = cooldown


_RETRYABLE_CODES = {403, 429, 500, 502, 503, 504, 520, 521, 522, 523, 524}


def _attempt(url, timeout):
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": UA,
            "Accept": "application/json, */*",
            "Accept-Language": "en-US,en;q=0.9",
        })
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read()
    except urllib.error.HTTPError as e:
        try:
            eb = e.read()[:600].lower()
        except Exception:
            eb = b""
        cooldown = 30.0 if e.code in (403, 429) else 0.0
        if b"just a moment" in eb:
            cooldown = 60.0
        raise FetchError("HTTP %d" % e.code,
                         retryable=(e.code in _RETRYABLE_CODES),
                         cooldown=cooldown)
    except Exception as e:  # URLError / timeout / reset ...
        raise FetchError("网络错误: %s" % e, retryable=True)
    head = body[:600].lstrip().lower()
    if head.startswith(b"<") or b"just a moment" in head:
        raise FetchError("CF 挑战页", retryable=True, cooldown=45.0)
    try:
        return json.loads(body.decode("utf-8"))
    except Exception:
        raise FetchError("响应非 JSON: %r" % body[:80], retryable=True)


def fetch_json(url, retries=4, timeout=45):
    delay = 2.0
    for attempt in range(1, retries + 1):
        try:
            return _attempt(url, timeout)
        except FetchError as e:
            if not e.retryable or attempt == retries:
                raise
            time.sleep(max(delay, e.cooldown) + random.random() * 1.5)
            delay *= 1.7
    raise FetchError("重试失败")  # pragma: no cover


def fetch_video_page(page, retries=4):
    d = fetch_json("%s/videos?sort=date&rating=all&limit=%d&page=%d"
                   % (API, PAGE_LIMIT, page), retries=retries)
    if isinstance(d, dict):
        return d.get("results") or []
    return d or []


# ---------------------------------------------------------------- 数据规整 / 快照 IO
def norm_item(it):
    tags = []
    for t in (it.get("tags") or []):
        if isinstance(t, dict):
            if t.get("id"):
                tags.append(str(t["id"]))
        elif isinstance(t, str):
            tags.append(t)
    u = it.get("user") or {}
    f = it.get("file") or {}
    try:
        views = int(it.get("numViews") or 0)
    except Exception:
        views = 0
    try:
        likes = int(it.get("numLikes") or 0)
    except Exception:
        likes = 0
    try:
        dur = int(f.get("duration") or 0)
    except Exception:
        dur = 0
    return {
        "id": str(it.get("id") or ""),
        "title": str(it.get("title") or "").strip(),
        "body": str(it.get("body") or "").strip(),
        "tags": tags,
        "user": str(u.get("username") or ""),
        "views": views,
        "likes": likes,
        "created": str(it.get("createdAt") or ""),
        "rating": str(it.get("rating") or ""),
        "dur": dur,
        "file_id": str(f.get("id") or ""),
    }


def snap_paths(d):
    d = Path(d)
    return d, d / "videos.jsonl", d / "state.json"


def load_ids(d):
    _, jl, _ = snap_paths(d)
    ids = set()
    if jl.exists():
        with open(jl, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    ids.add(str(json.loads(line).get("id") or ""))
                except Exception:
                    continue
    ids.discard("")
    return ids


def append_items(d, items):
    _, jl, _ = snap_paths(d)
    with open(jl, "a", encoding="utf-8") as fh:
        for it in items:
            fh.write(json.dumps(it, ensure_ascii=False) + "\n")


def load_state(d):
    _, _, st = snap_paths(d)
    if st.exists():
        try:
            return json.loads(st.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def save_state(d, state):
    _, _, st = snap_paths(d)
    tmp = Path(str(st) + ".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(str(tmp), str(st))


# ---------------------------------------------------------------- update
def cmd_update(a):
    d, jl, _ = snap_paths(a.dir)
    d.mkdir(parents=True, exist_ok=True)
    ids = load_ids(d)
    before = len(ids)
    state = load_state(d)
    done = bool(state.get("done"))
    next_page = state.get("next_page")
    if a.reset:
        done = False
        next_page = 0
    workers = max(1, min(MAX_WORKERS, int(a.workers)))
    budget = int(a.max_pages) if a.max_pages and a.max_pages > 0 else None

    t0 = time.time()
    last_log = t0
    tried = 0
    new_cnt = 0
    failed = []
    hit_end = False
    top_last = None

    def fetch_batch(pages):
        nonlocal tried
        tried += len(pages)
        out = {}
        if not pages:
            return out
        with ThreadPoolExecutor(max_workers=min(workers, len(pages))) as ex:
            futs = {ex.submit(fetch_video_page, p): p for p in pages}
            for f in as_completed(futs):
                p = futs[f]
                try:
                    out[p] = f.result()
                except FetchError as e:
                    out[p] = None
                    failed.append((p, str(e)[:70]))
        return out

    def handle(items):
        nonlocal new_cnt
        fresh = []
        for it in items:
            n = norm_item(it)
            if n["id"] and n["id"] not in ids:
                ids.add(n["id"])
                fresh.append(n)
        if fresh:
            append_items(d, fresh)
            new_cnt += len(fresh)
        return len(fresh)

    def budget_left():
        return None if budget is None else budget - tried

    def progress(force=False):
        nonlocal last_log
        if force or (time.time() - last_log) >= 15:
            el = max(time.time() - t0, 0.001)
            log("  .. 已扫 %d 页 | 新增 %d | 快照 %d 条 | %.1f 页/秒"
                % (tried, new_cnt, len(ids), tried / el))
            last_log = time.time()

    def persist():
        dn = (done or hit_end) and not failed
        save_state(d, {
            "next_page": None if dn else next_page,
            "done": bool(dn),
            "last_run": now_iso(),
            "total": len(ids),
        })

    # ---- 阶段1：从顶部收新（连续 2 页无新即停）----
    zero_run = 0
    bsize = min(workers, 6)
    p = 0
    while True:
        left = budget_left()
        if left is not None and left <= 0:
            break
        n = bsize if left is None else min(bsize, left)
        if n <= 0:
            break
        batch = list(range(p, p + n))
        res = fetch_batch(batch)
        stop = False
        for pg in batch:
            items = res.get(pg)
            if items is None:
                zero_run = 0
                continue
            if len(items) == 0:
                hit_end = True
                stop = True
                break
            f = handle(items)
            top_last = pg
            zero_run = zero_run + 1 if f == 0 else 0
            if zero_run >= 2:
                stop = True
                break
        if top_last is not None and not done:
            cand = top_last + 1
            next_page = cand if not isinstance(next_page, int) else max(next_page, cand)
        p += n
        bsize = min(workers, max(6, bsize * 2))
        persist()
        progress()
        if stop:
            break

    # ---- 阶段2：从断点续拉到底 ----
    if not hit_end and not done:
        start = max(0, (next_page or 0) - int(a.rewind))
        p = start
        while True:
            left = budget_left()
            if left is not None and left <= 0:
                break
            n = workers if left is None else min(workers, left)
            if n <= 0:
                break
            batch = list(range(p, p + n))
            res = fetch_batch(batch)
            stop = False
            last_good = None
            for pg in batch:
                items = res.get(pg)
                if items is None:
                    continue
                if len(items) == 0:
                    hit_end = True
                    stop = True
                    break
                handle(items)
                last_good = pg
            if last_good is not None:
                cand = last_good + 1
                next_page = cand if not isinstance(next_page, int) else max(next_page, cand)
            p += n
            persist()
            progress()
            if stop:
                break

    # ---- 失败页补扫（最多 3 轮）----
    for rnd in range(3):
        if not failed:
            break
        pend = sorted({p for p, _ in failed})
        failed = []
        res = fetch_batch(pend)
        for pg in pend:
            items = res.get(pg)
            if items is None:
                continue
            if len(items) == 0:
                hit_end = True
                continue
            handle(items)
        if failed:
            time.sleep(4.0 * (rnd + 1))

    fin_done = True if hit_end else bool(done)
    if failed:
        fin_done = False
        fp = min(p for p, _ in failed)
        next_page = fp if not isinstance(next_page, int) else min(next_page, fp)
    save_state(d, {
        "next_page": None if fin_done else next_page,
        "done": fin_done,
        "last_run": now_iso(),
        "total": len(ids),
    })

    el = time.time() - t0
    log("[update] 目录: %s" % d)
    log("[update] 扫描 %d 页 | 新增 %d 条 | 快照总数 %d（此前 %d）"
        % (tried, new_cnt, len(ids), before))
    log("[update] 用时 %.1f 秒 | 全量完成=%s | next_page=%s"
        % (el, fin_done, "None" if fin_done else next_page))
    if failed:
        head = ", ".join(str(p) for p, _ in failed[:8])
        log("[update] ⚠ %d 页未取到（%s%s）；下次 update 会优先重扫，也可现在重跑一次"
            % (len(failed), head, " …" if len(failed) > 8 else ""))
        return 1
    log("[update] OK")
    return 0


# ---------------------------------------------------------------- search
_KANA_MAP = str.maketrans({chr(c): chr(c - 0x60) for c in range(0x30A1, 0x30F7)})
_ID_TOKEN_SKIP = {"https", "http", "www", "com", "video", "iwara", "tv"}


def fold(s):
    return unicodedata.normalize("NFKC", str(s)).lower().translate(_KANA_MAP)


def fmt_dur(sec):
    try:
        sec = int(sec or 0)
    except Exception:
        sec = 0
    return "%d:%02d" % (sec // 60, sec % 60)


def fmt_num(n):
    try:
        return format(int(n), ",")
    except Exception:
        return str(n)


def md_cell(s):
    return str(s).replace("|", "｜").replace("\n", " ").strip()


def video_url(vid):
    return "https://www.iwara.tv/video/%s" % vid


def _read_id_list(path):
    ids = []
    p = Path(path)
    if not p.exists():
        return ids
    txt = p.read_text(encoding="utf-8", errors="ignore")
    if p.suffix.lower() == ".json":
        try:
            data = json.loads(txt)
            items = data.get("items") if isinstance(data, dict) else data
            if isinstance(items, list):
                for it in items:
                    if isinstance(it, dict) and it.get("id"):
                        ids.append(str(it["id"]))
                    elif isinstance(it, str) and it.strip():
                        ids.append(it.strip())
                return ids
        except Exception:
            pass
    for line in txt.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("{"):
            try:
                j = json.loads(line)
                if j.get("id"):
                    ids.append(str(j["id"]))
                continue
            except Exception:
                pass
        for lk in re.findall(r"/video/([A-Za-z0-9_\-]+)", line):
            ids.append(lk)
        if re.fullmatch(r"[A-Za-z0-9_\-]{6,40}", line) and not line.isdigit():
            ids.append(line)  # 整行即一个 id（txt 列表；全大写 id 也照收）
            continue
        toks = [t for t in re.findall(r"[A-Za-z0-9_\-]{6,40}", line)
                if re.search(r"\d", t) and re.search(r"[A-Za-z]", t)
                and t.lower() not in _ID_TOKEN_SKIP]
        ids.extend(toks)
    seen = set()
    out = []
    for i in ids:
        if i not in seen:
            seen.add(i)
            out.append(i)
    return out


def load_exclude_ids(files):
    s = set()
    for fp in files:
        if not Path(fp).exists():
            log("[search] ⚠ --exclude-ids 文件不存在: %s" % fp)
            continue
        s.update(_read_id_list(fp))
    return s


def cmd_search(a):
    d, jl, _ = snap_paths(a.dir)
    if not jl.exists():
        log("[search] 快照不存在: %s" % jl)
        log("[search] 先跑 update（或指定 --dir）；详见 references/site-snapshot.md")
        return 2
    terms = [t.strip() for t in (a.terms or []) if t.strip()]
    if a.terms_file:
        try:
            for line in Path(a.terms_file).read_text(encoding="utf-8").splitlines():
                t = line.strip()
                if t and not t.startswith("#"):
                    terms.append(t)
        except Exception as e:
            log("[search] 读词表失败: %s" % e)
            return 1
    if not terms:
        log("[search] 至少给一个词（或 --terms-file）")
        return 2
    ft = [(t, fold(t)) for t in terms]
    ft = [(t, f) for t, f in ft if f]
    nots = [fold(x) for x in (a.not_ or []) if fold(x)]
    excl = load_exclude_ids(a.exclude_ids or [])

    t0 = time.time()
    hits = []
    n_total = 0
    n_excl = 0
    with open(jl, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except Exception:
                continue
            n_total += 1
            rid = str(rec.get("id") or "")
            if rid in excl:
                n_excl += 1
                continue
            hay = {
                "title": fold(rec.get("title") or ""),
                "body": fold(rec.get("body") or ""),
                "tags": fold(" ".join(rec.get("tags") or [])),
                "user": fold(rec.get("user") or ""),
            }
            if nots:
                blob = " ".join(hay.values())
                if any(nm in blob for nm in nots):
                    continue
            matched = []
            fields = set()
            for t, f in ft:
                flds = [k for k, v in hay.items() if f in v]
                if flds:
                    matched.append(t)
                    fields.update(flds)
            if not matched:
                continue
            rec["_match"] = matched
            rec["_fields"] = sorted(fields)
            hits.append(rec)

    if a.sort == "date":
        hits.sort(key=lambda r: str(r.get("created") or ""), reverse=True)
    else:
        hits.sort(key=lambda r: int(r.get("views") or 0), reverse=True)

    el = time.time() - t0
    md_path = jl_path = None
    if a.out:
        outp = Path(a.out)
        stem = outp.with_suffix("") if outp.suffix.lower() in (".md", ".jsonl", ".txt") else outp
        md_path = Path(str(stem) + ".md")
        jl_path = Path(str(stem) + ".jsonl")
        lines = [
            "# Iwara 快照匹配结果",
            "",
            "- 生成: %s | 快照: %s（%d 条）" % (now_iso(), jl, n_total),
            "- 词(%d): %s" % (len(ft), "、".join(t for t, _ in ft)),
            "- 命中: %d 条（--exclude-ids 排除 %d 条）" % (len(hits), n_excl),
            "",
            "| 标题 | 作者 | 时长 | views | 匹配词 | 链接 |",
            "|---|---|---|---|---|---|",
        ]
        for r in hits:
            lines.append("| %s | %s | %s | %s | %s | %s |" % (
                md_cell(r.get("title")), md_cell(r.get("user")),
                fmt_dur(r.get("dur")), fmt_num(r.get("views")),
                md_cell("、".join(r.get("_match") or [])), video_url(r.get("id"))))
        md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        with open(jl_path, "w", encoding="utf-8") as fh:
            for r in hits:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    log("[search] 快照 %d 条 | 词 %d 个 | 命中 %d（排除 %d）| 用时 %.1f 秒"
        % (n_total, len(ft), len(hits), n_excl, el))
    show = min(int(a.limit), len(hits))
    for i, r in enumerate(hits[:show], 1):
        log("  %d. [%s] %s | @%s | %s | %s"
            % (i, fmt_num(r.get("views")), str(r.get("title"))[:70], r.get("user"),
               fmt_dur(r.get("dur")), "、".join(r.get("_match") or [])))
    if a.out:
        log("[search] 写出: %s + %s（%d 条）" % (md_path, jl_path, len(hits)))
    else:
        log("[search] （加 --out 文件名 可落盘 md+jsonl）")
    log("[search] OK")
    return 0


# ---------------------------------------------------------------- verify
def cmd_verify(a):
    ids = _read_id_list(a.in_)
    if not ids:
        log("[verify] 没有读到 id: %s" % a.in_)
        return 2
    workers = max(1, min(16, int(a.workers or 8)))
    t0 = time.time()
    live = []
    dead = []

    def check(vid):
        try:
            d = fetch_json("%s/video/%s" % (API, vid), retries=3, timeout=30)
        except FetchError as e:
            return vid, None, str(e)[:60]
        if isinstance(d, dict) and str(d.get("status") or "") == "active":
            f = d.get("file") or {}
            u = d.get("user") or {}
            try:
                dur = int(f.get("duration") or 0)
            except Exception:
                dur = 0
            return vid, {
                "title": str(d.get("title") or ""),
                "user": str(u.get("username") or ""),
                "views": int(d.get("numViews") or 0),
                "dur": dur,
                "unlisted": bool(d.get("unlisted")),
            }, None
        return vid, None, "非 active"

    with ThreadPoolExecutor(max_workers=min(workers, len(ids))) as ex:
        for vid, info, err in ex.map(check, ids):
            if info:
                live.append((vid, info))
            else:
                dead.append((vid, err))

    out = a.out
    if not out:
        pth = Path(a.in_)
        out = str(pth.with_suffix("")) + "-verified.md"
    el = time.time() - t0
    lines = [
        "# 候选核验（verify）",
        "",
        "- 输入: %s | 核验时间: %s" % (a.in_, now_iso()),
        "- active: %d | 拿不到: %d" % (len(live), len(dead)),
        "",
        "## 有效（status=active）",
        "",
        "| 标题 | 作者 | 时长 | views | 链接 | 备注 |",
        "|---|---|---|---|---|---|",
    ]
    for vid, info in live:
        lines.append("| %s | %s | %s | %s | %s | %s |" % (
            md_cell(info["title"]), md_cell(info["user"]), fmt_dur(info["dur"]),
            fmt_num(info["views"]), video_url(vid),
            "unlisted（仅持链接可见）" if info["unlisted"] else ""))
    lines += ["", "## 拿不到（404/403/非 active）", ""]
    for vid, err in dead:
        lines.append("- %s — %s" % (vid, err))
    Path(out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    log("[verify] 核验 %d 条：active %d | 拿不到 %d | 用时 %.1f 秒"
        % (len(ids), len(live), len(dead), el))
    if dead:
        log("[verify] 拿不到: %s%s"
            % (", ".join(v for v, _ in dead[:8]), " …" if len(dead) > 8 else ""))
    log("[verify] 写出: %s" % out)
    log("[verify] OK")
    return 0


# ---------------------------------------------------------------- playlist
def cmd_playlist(a):
    m = re.search(r"/playlist/([0-9a-fA-F\-]{16,40})", a.id_or_url or "")
    uuid = m.group(1) if m else (a.id_or_url or "").strip()
    if not re.fullmatch(r"[0-9a-fA-F\-]{16,40}", uuid or ""):
        log("[playlist] 看着不像 playlist id / URL: %r" % a.id_or_url)
        return 2
    items = []
    page = 0
    while True:
        d = fetch_json("%s/playlist/%s?page=%d&limit=32" % (API, uuid, page),
                       retries=4, timeout=45)
        results = d.get("results") if isinstance(d, dict) else d
        results = results or []
        if not results:
            break
        for it in results:
            items.append(norm_item(it))
        page += 1
        if page > 500:
            break
        time.sleep(0.3)
    seen = set()
    uniq = []
    for it in items:
        if it["id"] in seen:
            continue
        seen.add(it["id"])
        uniq.append(it)
    out = a.out
    if not out:
        d0, _, _ = snap_paths(a.dir)
        out = str(d0 / ("playlist-%s.json" % uuid))
    outp = Path(out)
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(json.dumps(
        {"playlist": uuid, "count": len(uniq), "fetched": now_iso(), "items": uniq},
        ensure_ascii=False, indent=1), encoding="utf-8")
    log("[playlist] %s | 拉取 %d 页 | %d 条（去重后）" % (uuid, page, len(uniq)))
    log("[playlist] 写出: %s" % outp)
    log("[playlist] OK（可作 search --exclude-ids 输入）")
    return 0


# ---------------------------------------------------------------- info
def cmd_info(a):
    d, jl, _ = snap_paths(a.dir)
    if not jl.exists():
        log("[info] 快照不存在: %s" % jl)
        log("[info] 先跑: python <skill>/scripts/iwara_snapshot.py update")
        return 0
    count = 0
    mn = ""
    mx = ""
    with open(jl, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            count += 1
            c = str(r.get("created") or "")
            if c:
                if not mn or c < mn:
                    mn = c
                if not mx or c > mx:
                    mx = c
    mb = jl.stat().st_size / 1048576.0
    state = load_state(d)
    log("[info] 目录: %s" % d)
    log("[info] 条数: %d | 日期范围: %s ~ %s | 大小: %.1f MB"
        % (count, (mn[:10] or "?"), (mx[:10] or "?"), mb))
    log("[info] 状态: done=%s next_page=%s last_run=%s"
        % (state.get("done"), state.get("next_page"), state.get("last_run") or "-"))
    log("[info] OK")
    return 0


# ---------------------------------------------------------------- CLI
def build_parser():
    ap = argparse.ArgumentParser(
        prog="iwara_snapshot.py",
        description="Iwara 整站快照：拉取/增量更新 + 本地匹配 + 核验（纯标准库）")
    sub = ap.add_subparsers(dest="cmd")

    up = sub.add_parser("update", help="拉取/增量更新整站快照（断点续拉，默认32并发）")
    up.add_argument("--dir", default=DEFAULT_DIR)
    up.add_argument("--workers", type=int, default=32)
    up.add_argument("--rewind", type=int, default=20)
    up.add_argument("--max-pages", type=int, default=0, help="调试：本次最多取 N 页（0=不限）")
    up.add_argument("--reset", action="store_true", help="忽略断点从头重扫（去重仍然生效）")

    se = sub.add_parser("search", help="在快照上做本地文本匹配（多词 OR）")
    se.add_argument("terms", nargs="*", help="搜索词（中文/日文/英文均可，多词 OR）")
    se.add_argument("--terms-file", default=None, help="从文件读词（一行一词，# 注释）")
    se.add_argument("--dir", default=DEFAULT_DIR)
    se.add_argument("--out", default=None, help="输出文件名（会生成 .md + .jsonl）")
    se.add_argument("--exclude-ids", nargs="*", default=None,
                    help="排除 id 列表（playlist.json / ids.txt / 含链接的 md 均可）")
    se.add_argument("--not", dest="not_", action="append", default=None,
                    help="误命中排除词（可多次）")
    se.add_argument("--limit", type=int, default=30, help="终端预览条数（默认30）")
    se.add_argument("--sort", choices=["views", "date"], default="views")

    ve = sub.add_parser("verify", help="逐条核验视频 id（/video/{id}）")
    ve.add_argument("--in", dest="in_", required=True, help="输入 id 列表（jsonl/txt/md）")
    ve.add_argument("--out", default=None, help="输出 md（默认 <输入>-verified.md）")
    ve.add_argument("--dir", default=DEFAULT_DIR)
    ve.add_argument("--workers", type=int, default=8)

    pl = sub.add_parser("playlist", help="拉取 playlist 全量 → JSON")
    pl.add_argument("id_or_url", help="playlist id 或完整 URL")
    pl.add_argument("--out", default=None)
    pl.add_argument("--dir", default=DEFAULT_DIR)

    inf = sub.add_parser("info", help="查看快照状态")
    inf.add_argument("--dir", default=DEFAULT_DIR)
    return ap


def main(argv=None):
    ap = build_parser()
    a = ap.parse_args(argv)
    if not a.cmd:
        ap.print_help()
        return 0
    try:
        return {
            "update": cmd_update,
            "search": cmd_search,
            "verify": cmd_verify,
            "playlist": cmd_playlist,
            "info": cmd_info,
        }[a.cmd](a)
    except KeyboardInterrupt:
        log("[!] 手动中断；进度已保存，重跑同样的命令会继续。")
        return 130
    except FetchError as e:
        log("[ERR] 网络/接口失败: %s（稍后重跑即可；update 支持断点续拉）" % e)
        return 1
    except Exception as e:
        log("[ERR] %s: %s" % (type(e).__name__, e))
        return 1


if __name__ == "__main__":
    sys.exit(main())
