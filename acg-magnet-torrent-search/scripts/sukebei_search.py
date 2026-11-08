#!/usr/bin/env python3
"""sukebei_search.py — 带「对照词自检」的 sukebei 检索，避免把坏管道当成「零命中」。

为什么要有这个脚本：
  2026-11-06 本机模型用 `?query=` 查 sukebei（sukebei 只认 `?q=`），页面回的是首页最新列表，
  再用一个不存在的正则 `/f/<id>/` 解析 → 0 条 → 输出「没有磁力」。实际同关键词有 75 条、5 条可用磁力。
  这个脚本把三件事固化成硬门槛：
    1) 参数只用 `?q=<kw>&f=0&c=0_0`；
    2) 解析后回读搜索框 `name="q" value=...`，值不等于关键词就说明参数被忽略 → 直接报管道故障；
    3) 每次检索前先跑对照词（默认 MIDE-599），对照 0 条就拒绝给「无资源」结论。

用法：
  python sukebei_search.py 藤木紗英 サンダーロード --proxy http://127.0.0.1:10808
  python sukebei_search.py TSAK --json out.json --limit 30
  python sukebei_search.py 关键词 --no-control      # 只在明确知道管道没坏时用

退出码：0 = 对照通过（结果可能为 0 条，那是可信的零命中）；2 = 管道故障，禁止据此下「没有」结论。
"""
import argparse
import gzip
import html
import json
import re
import ssl
import sys
import urllib.parse
import urllib.request
import zlib

BASE = "https://sukebei.nyaa.si/"
CONTROL_KEYWORD = "MIDE-599"          # 长期存在的真资源，用来验证检索管道
UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept-Language": "ja,en;q=0.8,zh-CN;q=0.6",
    "Accept-Encoding": "gzip",
}

ROW_RE = re.compile(r'<tr class="(?:default|success|danger)">(.*?)</tr>', re.S)
VIEW_RE = re.compile(r'<a href="(/view/\d+)"[^>]*title="([^"]*)"')
MAG_RE = re.compile(r'href="(magnet:\?[^"]+)"')
BTIH_RE = re.compile(r'btih:([0-9a-fA-F]{40})')
TD_RE = re.compile(r'<td[^>]*>(.*?)</td>', re.S)
SIZE_RE = re.compile(r'^\s*[\d.]+\s*[KMG]iB\s*$')
DATE_RE = re.compile(r'^\s*\d{4}-\d{2}-\d{2}')
SEARCHBOX_RE = re.compile(r'name="q"[^>]*value="([^"]*)"')


def opener(proxy):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    handlers = [urllib.request.HTTPSHandler(context=ctx)]
    if proxy:
        handlers.append(urllib.request.ProxyHandler({"http": proxy, "https": proxy}))
    return urllib.request.build_opener(*handlers)


def fetch(url, proxy):
    with opener(proxy).open(urllib.request.Request(url, headers=UA), timeout=35) as r:
        raw = r.read()
        enc = (r.headers.get("Content-Encoding") or "").lower()
        # 代理/服务器会无视 Accept-Encoding 直接回 gzip，不解压就会把二进制当 HTML 解析出 0 行
        if raw[:2] == b"\x1f\x8b" or "gzip" in enc:
            raw = gzip.decompress(raw)
        elif "deflate" in enc:
            raw = zlib.decompress(raw, -zlib.MAX_WBITS)
        return r.status, raw


def parse_page(text):
    """返回 [(标题, 体积, 日期, 做种, 下载完成数, hash, view_url)]"""
    out = []
    for row in ROW_RE.findall(text):
        v = VIEW_RE.search(row)
        if not v:
            continue
        cells = [html.unescape(re.sub("<[^>]+>", "", c)).strip() for c in TD_RE.findall(row)]
        size = next((c for c in cells if SIZE_RE.match(c)), "")
        date = next((c for c in cells if DATE_RE.match(c)), "")
        idx = cells.index(date) if date in cells else -1
        nums = cells[idx + 1: idx + 4] if idx >= 0 else []
        mag = MAG_RE.search(row)
        h = BTIH_RE.search(mag.group(1)) if mag else None
        out.append({
            "title": html.unescape(v.group(2)),
            "size": size,
            "date": date,
            "seeders": nums[0] if len(nums) > 0 else "",
            "completed": nums[2] if len(nums) > 2 else "",
            "hash": h.group(1).lower() if h else "",
            "view": BASE.rstrip("/") + v.group(1),
        })
    return out


def search(keyword, proxy):
    url = f"{BASE}?q={urllib.parse.quote(keyword)}&f=0&c=0_0"
    status, body = fetch(url, proxy)
    text = body.decode("utf-8", "ignore")
    rows = parse_page(text)
    box = SEARCHBOX_RE.findall(text)
    echoed = html.unescape(box[0]) if box else None
    # 只看「参数是否被接受」：搜索框回显等于关键词即说明 q= 生效；真·零命中是合法结果。
    # 参数被忽略时回显为空（首页），这时才判管道/参数故障。
    ok = echoed == keyword
    nores = bool(re.search(r"No results found|没有找到|0 results", text, re.I))
    return {"url": url, "status": status, "bytes": len(body), "rows": rows,
            "echoed": echoed, "ok": ok, "nores": nores, "error": None}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("keywords", nargs="+")
    ap.add_argument("--proxy", default=None, help="如 http://127.0.0.1:10808；失败时自动再试直连")
    ap.add_argument("--control", default=CONTROL_KEYWORD, help="对照词，默认 MIDE-599")
    ap.add_argument("--no-control", action="store_true")
    ap.add_argument("--limit", type=int, default=15)
    ap.add_argument("--json", dest="json_path", default=None)
    args = ap.parse_args()

    # 1) 对照词自检
    if not args.no_control:
        c = None
        for px in [args.proxy, None] if args.proxy else [None]:
            try:
                c = search(args.control, px)
                break
            except Exception as e:  # noqa: BLE001
                c = {"error": f"{type(e).__name__}: {e}", "ok": False, "rows": [], "bytes": 0}
        if not c.get("ok") or len(c["rows"]) < 3:
            print(f"[PIPELINE FAIL] 对照词 {args.control} 没跑通："
                  f"error={c.get('error')} bytes={c.get('bytes')} rows={len(c.get('rows') or [])} "
                  f"echoed={c.get('echoed')!r}")
            print("[PIPELINE FAIL] 管道坏了 → 本次任何「零命中」都不成立，禁止据此说没有资源。")
            return 2
        print(f"[control ok] {args.control}: {len(c['rows'])} 行, {c['bytes']} bytes")

    # 2) 正式检索
    results = {}
    for kw in args.keywords:
        try:
            r = search(kw, args.proxy)
        except Exception as e:  # noqa: BLE001
            r = {"error": f"{type(e).__name__}: {e}", "rows": [], "bytes": 0, "echoed": None, "ok": False}
        results[kw] = r
        if r.get("error"):
            print(f"\n=== {kw} ===\n  [ERROR] {r['error']}")
            continue
        if not r["ok"]:
            hint = "参数被忽略（搜索框回显不符）" if r["echoed"] != kw else "解析到 0 行"
            print(f"\n=== {kw} ===\n  [FAIL] {hint}: bytes={r['bytes']} echoed={r['echoed']!r}")
            continue
        print(f"\n=== {kw} === {len(r['rows'])} 条" + ("  [零命中，管道已验证]" if not r["rows"] else ""))
        for i, d in enumerate(r["rows"][: args.limit], 1):
            print(f"  {i:>2}. {d['title'][:96]}")
            print(f"      {d['size']} {d['date']} seeds={d['seeders']} done={d['completed']} "
                  f"{d['hash']} {d['view']}")

    if args.json_path:
        with open(args.json_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=1)
        print(f"\n[json] {args.json_path}")

    failed = [k for k, v in results.items() if v.get("error") or not v.get("ok")]
    if failed:
        print(f"\n[WARN] 这些词管道没验证通过，不能算「搜过且没有」：{failed}")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
