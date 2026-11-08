# 搜图源 HTTP 协议手册（免浏览器）

配套脚本：`../scripts/soutu_http_probe.py`（纯标准库，`python scripts/soutu_http_probe.py --self-test` 可离线自检）。

浏览器只在两种情况下出场：需要登录态，或撞 Cloudflare 需要人机点击。其余全部走 HTTP。

---

## 0. 一句话选源

| 目标 | 首选 | 备注 |
|------|------|------|
| 二次元插画找 P 站/推特原帖 | SauceNAO（有 key）/ Yandex | SauceNAO 的 Twitter 索引 **2019-12 起停更**，近期推图只能靠 Yandex / ascii2d |
| 本子单格截图找车号 | soutubot | 需先过 CF |
| 三次元 / 直播帧 / 转载页 | Yandex `cbirSites` | 强在「有网页引用的图」，不擅长精确溯源二次元插画 |
| 纯关键词找二次元图 | Safebooru DAPI | 免 key、无 CF |
| 裁剪/旋转/调色过的图 | ascii2d `bovw` | `/color/` 换 `/bovw/` 再 GET 一次 |

---

## 1. Yandex（`yandex.ru`，免 key）

**端点**：`POST {base}/images/search?rpt=imageview&format=json&request={"blocks":[{"block":"b-page_type_search-by-image__link"}]}`

- `base` 用 **`https://yandex.ru`**，比 `yandex.com` 反爬松、大陆更稳。
- multipart 字段：`prg=1` + `upfile`（图片字节）。**body 必须自己拼成完整 bytes**（显式 Content-Length），chunked 上传会 413。
- 头：浏览器 UA + `Origin: {base}` + `Referer: {base}/images/`。

**两步流**：
1. 响应里含 `<html` → 直接解析。
2. 否则是 JSON，取 `blocks[0].params.cbirId`，再 GET
   `{base}/images/search?rpt=imageview&cbir_id=<quote(cbirId)>&cbir_page=sites` 解析。

**解析**：不解析 DOM class，直接正则取 `data-state="([^"]{300,})"` → `html.unescape` → `json.loads` → 找 `initialState`：
- `initialState.cbirSites.sites[]`：**包含该图**的网页（`url` / `title` / `domain` / `thumb.url`）。
- `initialState.cbirSimilar.thumbs[]`：视觉相似图（`linkUrl` / `imageUrl`），sites 为空时兜底。

**来源质量三级分选**（关键，否则 Pinterest 刷屏到看不见真来源）：
- high：booru（`donmai.us` / `donmai.moe` / `safebooru.org` / `yande.re` / `konachan.*` / `gelbooru.com` / `nhentai.net` / `e-hentai.org` / `hitomi.la`）、画师平台（`pixiv.net` / `x.com` / `twitter.com` / `skeb.jp` / `fanbox.cc` / `fantia.jp` / `dlsite.com` / `booth.pm` / `patreon.com`）、资料（`wikipedia.org` / `fandom.com` / `bangumi.tv` / `vndb.org`）、求物与视频源（`telegra.ph` / `t.me` / `bbs.spring-plus.net` / `threads.com` / `weibo.com` / `bilibili.com` / `youtube.com` / `javdb.com`）。
- low：`tumblr.com` / `reactor.cc` / `joyreactor.cc` / `wattpad.com` / 内容农场；**Pinterest 全系用品牌标签匹配**（host 的某个 DNS 标签等于 `pinterest`/`pinimg`/`duitang`/`huaban`），通杀 `.com/.ru/.co.uk/za.pinterest.com` 等数十变体。
- neutral：其余站点。
- 排序 `high → neutral → low`（同级保持原始顺序），**排序之后**按域名分桶，每桶最多 `--max-per-domain`（默认 2），Pinterest 全系合成一个桶。
- 兜底不空：过滤后再截 `--top-k`。
- **诚实告警**：结果里没有任何 high 来源时，明确输出「未找到包含该图的图库来源，以下为视觉相似图（可尝试 SauceNAO 精确反查）」。绝不把相似图说成来源。

域名匹配用「后缀匹配」（`host == suffix` 或 `host.endswith('.' + suffix)`），不要用子串包含——`notdanbooru.donmai.us.evil.com` 会骗过子串判断。

**分级只按域名，不等于「页面真的含这张图」**：实测一张随机噪声 PNG 也会在 `cbirSites` 里给出 `en.wikipedia.org/wiki/File:Tux_encrypted_ctr.png` 这种「视觉相似的噪声图」页面，且因为域名是 wiki 被判 high。所以 `high` 只代表「优先看」，定锤前仍要打开页面 / 比对返回缩略图与用户图是否同一张。`SIMILAR_ONLY_WARNING` 只在**完全没有** high 域名时触发，它是「连值得看的都没有」的兜底提示，不是「有 high 就一定对」的保证。

---

## 2. soutubot.moe（搜图Bot酱，schema 2.2）

**端点**：`POST https://soutubot.moe/api/search`，multipart 字段 `file` + `factor`（`1.2` 常规 / `1.4` 严格）+ `metadata_mode=display` + `top_k`。

- **UA 必须用 Camoufox 的 Firefox UA**（`...rv:152.0) Gecko/20100101 Firefox/152.0`）——`cf_clearance` 绑 UA + 出口 IP，换 UA 立刻 403。
- 命中判据：`results[].path_segments` 非空。
- 置信阈值：`factor=1.4` → **35**；否则 **45**。`score >= 28` 进主列表。
- 标题回退链：`metadata.title.japanese_or_alias`（日文/中文原名）→ `metadata.title.primary`（英文）→ 平铺 `metadata.title` 字符串。
- 链接回退链：`page_url` → `chapter_url` → `source_url` → `metadata.source.url`。
- **HTTP 200 但非 JSON = 挑战页，必须报错**，不能静默当「没搜到」（与 Safebooru 刻意不对称：那边无结果本来就返空体）。
- `status: partial` 常由某个源库 connect timeout 造成，重发 1–2 次常出高分结果。

---

## 3. SauceNAO（需 key）

**端点**：`POST https://saucenao.com/search.php?output_type=2&numres=&minsim=&hide=[&dbmask=]`

- 表单字段 `file`；`api_key` 放 query。
- **`dbmask` 位掩码**：`0x20`=pixiv、`0x40`=pixivhistorical（**`96` = 0x20|0x40 = 现行 pixiv + 历史库**；历史库里多是已删/老作，所以结果会混进老图——不是「搜不到新图」）、`0x200`=danbooru、`0x1000`=yande.re、`0x20000`=nhentai、`0x10000000000`=Twitter、`0x80000000000`=Skeb。
- **全库时省略 `dbmask` 参数，不要发 `dbmask=0`**（位掩码语义下 0 可能被当成「不启用任何库」）。
- 配额：响应 `header.short_remaining`（4 次/30 秒）、`long_remaining`（150 次/天）；耗尽要明确提示，不要报「没搜到」。`header.status != 0` = 错误。
- `header.similarity` 是**字符串**（`"95.42"`），安全转 float。
- 链接回退：`data.ext_urls[0]` → `pixiv_id` 拼 `https://www.pixiv.net/artworks/{id}` → `data.source`。
- 画师：`creator` / `author_name`，退化用 `member`（uid）拼 `https://www.pixiv.net/users/{uid}`。
- 缩略图带 `auth`/`exp` 签名会过期，**先下载再发**，别把 URL 当文本外传。

---

## 4. ascii2d（免 key，CF 严）

**端点**：`POST https://ascii2d.net/search/file`，字段 `file`；头带 `Accept-Language: ja,en;q=0.8`。

- 跟随重定向后的**最终 URL** 形如 `/search/color/<hash>` = 色彩检索结果。
- **特征检索**：把最终 URL 里的 `/color/` 换成 `/bovw/` 再 GET 一次（剪裁/旋转/调色图更有效，慢一倍）。
- 解析：`div.row.item-box` 作用域内取 `h6`（标题）、`small`（来源标记：`pixiv`/`twitter`/`fanbox`/`fantia`/`misskey`/`ニコニコ静画`/`ニジエ`，大小写不敏感）、外部链接（首个=作品，次个=画师）。
- 标题噪声直接置空：`詳細掲示板のログ` / `2ちゃんねるのログ`。
- **不返回相似度**：`score` 留 `None`，**绝不要**套 SauceNAO 的 `min_similarity` 过滤，否则结果被全滤光。
- 近期 Cloudflare WAF（指纹 + Turnstile）严，直连/机房代理易 403；有日本住宅代理再开。

---

## 5. Safebooru（免 key、无 CF）

`GET https://safebooru.org/index.php?page=dapi&s=post&q=index&tags=<a+b>&limit=N&pid=<0起>&json=1`

- 多标签用 `+` 连接（AND）；`pid` 从 0 开始。
- **无结果时可能返回空响应体**（不是 `[]`），必须容错，不能当异常。
- `rating` 过滤：safe 时丢弃 `sensitive`/`questionable`/`explicit`。

---

## 6. 复用 cf_clearance（CF 硬墙站点）

```bash
# 1) 过挑战并导出 Netscape jar（turnstile-bypass skill）
cd <HERMES_HOME>/skills/web/turnstile-bypass && ./.venv/Scripts/python.exe \
  scripts/human_click.py --url "https://soutubot.moe/" --cookie-out <HERMES_HOME>/cache/scratch/soutubot_jar.txt

# 2) 带着 jar + 同一个 UA 打 API
python <HERMES_HOME>/skills/acg-reverse-image-search/scripts/soutu_http_probe.py soutubot \
  --image <img> --cookie-jar <HERMES_HOME>/cache/scratch/soutubot_jar.txt \
  --ua "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:152.0) Gecko/20100101 Firefox/152.0"
```

三要素缺一不可：**同一 UA + 同一出口 IP + 同一 jar**。换节点或换 UA → 依旧 403。
撞墙先查出口 IP 类型（`curl https://api.ipify.org`）；数据中心出口必吃 hard challenge，住宅线路常常裸 curl 就过。

---

## 7. 本机实测结论（随出口/时间会变，采信前自己重跑一遍）

| 源 | 结果 |
|----|------|
| Yandex | ✅ 通，~5–6s；`cbirSites` 能出 high 来源并正确排序 |
| Safebooru | ✅ 通，~1s，中文/日文标签均可 |
| soutubot | ✅ 过 CF 后通：`human_click.py` 点一次 → cf_clearance → 本脚本带 jar 出 JSON（无命中也会正常报「低于 min-score」而不是 403） |
| ascii2d | ⛔ 挑战能解（cf_clearance 拿到），但 `POST /search/file` 仍 403 `Attention Required!`（CF WAF 拦截；urllib 与页内 fetch 都一样）→ 搜索只能浏览器手动传图，或换日本住宅 IP |
| SauceNAO | ⏸ 需 key（脚本在取图前就退出：不读盘、不下载、不发请求，属预期行为） |
| human_click.py | ✅ 2026-11-01 修复后连过 soutubot.moe 与 ascii2d.net（headed/headless 各一次），jar 可复用 |

`human_click.py` 的两个关键修复（细节见 turnstile-bypass skill）：

1. **GPU 崩溃**：turnstile 的 WebGL 探测让 Firefox 在 RTX 50xx 上丢 D3D12 设备（`CompositorDevice does not exist` / `WebGL context was lost` / `Failed to find D3D12 adapter with the same LUID`），渲染进程死后 Playwright 报 `Browser.close: Connection closed while reading from the driver`。现在默认**软件渲染**，`--gpu` 才走硬件。
2. **两类挑战**：interactive（iframe 有真实尺寸 ≈300×65，可点）vs managed/invisible（`page.frames` 里有 turnstile、但 `frame_element()` 报 0×0、主文档无 iframe，点不到东西）。后者只等不点，超时输出 `challenge_kind: "managed"` 并建议换出口。

`soutu_http_probe.py --self-test` 覆盖：来源分级/去重桶/Yandex fixture 解析/soutubot 阈值与标题回退/SauceNAO 配额与回退链/ascii2d HTML/cookie jar 域匹配，全部离线。

---

## 8. 维护这个脚本时的实现坑（Python stdlib）

- **`urllib` 的 opener 不能给 `open()` 传 `context=`**（`TypeError: unexpected keyword argument 'context'`）：要 `build_opener(HTTPSHandler(context=ctx))`，而且 `ctx` 必须在构造 handler **之前**创建。
- **multipart 自己拼完整 bytes**：`urllib` 按 `len(body)` 自动补 `Content-Length`，天然避开 chunked 上传引发的 413；不要改成流式。
- **HTML 内嵌 JSON 的 fixture 只 escape 一次**：`json.dumps(...).replace('"', '&quot;')` 直接拼进 `data-state="..."`。**不要**在拼之前 `html.unescape` —— 那会把转义还原成裸引号，`data-state="([^"]{300,})"` 直接匹配 0 条，自检会红但页面看着「没错」。
- **Windows 打印日文/中文标题**：启动时 `sys.stdout.reconfigure(encoding="utf-8", errors="replace")`，否则 cp936 抛 `UnicodeEncodeError` 把整轮中断在第一条命中上。
- **Netscape cookie jar 自己解析**：按 `host == dom or host.endswith("." + dom)` 匹配，**不要**子串匹配（`evil-soutubot.moe` 会误发 cookie）；`#HttpOnly_` 前缀要剥掉，过期项丢弃。
- **错误信息不要整段吐挑战页 HTML**：先判 `just a moment` / `challenge-platform`，给一句可读诊断 + 下一步动作（导 jar / 换住宅出口），否则 403 的 200 行 HTML 会淹掉真正结论。
- **每加一个 provider 就补一组 fixture 断言**，改完先 `--self-test` 再真机单源各跑一次；只有真跑通的源才配写进 SKILL.md 正文。
- **文档与代码冲突时先判断谁对**：文档里关于脚本的每一条（参数名、默认值、请求头、失败时机）都要**实跑**核过，不能靠读代码。如果文档描述的是更合理的行为（给日本站发 `Accept-Language: ja`、没 key 时在取图前就退出），**改代码去满足文档**，而不是把文档降级成现状。
