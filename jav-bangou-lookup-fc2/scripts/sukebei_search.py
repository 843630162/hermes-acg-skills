#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sukebei.nyaa.si 直查（FC2/JAV 番号兜底磁源）。用法:
  python sukebei_search.py 4825364 4121738 ...        # bare numbers or full IDs
  python sukebei_search.py --json out.json 4825364

Why this exists (2026-11, verified):
- urllib must NOT send `Accept-Encoding: gzip`: it never auto-decompresses, so the
  body stays gzip bytes and every regex finds nothing -> a fake "site has no hits".
- Current row markup is `<tr class="default">`; the old `<tr class='torrentrow'>`
  gives zero rows.
- `<td class="text-center">` columns are [empty Link cell, Size, Date, Seeders,
  Leechers, Downloads], but some rows carry an extra marker cell, so index by
  CONTENT (date regex / size regex / remaining ints), never by position.
Rank magnets by seeds*5 + downloads; deliver both the original rip and the
smallest [H265 1080p] encode when both exist.
"""
import html
import json
import re
import sys
import time
import urllib.parse
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$")
SIZE_RE = re.compile(r"^[\d.]+ (?:B|KiB|MiB|GiB|TiB)$")
SLEEP = 5  # keep ~1 req/5s; faster gets the IP blocked


def fetch(query):
    url = "https://sukebei.nyaa.si/?q=" + urllib.parse.quote(query)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def rows_of(page):
    out = []
    for tr in re.findall(r'<tr class="default">(.*?)</tr>', page, re.S):
        m = re.search(r'<a href="/view/(\d+)" title="([^"]+)"', tr)
        if not m:
            continue
        mag = re.search(r'href="(magnet:[^"]+)"', tr)
        size = date = None
        ints = []
        for c in re.findall(r'<td class="text-center"[^>]*>(.*?)</td>', tr, re.S):
            t = html.unescape(re.sub(r"<[^>]+>", "", c)).strip()
            if not t:
                continue
            if DATE_RE.match(t):
                date = t
            elif SIZE_RE.match(t):
                size = t
            elif re.fullmatch(r"\d+", t):
                ints.append(int(t))
        seeds, leech, down = (ints + [None, None, None])[:3]
        out.append({
            "name": html.unescape(m.group(2)),
            "magnet": html.unescape(mag.group(1)) if mag else None,
            "size": size, "date": date, "seeds": seeds, "leechers": leech,
            "downloads": down,
            "page": "https://sukebei.nyaa.si/view/" + m.group(1),
        })
    return out


def main():
    args = sys.argv[1:]
    out_path = None
    if args and args[0] == "--json":
        out_path, args = args[1], args[2:]
    if not args:
        print(__doc__)
        return 1
    result = {}
    for raw in args:
        num = re.sub(r"[^0-9]", "", raw)[-7:]
        query = raw if "-" in raw else "FC2-PPV-" + num
        try:
            rows = rows_of(fetch(query))
        except Exception as exc:
            print(f"{query}: ERROR {type(exc).__name__}: {exc}")
            result[query] = {"error": str(exc)}
            time.sleep(SLEEP)
            continue
        hits = [r for r in rows if num in r["name"].replace("-", "")]
        hits.sort(key=lambda r: (r["seeds"] or 0) * 5 + (r["downloads"] or 0),
                  reverse=True)
        result[query] = {"rows": len(rows), "hits": hits}
        print(f"=== {query}: rows={len(rows)} hits={len(hits)}")
        for r in hits:
            print(f"  {r['size'] or '?':>10}  seeds={r['seeds']} dl={r['downloads']} "
                  f"{r['date']}  {r['name'][:70]}")
            print(f"    {r['magnet']}")
        time.sleep(SLEEP)
    if out_path:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=1)
        print("saved", out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
