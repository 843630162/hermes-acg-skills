#!/usr/bin/env python3
"""Labeled contact sheet from cover JSON (ACG release schedule delivery).
Usage:
  python scripts/contact_sheet.py items.json --title "2026年9月 里番新番" --out out.png [--cols 3]
items.json: [{"id":"...", "date":"9月4日", "title":"...", "image":"cov_xxx.jpg" | "url": "https://..."}, ...]
Requires Pillow. On this host run with <HERMES_HOME>/hermes-agent/venv/Scripts/python.exe.
"""
import argparse
import io
import json
import os
import urllib.request
from PIL import Image, ImageDraw, ImageFont

FONT_CANDIDATES = [r"C:\Windows\Fonts\msyh.ttc", r"C:/Windows/Fonts/msyh.ttc"]


def load_font(size):
    for p in FONT_CANDIDATES:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def fetch(url):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126",
                 "Referer": "https://hanime1.me/"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return Image.open(io.BytesIO(r.read())).convert("RGB")


def fit(im, w, h):
    im2 = im.copy()
    im2.thumbnail((w, h), Image.LANCZOS)
    return im2


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("items_json")
    ap.add_argument("--title", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--cols", type=int, default=3)
    a = ap.parse_args()

    items = json.load(open(a.items_json, encoding="utf-8"))
    f_head, f_date, f_small = load_font(40), load_font(26), load_font(20)
    CELL_W, IMG_H, PAD, LABEL_H = 360, 380, 16, 90
    rows = (len(items) + a.cols - 1) // a.cols
    W = PAD * (a.cols + 1) + CELL_W * a.cols
    H = PAD + 70 + rows * (IMG_H + LABEL_H + PAD)
    canvas = Image.new("RGB", (W, H), "#141414")
    d = ImageDraw.Draw(canvas)
    d.text((PAD, PAD // 2), a.title, font=f_head, fill="#ffffff")

    for i, it in enumerate(items):
        r, c = divmod(i, a.cols)
        x = PAD + c * (CELL_W + PAD)
        y = PAD + 70 + r * (IMG_H + LABEL_H + PAD)
        d.rectangle([x - 4, y - 4, x + CELL_W + 4, y + IMG_H + LABEL_H + 4], outline="#3a3a3a")
        src = it.get("image") or it.get("url", "")
        try:
            im = fit(fetch(src) if str(src).startswith(("http://", "https://")) else Image.open(src), CELL_W, IMG_H)
            canvas.paste(im, (x + (CELL_W - im.width) // 2, y + (IMG_H - im.height) // 2))
        except Exception as e:
            d.text((x + 10, y + IMG_H // 2), f"(缺图 {e})", font=f_small, fill="#888")
        ty = y + IMG_H + 14
        if it.get("date"):
            d.text((x + 6, ty), it["date"], font=f_date, fill="#ffd54f")
            ty += 38
        line = ""
        for ch in it.get("title", ""):
            if d.textlength(line + ch, font=f_small) > CELL_W - 12:
                d.text((x + 6, ty), line, font=f_small, fill="#dddddd")
                ty += 28
                line = ch
            else:
                line += ch
        if line:
            d.text((x + 6, ty), line, font=f_small, fill="#dddddd")
    canvas.save(a.out, quality=90)
    print("saved", a.out, canvas.size)


if __name__ == "__main__":
    main()
