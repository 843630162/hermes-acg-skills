---
name: ACG magnet torrent search
description: 用户要搜磁力、种子、BT 时使用：Router 默认只在三次元自动搜磁；二次元搜图闭环不要调用本 skill，除非用户事后明确要磁力。三次元严格按 javdb-cli → JavDB 网页 → sukebei nyaa。
---
# ACG 磁力 / BT 搜索

用户要找 **磁力链接、种子、BT 资源** 时使用。只负责检索与比对条目，**不自动开下、不批量打种**，把候选交给用户选择。

**Router 默认**：只给 **三次元** 自动调用本 skill。二次元反向搜图闭环**不要**进来；仅当用户事后明确说「要磁力 / 种子 / BT」时，才用下面的二次元索引。

## 安全

- 输出磁力前核对：标题、字幕组、体积、是否合集、是否标注广告/病毒常见特征（异常体积、乱码名）；存疑则标风险。

## 免责声明

本 skill **仅供学习与技术参考**。只负责检索与比对候选，**不自动开下、不批量打种**。不提供、不保证任何磁力或在线源的合法性或可用性；使用者须自行遵守所在地法律与站点条款。疑似未成年内容必须拒绝。

## 第 0 步：先分二次元 / 三次元

| 类型 | 何时走 |
|------|--------|
| **二次元** | 表番、里番、本子包、Gal/H 游、字幕组动画等 |
| **三次元** | 番号、JAV、FC2、实拍、女优作品等 |

- 输出先写：**资源类型：二次元 / 三次元**。
- 由搜图 skill 或 Router 传入类型时，**直接沿用**，不要再混搜。
- 仅有番号（`ABC-123` / `FC2-PPV-…`）→ 默认 **三次元**。
- 仅有番名/字幕组用语 → 默认 **二次元**。
- **不要**用三次元主链去搜表番；**不要**把花园/Anime Garden 当作三次元主链。

## 输入规范化

1. 取出：作品名（中/日/英）、季数集数、字幕组偏好、分辨率；或规范化番号。
2. 有标题/番号文字时：先网页检索对齐番号，**不要**为了搜磁先跑反向搜图。有图无文字时才跑 [ACG reverse image search](acg-reverse-image-search)。二次元且用户没明确要磁力 → **结束，不要继续本 skill**。
3. 三次元有番号时：可先跑 [JAV bangou lookup FC2](jav-bangou-lookup-fc2) 核对标题，再用番号/标题搜磁。
4. 浏览器：静态列表优先 curl；必须浏览时一次 `new_tab` 之后 `goto_url`，读完就走，禁止翻页循环开新标签。

---

## 二次元索引（仅用户明确要二次元磁力时；顺序保持）

### 表番 / 字幕组

1. **Anime Garden** — `https://animes.garden/`（多源聚合；API `https://api.animes.garden/resources` 可程序化查）
2. **动漫花园** — `https://share.dmhy.org/`
3. **萌番组 Mikan** — `https://mikanani.me/`（镜像 `https://mikanime.tv/`）
4. **爱恋** — `http://www.kisssub.org/`
5. **acg.rip** — `https://acg.rip/`
6. **bangumi.moe** — `https://bangumi.moe/`
7. **Nyaa** — `https://nyaa.si/` ；备用 `https://nyaa.land/`
8. **Anime Tosho** — `https://animetosho.org/`（RSS/Torznab；DDL 镜像）
9. **SubsPlease** — `https://subsplease.org/`（英文组）
10. **菲特动漫** — `https://www.fitacg.com/` ；**简单动漫** — `https://www.36dm.org/`
11. **MagHub** — `https://www.maghub.org/` 游客磁力聚合（主收 AI 短剧/二次元）：首页输入框 → 点「搜尋」按钮（XHR POST `/search` → 跳 `/search?t=<token>`）；直接开 `/search?q=` 会显示「搜尋連結已過期」无效。AI 漫画类常无收录，结果偏噪音需按标题过滤

### 里番 / 成人同人磁链（二次元）

1. **sukebei** — `https://sukebei.nyaa.si/`
2. **sukebei.pantsu** — `https://sukebei.pantsu.cat/`
3. Tokyo Tosho 对应分区 — `https://www.tokyotosho.info/`
4. **老王论坛（`laowang.vip`）无磁力/死种兜底** — 当常规磁力站（Nyaa/sukebei/花园）无磁力链或死种时，调用 [laowang-cli](laowang-cli) 搜索（`laowang search "<关键词>" --forum 44` 二次元视频 / `--forum 517` 二次元本子），再用 `laowang thread <tid>` 提取网盘分流（百度/夸克/PikPak/123pan）、种子附件或 `remote_play` 免费在线视频/种子（付费项默认 dry-run，未经用户明确同意严禁 `--confirm`）。

### Gal / H 游磁链（二次元）

1. **ggbases** — `https://www.ggbases.com/`
2. **sukebei**（关键词 + 厂商/原名）
3. 论坛型站点（北+、2DJGAME 等）仅作「有人发过」线索，优先摘公开磁链，不代替用户登录灌水。
4. **老王论坛（`laowang.vip`）无磁力/死种兜底** — 当 ggbases / sukebei 无磁力链或死种时，调用 [laowang-cli](laowang-cli) 在游戏下载区搜索（`laowang search "<关键词>" --forum 65`），再用 `laowang thread <tid>` 提取网盘分流或种子附件（未经用户明确同意严禁 `--confirm` 购买）。

### RSS / 自动化线索（可选，二次元）

- Anime Garden RSS / MCP
- Mikan / DMHY 的 keyword RSS
- AutoBangumi 仅作「如何订阅」说明，不在本 skill 里替用户部署

**二次元执行**：用规范化标题在 **Anime Garden（或花园）+ Nyaa/sukebei（按是否成人向）** 至少两端交叉；按字幕组信誉、分辨率、单集/合集、时间、体积排序。

---

## 三次元索引（严格按序）

只按下面顺序，**不要打乱**，也不要插入花园/Nyaa 表站等二次元源当主链。

1. **JavDB（优先 javdb-cli）**
   - 二进制可用时先用 CLI：`javdb search <规范化番号> --magnets N`（一次完成搜索、筛选、排序与磁力获取；`--cnsub`/`--hd` 在排序前筛选，N=0 返回全部），或 `javdb magnets <番号>` / `--best`。执行前按 [javdb-cli](javdb-cli) skill 用 `javdb <command> --help` 核对参数；CLI 无需登录即可取磁。
   - `javdb search <番号> --magnets 0` 是模糊搜，结果常带相近番号（如 DEAA-004 旁边给 DEAB-004）。精确番号 0 磁力而相近番号有磁力时，别直接当目标命中：对两者各跑 `javdb detail` 确认是不同作品后，把相近番号作为「是否记错」候选列出（标题/女优/前几条磁力），并注明是另一部作品。
   - `javdb detail` 的 `maker_name` 若是 FANZA 素人 label（见下方官方预览型判定），确认本步 0 磁力后可结束，不必跑完第 2–4 步。
   - CLI 缺失/失败，或 JavDB 结果不足时，再打开网页 `https://javdb.com/` 条目页采集磁链/网盘线索与标题元数据。先做资料核对，再摘磁；无磁链再进入下一步。输出中注明走的是 CLI 还是网页。
2. **sukebei (Nyaa)** — `https://sukebei.nyaa.si/`  
   - 关键词优先：`规范化番号`，其次官方/资料站标题。
   - 查询参数：`?q=<关键词>&f=0&c=0_0`（2026-11-07 实测 200）。**只有 `q` 是搜索参数**：`?query=` 会静默回首页最新列表（实测 ~134KB / 75 行无关条目），`?rss=1&q=` 也无效（~45KB HTML / 0 `<item>`）；RSS 只有 `?page=rss&q=` 能用。`&f=all` 会 400（合法值 0/1/2），但 `&c=0_0` 正常——别把整条 `&c=` 当禁区。`/json`、`/json.php` 均 404。
   - **零命中前必须过对照词**：先查已知存在的 `MIDE-599`（应 19 行 / ~45KB），或直接跑 `python <HERMES_HOME>/skills/acg-magnet-torrent-search/scripts/sukebei_search.py "<词>" --proxy http://127.0.0.1:10808`（内置对照 + 搜索框回显校验 + gzip 解压；管道坏时退出码 2）。body 为 0 字节、gzip 没解压、解析 0 行，都只算「没查成」，不许当成「没有资源」。
   - 列表页结构：`<tr class="default|success|danger">` + `<a href="/view/<id>" title="...">` + `href="magnet:?xt=..."`。**站内没有 `/f/<id>/` 这种链接**，拿它解析必然 0 条（2026-11-06 误判原因之一）。完整 `dn`/`tr` 进 `/view/<id>` 取。
3. **OneJAV** — `https://onejav.com/search/?q=关键词`（搜索格式已验证）  
   - 真磁力/torrent 源（页面带体积 GB/MB + Torrents 标签）。番号搜不到时用**日文原标题 / 卖家名 / 女优名**再搜；适合官网下架、JavDB+sukebei 都无收录的冷门 FC2。
   - 搜索页出现 `No torrents found.` 即无结果；页面里的最新 torrent 列表（如 `/torrent/sdmm243` 侧栏）是站点最新上传，与本次搜索无关，不要当成命中。
4. **JAVHouse** — `https://javhouse.org/`（需登录，用户已手动登录过）  
   - 搜索必须用首页 POST 表单：`do=search&subaction=search&story=关键词`；URL 路径 `/search/番号` 无效会报 not found。
   - 真磁力源：详情页 `https://javhouse.org/video/<id>-<code>.html` 有 **Download Magnet**（完整 `magnet:?xt=...&tr=...`）+ **Download Torrent**。点结果里的视频链接可能跳外部广告页，要直接 goto 详情页 URL。

前一步已有足够优质磁链（≥1 条体积合理、非明显广告名）可结束；否则必须跑完第 4 步再下结论。仍无可用磁力时走下面「无磁力 → 在线视频兜底」，不要直接下『未找到』结论。

**「足够」按变体覆盖判，不只按条数**：JavDB 同一个番号常只给 3 条同源 rip（hash 不同、体积几乎一样、都无中字），而 sukebei 才是变体库——**中文字幕 / 无码破解 / Reducing Mosaic 薄码 / H265 小体积** 往往只在 sukebei 有。用户明确要磁力时，哪怕 JavDB 已返回结果，也额外花一次 `curl -sL --compressed` 拉一次 sukebei 列表补变体；漏掉中字版是最常见的返工原因。
- sukebei 结果行可一次解析出体积/做种/下载数，按 中字 > 做种数 > 体积 排序推荐。
- 标题带 `+++`、`★★★` 等前缀是上传者刷搜索排名的惯用手法，不代表资源有毒：照常核对信息，但在输出里点一句前缀性质，别让用户以为是被篡改的假档。

---

### 韩国 AV（K-av）捷径（2026-11 实测，채승하 例）

K-av（韩国实拍，如前女团成员转型演员）**JavDB 基本无收录**：`javdb search` 按韩文/罗马音均空属正常，确认 0 收录后可直接进 sukebei，不算「跳过 JavDB」。要点：
- **sukebei 用韩文名搜**（`채승하`/`승하`）；罗马音（`Seungha`）常 0 命中。命中后 `/view/<id>` 取 magnet + seeds/leeches/size。
- **TMDB 收录 K-av 片目与演员**：演员页（`themoviedb.org/person/<id>`）CF 墙 → browser_exec 过墙；credits_list 表（`data-url="/movie/<id>"` + `year` + `bdi` 标题 + 角色名）= 完整片目（含客串片，需按角色名过滤）。
- **海报批量取**：逐 movie 页读 `meta[property=og:image]`（w500），browser 内 `goto_url` 循环 + sleep 1.3s；无 og:image 的片=TMDB 无海报。图床 `media.themoviedb.org/t/p/w500/<path>` 可 curl 直下。
- **片目交叉源**：namu.wiki 演员词条（含作品年表）、Setflix 等韩系串流站。
- 交付「作品+预览图」时：海报网格做成 PIL 多页 PDF 比逐图发 QQ 稳。配方（TMDB 抓取、网格排版、**韩文+简体中文混排的 per-char 字体回退**、成品落盘位置）见 `references/works-poster-pdf.md`——单用 `malgun.ttf` 会把简体字（尘/贺/广…）渲成方块。

### 无磁力 → 在线视频兜底（仅三次元）

**触发条件**：三次元番号跑完 JavDB（javdb-cli）→ sukebei → OneJAV → JAVHouse 四源后仍无可用磁链（或 `magnets_count=0`）。FC2 PPV「原盤送付」类商品惯例卖文件不挂 BT，各流站只有在线页、无磁力属正常现象——兜底是常规出口，不是异常。

官方预览型作品不需要跑本兜底流程（也无需磁力链搜索）；这些站点仅在**核对最终结果时做预览/图片对比**。

**步骤 0：官方预览型判定**

作品来自官方付费源——FC2 PPV（原盤送付、卖文件不挂 BT），或 moodyz.com / video.dmm.co.jp/av/ 等 AV 正版官方收费站——且其在线渠道最终都跳转到 FC2 官方播放器（`https://adult.contents.fc2.com/embed/<纯数字>`，免费约60秒预览）或该官方付费页时 → 判定为「官方预览型」：**不需要**做在线视频搜索，也**不需要**做磁力链搜索；这些站点仅在**核对最终搜索结果时**用于预览/图片对比（身份核验：番号、标题是否一致，播放器有没有跳到别的作品）。

**FANZA 原创素人 label 作品同样判「官方预览型」**：JavDB `javdb detail` 的 `maker_name` 为 FANZA 素人 label（如 電影シロウト-青春-，番号系列形如 DEAA/DEAS-xxx）时，官方家在 `https://video.dmm.co.jp/amateur/content/?id=<去连字符品番>`（年龄认证墙 + 地区限制，非日本出口会跳「not available in your region」）；惯例卖文件不挂 BT，整系列 0 磁力是正常现象。JavDB 步骤确认 0 磁力后可直接交 FANZA 官方页 + JavDB 预览，不必再跑 sukebei/OneJAV/JAVHouse。标题/素人实名/配信日可用 `https://av-wiki.net/<去连字符品番>/` 交叉核对。别追 label 自有域名：`1pondo.net`（原 1Pondo）全球 NXDOMAIN，`1pondo.com` 是另一家 cam 聚合站、这类品番一律软 404——FANZA 素人 label 的官方家只有 `video.dmm.co.jp/amateur` 一处。

**步骤 A：按名字搜在线视频**。用日文标题中最独特的短语（从 JavDB `javdb detail <纯数字>` 的 `origin_title` / `title` 取；避开「中出し」「素人」这类通用词）做 web_search / 各站站内搜索；可用 **番号**、**女优名/扮演者名**、**作品名** 三种关键词交叉。FC2 号在 JavDB 只输纯数字（如 `javdb detail 4972767`），整串 `FC2-PPV-xxxxx` 会假阴性。

**步骤 B：已验证的在线视频源（2026-09 实测）**

| 站点 | 搜索 / 入口方式 | 备注 |
|------|----------------|------|
| xjav.jp | `https://xjav.jp/?s=<番号或数字>` | 结果页 `/videos/<id>` |
| miss-jav.com | `?s=` 搜索 | 条目页 `/videos/<id>/` |
| shirouto-kantei.com | 条目页 `/works/fc2-<纯数字>/` | 带评分与价格 |
| glamoroustube.com | 站内按作品名/女优名搜 | — |
| FC2 官方 embed | `https://adult.contents.fc2.com/embed/<纯数字>` | 免费预览；完整片需 FC2 コンテンツマーケット购买 |
| TokyoMotion | `https://www.tokyomotion.net/search?search_query=<关键词>&search_type=videos&type=public` | 区分 `type=public`（HTML 含 `<source src=".../vsrc/hd/...">` 可直看）与 `type=private`（仅好友可见，常含完整分P） |
| PikPak / ApexDrive 云盘分享 | `web_search` `"mypikpak.com/s/"` 或 `"newapexcloud.com/s/"` + 创作者 ID/日文名（另可查 TokyoMotion 用户的 `/user/<name>/wall` 留言板） | MyFans / CandFans 同人长片主力完整版来源（见下方免登录核验法） |
| 老王论坛 (`laowang.vip`) | 调用 [laowang-cli](laowang-cli)：`laowang search "<番号或标题>"`（可加 `--forum 40` 亚洲无码 / `--forum 41` 亚洲有码 / `--forum 43` 国产自拍）→ `laowang thread <tid>` | 无磁力时的论坛网盘/种子/在线视频兜底：免扣币提取网盘链接、`remote_play` 免费 `m3u8`/`.torrent`，或 dry-run 预览付费附件/资源卡（未经用户明确同意严禁 `--confirm` 购买） |

注意：
- **老王论坛 (`laowang-cli`) 兜底**：当公开磁力站无磁链时，用 `laowang search "<番号或标题>"`（按需加 `--forum 40` 亚洲无码 / `--forum 41` 亚洲有码 / `--forum 43` 国产自拍）搜索帖子，再执行 `laowang thread <tid>` 免扣币提取百度/夸克/PikPak/123pan 网盘链（自动 `jnpar_pansell:check` 验活）、`remote_play` 的免费 `m3u8` 与 `.torrent`，或以默认 dry-run 模式预览付费附件/资源卡价格与余额（未经用户明确同意严禁加 `--confirm` 扣软妹币）。
- 流站静态 HTML 常无 `<video>` 标签（JS 懒加载）；要拿时长/确认可播放时，用 browser_exec 打开页面滚动或点播放后读 `video.duration`。
- **PikPak 分享链免登录核验**：直接 GET `https://mypikpak.com/s/<share_id>`（有效分享 HTML 约 130KB，失效/空壳约 68KB），解析页面 `<script>` 内 Nuxt SSR 的 `ShallowReactive` 数组即可拿到 `share_status: "OK"`、各文件 `name`、`size`、`duration`（秒）、分辨率、SHA1 `hash` 及截图 `https://sg-thumbnail-drive.mypikpak.com/v0/screenshot-thumbnails/<HASH>/720/2048`，无需登录即可核实完整分P与时长。
- **TokyoMotion 上传者 profile 是 PikPak 富矿**：`https://www.tokyomotion.net/user/<name>` 的 More Info 里 `Here for:` / `Favorite Sex categories:` 常直接写 PikPak 分享链（grep `mypikpak`）。同一位搬运工往往一次挂齐同一创作者的多部完整版。
- **TokyoMotion 直链要 Referer**：`/vsrc/hd/<hash>`、`/vsrc/sd/<hash>` 裸 GET 返回 403；带 `-e https://www.tokyomotion.net/` 才 206。页面内 HTML5 播放器自动带 Referer，所以给用户的是页面 URL；要用 yt-dlp/IDM 抓才补 `--referer`。
- **CandFans 全量作品清单（免登录）**：`https://candfans.jp/api/contents/get-timeline?user_id=<数字>&page=N`，每页 10 条，`title` / `price` / `movie_time`(秒) / `post_date` 全给。`user_id` 从 `https://candfans.jp/<user_code>` 的 `__NEXT_DATA__` → `props.pageProps.dehydratedState.queries[0].state.data.user.id` 取。`page=1..N` 直到空数组（305 帖约 31 页）。`sample.m3u8` 直取 AccessDenied，预览只能走流站。
- **ApexDrive（`newapexcloud.com/s/<token>` → `link.myapexdrive.com/s/<token>`）免登录列目录**：向 `https://partner.apexdriveapi.com/v2/s/access/home`（根目录）或 `/v2/s/access/dir`（子目录，带 `parent_id`）POST `{"share_token":"<token>","offset":"","page_size":100}`，请求头加 `Apex-Share-Acl: <token>:<password>`（无密码即 `<token>:`）。

**步骤 C：返回视频时长 + 区分预览/完整版（用户硬性要求）**
- 必须给出 **视频时长**；只找到预览片段时明确标注「预览」并附可得的时长。
- 打不开链接不要直接丢弃：检查该页标题、播放器加载后是否跳转到其他作品的预览页（embed 可能载入别的片）；用页面 title 里的番号/标题与目标核对身份一致后才交付。

**步骤 D：同作品旧号**。FC2 PPV 常换号重上架，同一作品可能有旧号。把日文独特短语搜出的 **全部命中** 都记下来；若发现旧号（如 FC2-PPV-4719088 与 4972767 为同作品），旧号的在线页、搜索结果乃至磁力链一并返回，并注明新旧号关系。

**步骤 E：输出格式追加字段**。每条在线渠道给 **预览图 URL（封面缩略图）+ 页面链接 + 视频时长 + 完整/预览标注**；旧号结果单独列一块。

---

## 执行步骤（总）

1. 完成第 0 步分类 → 只进入对应分支。
2. 每条候选提取：`标题 | 体积 | 日期 | 来源站 | magnet 或详情页 URL`。
3. 同一资源多站命中时合并，保留最短可信磁链 + 来源列表。
4. 若全空：二次元换别名（罗马音/日文原名）再搜；三次元核对番号写法（补连字符、FC2 在 JavDB 用纯数字检索）后再搜；三次元仍无磁力 → 走「无磁力 → 在线视频兜底」；都跑完仍无结果才如实说没有。

## 输出格式

1. **资源类型**：二次元 / 三次元  
2. **查询词**：实际使用的关键词列表  
3. **推荐（最多 5 条）**：标题、体积、来源、magnet（完整 `magnet:?xt=...`）或种子页  
4. **备选**  
5. **注意**：合集/生肉/广告风险点  

## 不要做的事

- 不要伪造 magnet hash，也不要凭记忆复述 hash：回复和表格里的每条 hash 都必须从本轮抓取的页面 / JSON / 种子文件里直接复制。记忆复述会串条目，效果等同伪造（已发生过：表里 12 条有 10 条是编的）。
- 交付磁力清单时逐条带 seeds / leechers / completed（sukebei `/view/<id>` 的 `Seeders:`/`Leechers:`/`Completed:` 三行可解析），不要只汇总成「全部 seed=0」——用户要靠 done 数判断哪条值得等补种。
- 不要在未获用户确认时调用下载器开始下载。
- 二次元不要只查一个站就结束（至少两端交叉）。
- 三次元不要跳过 JavDB 直接只搜 sukebei；JavDB 优先走 javdb-cli，CLI 不可用再降级网页（须在输出注明）。
- FC2 号在 JavDB+sukebei 都搜不到、且官网显示「找不到商品」（下架）时**别过早下结论**：先用日文原标题/女优名在 OneJAV 交叉一次；该系列可能换号重上架，可在输出里提示用户。
- 不要把 JavDB 当 FC2 官网；官网对比仍归番号 skill。
- 不要在二次元搜图闭环里自动搜磁（Router 默认禁止）；用户明确要磁力除外。
- 不要为翻页循环 `new_tab`；读完当前页用 `goto_url` 或关掉。
- 官方预览型（FC2 PPV / moodyz·dmm 等官方付费源，流站最终都跳 FC2 官方 embed；含 FANZA 原创素人 label）不要再跑在线视频/磁力搜索；这些站点只在核对最终结果时做预览图/图片对比。
