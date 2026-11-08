# Coser identity attribution for reposted X/Twitter cosplay clips

Use when a viral X clip is a repost of a CN paid/fuwajiki coser set and there is no usable CN (cosplayer name) from captions.

## Pipeline that worked (2026-11 case, Aglaea selfie clip)
1. fxtwitter API (`api.fxtwitter.com/i/status/<id>`) → video `youtube_id`/media id + duration. Compare media ids across repost-chain tweets: identical id = same repost, different id = re-upload; earliest date wins the chain (promo accounts only).
2. Download mp4, extract frames (`ffmpeg select`), build comparison sheets with PIL/ffmpeg hstack.
3. Reverse search full frame + cropped FACE (crop head block ~ x 0.28-0.72, y 0.03-0.45) with `scripts/soutu_http_probe.py yandex`. Full-frame hits give leak-site albums; face-crop hits give pirate video-site pages (tvnews.tw/ik8tv/lioncp — SEO junk, thumbnails may be unrelated cosplays, do not trust titles).
4. Google Lens uploadbyurl works via browser; Google Images **AI mode** (tab span 'AI 模式', click its A ancestor, wait ~15s, read body) gives character guesses + cited links; treat citations as leads only (aggregator shorts/SEO spam).
5. Leak-site album enumeration is the decisive step: `cosplayboobs.com/pl/search/<Character>` lists ALL cosplayer albums of that character. Album previews: extract internal id from album page HTML (`images/a/\d+/[^/]+/(\d+)/`), then fetch `https://cosplayboobs.com/images/a/604/-10000001/<internalId>/<N>.webp` for N=1..count (604px wide, fast). Download full preview sets (90-140 imgs) per suspect album.
6. Batch compare: dHash(16) distance vs reference frame + pixel heuristics (warm top band = beige wall/curtain, dark bottom = black gauze) to rank candidates; then vision grid sheets with filename labels; final identity = face-crop montage vs frame face, ask per-cell 同人 judgment on 脸型/眼形/卧蚕/泪妆/唇形 (costume alone is unreliable — same character sets reuse outfits across cosplayers).
7. CN aliases: one fuwajiki has many names (咬一口兔娘ovo = 黏黏团子兔 = 咬人小小兔 = 兔叽桃奈奈; leak sites label them inconsistently, e.g. cosplayboobs 'Urumibunny Yaokoututu / Niantutu'). Before concluding two candidates are different people, web_search '别名/alias' aggregation sites (e.g. 584520.xyz posts list 名/别名/微博 URL).

## Pitfalls
- 简书/SEO 网盘引流文: AI-generated text + random cover images; article title naming the coser is weak evidence, cover is usually unrelated.
- Vision grid cell-indexing drifts when labels are tiny: draw labels with PIL ImageDraw at cell top-left, and prefer pixel/dHash ranking over vision picking cells.
- vision_analyze times out on wide multi-cell sheets; shrink to <= ~1680x640 or analyze cells individually.
- Hotel-room / plain-wall selfie videos are often the paid set's video previews (albums list 'N photos and M videos'); scene mismatch with studio previews does not disprove identity — face match does.
