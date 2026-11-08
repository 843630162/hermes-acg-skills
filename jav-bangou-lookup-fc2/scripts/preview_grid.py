#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build an official preview contact sheet for a JAV bangou.

Usage:
    python preview_grid.py SNOS-424 --out ./out
    python preview_grid.py SNOS-424 --out /tmp/x --cols 4 --max 14
    python preview_grid.py SNOS-424 --out /tmp/x --code snos00424   # override DMM code

Why this exists:
  * tp.spfcas.com (JavDB CDN) ships images with a 1-byte XOR key prepended.
    Naive Image.open() raises UnidentifiedImageError even though the HTTP
    fetch returned 200 and a normal-sized JPEG. decode_spfcas() fixes it.
  * pics.dmm.co.jp serves the same artwork unencrypted and at higher res.
    Its code is prefix + zero-padded 5 digits: SNOS-424 -> snos00424.
    Non-padded forms (snos424, 1snos00424) answer 405, which is NOT
    evidence that the title has no images.
  * DMM's sample gallery can be shorter than JavDB's preview_images list and
    its tail entry may be a grey "NOW PRINTING" placeholder returned with
    HTTP 200. looks_like_placeholder() drops those.

Outputs:
    <out>/<NUMBER>_cover.jpg      official cover (DVD jacket, front+back)
    <out>/<NUMBER>_previews.jpg   contact sheet, cover first

After running, ALWAYS vision_analyze the contact sheet before sending it:
check for placeholders/blank cells and confirm cell order matches the film.
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 " \
     "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
DMM = "https://pics.dmm.co.jp/digital/video/{code}/{name}"


def eprint(*a):
    print(*a, file=sys.stderr)


def fetch(url, dest, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r, open(dest, "wb") as f:
        f.write(r.read())
    return dest


def decode_spfcas(path):
    """Undo tp.spfcas.com's single-byte XOR obfuscation, in place."""
    with open(path, "rb") as f:
        data = f.read()
    if data[:2] == b"\xff\xd8":          # already a JPEG
        return False
    if not data:
        raise ValueError("empty image response: %s" % path)
    key = data[0]
    with open(path, "wb") as f:
        f.write(bytes(b ^ key for b in data[1:]))
    return True


def looks_like_placeholder(im):
    """Grey near-uniform tile such as DMM's 'NOW PRINTING' sample."""
    g = im.convert("L")
    px = list(g.getdata())
    n = len(px)
    mean = sum(px) / n
    var = sum((v - mean) ** 2 for v in px[::7]) / max(1, len(px[::7]))
    return mean > 200 and var ** 0.5 < 25


def dmm_code(number, override=None):
    if override:
        return override.lower()
    core = number.replace("-", "")
    i = 0
    while i < len(core) and not core[i].isdigit():
        i += 1
    prefix, digits = core[:i].lower(), core[i:]
    return f"{prefix}{digits.zfill(5)}"


def javdb_images(number):
    """Fallback: pull cover + samples from javdb-cli JSON."""
    out = subprocess.run(["javdb", "detail", number, "--json"],
                         capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError("javdb detail failed: %s" % out.stderr.strip()[:300])
    d = json.loads(out.stdout)
    urls = [d["cover_url"]] if d.get("cover_url") else []
    urls += [p["large_url"] for p in d.get("preview_images") or []]
    return urls


def build(paths, out_path, cols=4, cell_w=480, pad=12, bg=(22, 22, 26)):
    from PIL import Image

    imgs = [Image.open(p).convert("RGB") for p in paths]
    resized = []
    for im in imgs:
        w, h = im.size
        resized.append(im.resize((cell_w, max(1, int(h * cell_w / w))), Image.LANCZOS))

    rows = (len(resized) + cols - 1) // cols
    row_h = []
    for r in range(rows):
        chunk = resized[r * cols:(r + 1) * cols]
        row_h.append(max(i.size[1] for i in chunk))

    total_w = cols * cell_w + (cols + 1) * pad
    total_h = sum(row_h) + (rows + 1) * pad
    canvas = Image.new("RGB", (total_w, total_h), bg)

    y = pad
    for r in range(rows):
        x = pad
        for c in range(cols):
            idx = r * cols + c
            if idx >= len(resized):
                break
            im = resized[idx]
            # centre vertically: mixed 16:9 and 9:16 crops otherwise sit skewed
            canvas.paste(im, (x, y + (row_h[r] - im.size[1]) // 2))
            x += cell_w + pad
        y += row_h[r] + pad

    canvas.save(out_path, quality=92)
    return canvas.size, len(resized)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("number", help="bangou, e.g. SNOS-424 (not for FC2-PPV)")
    ap.add_argument("--out", default=os.environ.get("WORK_DIR", "."))
    ap.add_argument("--cols", type=int, default=4)
    ap.add_argument("--max", type=int, default=16, help="max samples to probe")
    ap.add_argument("--code", default=None, help="override DMM code, e.g. snos00424")
    ap.add_argument("--keep-samples", action="store_true")
    a = ap.parse_args()

    number = a.number.upper().strip()
    os.makedirs(a.out, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="preview_grid_")

    cover = os.path.join(a.out, f"{number}_cover.jpg")
    samples, source = [], None

    code = dmm_code(number, a.code)
    try:
        fetch(DMM.format(code=code, name=f"{code}pl.jpg"), cover)
        n = 1
        while n <= a.max:
            p = os.path.join(tmp, f"s{n}.jpg")
            try:
                fetch(DMM.format(code=code, name=f"{code}jp-{n}.jpg"), p)
            except urllib.error.HTTPError:
                break                      # 404 = gallery ended
            samples.append(p)
            n += 1
        source = f"dmm ({code})"
    except Exception as e:                  # noqa: BLE001 - fall through to JavDB
        eprint(f"[dmm] {type(e).__name__}: {e}; falling back to JavDB CDN")
        urls = javdb_images(number)
        if not urls:
            sys.exit("no images from DMM or JavDB")
        fetch(urls[0], cover)
        decode_spfcas(cover)
        for i, u in enumerate(urls[1:], 1):
            p = os.path.join(tmp, f"s{i}.jpg")
            fetch(u, p)
            decode_spfcas(p)
            samples.append(p)
        source = "javdb/spfcas (xor-decoded)"

    from PIL import Image
    kept = []
    for p in samples:
        try:
            im = Image.open(p)
        except Exception:                   # noqa: BLE001
            eprint(f"[skip] undecodable {os.path.basename(p)}")
            continue
        if looks_like_placeholder(im):
            eprint(f"[skip] placeholder tile {os.path.basename(p)}")
            continue
        kept.append(p)

    grid = os.path.join(a.out, f"{number}_previews.jpg")
    size, n = build([cover] + kept, grid, cols=a.cols)

    if not a.keep_samples:
        for p in samples:
            try:
                os.remove(p)
            except OSError:
                pass
        try:
            os.rmdir(tmp)
        except OSError:
            pass

    print(f"source      : {source}")
    print(f"samples kept: {len(kept)} (probed {len(samples)})")
    print(f"cover       : {cover}")
    print(f"grid        : {grid}  {size[0]}x{size[1]}  {n} cells")
    print("next        : vision_analyze the grid for placeholder/blank cells "
          "and cell order before sending")


if __name__ == "__main__":
    main()
