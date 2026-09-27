---
name: image-format-conversion
description: "Convert webp/jpg/png locally; feed result to vision models."
version: 1.0.0
author: local
license: MIT
platforms: [windows]
metadata:
  hermes:
    tags: [image, webp, conversion, vision]
---

# Local image format conversion (webp/jpg/png)

## When to Use

- 用户发来 `.webp`（或 jpg/png）附件/路径，需要查看内容、描述、喂 LLM/vision 模型。
- 任务里出现 webp 而下游工具只认 jpg/png 时；或反向要把 png/jpg 压成 webp 时。

## Tools (portable, under <HERMES_HOME>/tools — never install to C: or the work dir)

- libwebp 1.6.0 Windows x64 (Google official prebuilt, BSD-3-Clause): `<HERMES_HOME>/tools/libwebp-1.6.0-windows-x64/bin/` — `dwebp.exe` decodes WebP→PNG; `cwebp.exe` encodes PNG/JPEG→WebP.
- ffmpeg (9.x): glob `<HERMES_HOME>/tools/ffmpeg-*/bin/ffmpeg` for the versioned dir — full format support, only reliable path to a real JPEG from WebP.

## Procedure

1. First try the wrapper: `bash <HERMES_HOME>/tools/webp2img.sh <in.webp> [png|jpg]`. It picks dwebp for PNG and ffmpeg for JPG, and converts git-bash paths to native form automatically. Output lands next to the source file (source webp is kept).
2. Feeding a vision/LLM model: convert first, then analyze the OUTPUT — never pass the .webp original directly. Default `jpg` (small enough for LLMs); use `png` only when lossless or alpha channel matters.
3. Manual fallback:
   - WebP → PNG: `dwebp.exe -o out.png in.webp`
   - WebP → real JPEG: `ffmpeg -y -i in.webp -q:v 2 out.jpg`
   - PNG/JPEG → WebP: `cwebp.exe -q 85 in.png -o out.webp`
4. Verify with `file <out>` — the magic bytes must say what you asked for (a .jpg that reports "PNG image data" is a dwebp artifact, not a JPEG).

## Pitfalls

- dwebp.exe always writes PNG pixel data regardless of output extension; `-o x.jpg` produces PNG-in-.jpg. Use ffmpeg when the container must actually be JPEG.
- Native Windows .exe binaries called from git-bash need native paths (`F:\...`), not MSYS paths (`/f/...`) — pass `cygpath -m "$p"`; MSYS path translation is disabled in this environment, so `/f/Hermes/...` fails with "cannot open input file".
- If a needed tool is missing from `<HERMES_HOME>/tools`, download the official prebuilt binary there (e.g. libwebp from `https://storage.googleapis.com/downloads.webmproject.org/releases/webp/`) instead of installing to C: or the session working dir.