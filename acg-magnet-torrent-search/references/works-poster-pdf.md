# 作品片目 + 磁力 + 海报 PDF 交付

用户要「某演员的全部作品 / 磁力链 / 预览图，做成 PDF」时的整套配方。以 K-av 演员为例，任何 TMDB 有收录的演员通用。

## 1. 抓片目（TMDB 演员页）

- `https://www.themoviedb.org/person/<id>?language=ko-KR` 有 Cloudflare 墙：curl 只回 ~2.6KB 挑战页，**必须 browser_exec** 打开（真实 Chrome 能过）。
- 片目在 `class="credits_list"` 到 `<footer` 之间。**别按 `<tr>` 逐行正则**——部分行结构不同，逐行只拿到 63/83；可靠做法是整段扫 `/movie/(\d{5,7})` 去重，再用 `<td class="year">(\d{4}|—)</td>` + `<bdi>标题</bdi>` 的块级正则建 id→(年, 标题) 映射。
- 标题里有角色名（`<span class="character">`），客串片也在列表里——需要「主演作」时按角色名过滤，或干脆全给并注明含客串。
- 交叉源：namu.wiki 演员词条（作品年表）、韩系串流站（Setflix 等）。

## 2. 抓海报

- 海报不在演员页（只有 8 张 known-for）。逐部 `https://www.themoviedb.org/movie/<id>?language=ko-KR` 读 `document.querySelector('meta[property="og:image"]').content`（w500 路径）。
- browser_exec 里循环 `goto_url` + `time.sleep(1.2)`；83 部约 2 分钟/批，拆成 40 部一批避免超时。
- 取不到 og:image 的片 = TMDB 无海报（真实存在，别当失败重试）。
- 图床直下：`https://media.themoviedb.org/t/p/w500/<path>`，urllib/curl 均可，线程池 8 并发 ~7MB/82 张。
- 演员头像只有 `w300_and_h450_face` 可用；`w640` 会 400。

## 3. 多页 PDF（PIL，无 reportlab 也能做）

```python
pages[0].save(out, save_all=True, append_images=pages[1:], resolution=150)
```
A4 @150dpi = 1240×1754。4 列海报网格：cell 宽 ≈ (1240-2*56-3*14)/4，图高 = 宽×750/500，标题区 74px，每页 3 行 = 12 部。

### 韩文 + 简体中文混排：必须 per-char 字体回退

Windows 没有同时覆盖两者的字体：`malgun.ttf` 有韩文 + 繁体 Hanja，但缺简体字（尘、贺、广…）；`simsun/msyh/simhei` 有简体但没有韩文。用 .notdef 位图哈希判缺字，逐字选字体：

```python
PRIMARY, PRIMARY_B = "C:/Windows/Fonts/malgun.ttf", "C:/Windows/Fonts/malgunbd.ttf"
FALLBACK, FALLBACK_B = "C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/msyhbd.ttc"

def _sig(f, ch):                     # 渲染成小图取哈希；缺字时各字号都渲染同一个 .notdef
    im = Image.new("L", (72, 72), 0)
    ImageDraw.Draw(im).text((6, 6), ch, font=f, fill=255)
    return hashlib.md5(im.tobytes()).hexdigest()

def font_for(ch, size, bold=False):
    p = PRIMARY_B if bold else PRIMARY
    f = ImageFont.truetype(p, size)
    if _sig(f, ch) == _sig(ImageFont.truetype(p, size), "\ue000"):
        f = ImageFont.truetype(FALLBACK_B if bold else FALLBACK, size)
    return f

def tw(d, x, y, text, size, color, bold=False):   # 逐字绘制
    for ch in text:
        f = font_for(ch, size, bold)
        d.text((x, y), ch, font=f, fill=color)
        x += d.textlength(ch, font=f)
```

排版前先做一次冒烟：渲染 `蔡尘贺 아는사이 승하` 之类混合串，确认无空心方框——只看其中一种语言会漏掉另一边的缺字。

### 排版陷阱

- 用累加 `y` 往下排时，**图片块与文字块同列要先取 `max(y, 图片底部+间距)`**。简介折行后实际高度常超出预估，统计卡片会压到头像上（本轮踩过）。
- CJK 换行按字符切（`textlength` 逐字累加），英文磁力链按词切再兜底硬切；磁力按 `&tr=` 截断再显示，完整链留给 txt 附件。

## 4. 数据与成品

- 先把 sukebei 元数据落盘 JSON：`title / date / size / seeds / leech / done / magnet`，PDF 与 txt 都从 JSON 生成，绝不硬编码到脚本里。
- sukebei `/view/<id>` 字段结构：`<div class="col-md-1">Seeders:</div><div class="col-md-5"><span style="color: green;">0</span></div>`——正则要带冒号，且值 div 可能带额外属性（`data-timestamp="..."` 的 Date 行），用 `<div class="col-md-5[^"]*"[^>]*>` 兼容。
- 成品放 `<WORK_DIR>\<项目名>\`，**不要放 `<HERMES_HOME>\cache\scratch`**：scratch 空闲 24h 会被清，用户回头找文件就是「PDF 没了」。中间件（posters/、HTML、build 脚本）可以删，但片目+磁力 JSON 要留，否则重跑就是 83 次浏览器导航。
- QQ 交付可走 `qqbot-media-delivery`（本机私有 skill，未随仓库发布）：长任务成品走 zip + 探针主动推送。
