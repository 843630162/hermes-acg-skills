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
10. **菲特动漫** — `https://fitacg.com/` ；**简单动漫** — `https://www.36dm.org/`

### 里番 / 成人同人磁链（二次元）

1. **sukebei** — `https://sukebei.nyaa.si/`
2. **sukebei.pantsu** — `https://sukebei.pantsu.cat/`
3. Tokyo Tosho 对应分区 — `https://www.tokyotosho.info/`

### Gal / H 游磁链（二次元）

1. **ggbases** — `https://www.ggbases.com/`
2. **sukebei**（关键词 + 厂商/原名）
3. 论坛型站点（北+、2DJGAME 等）仅作「有人发过」线索，优先摘公开磁链，不代替用户登录灌水。

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
   - CLI 缺失/失败，或 JavDB 结果不足时，再打开网页 `https://javdb.com/` 条目页采集磁链/网盘线索与标题元数据。先做资料核对，再摘磁；无磁链再进入下一步。输出中注明走的是 CLI 还是网页。
2. **sukebei (Nyaa)** — `https://sukebei.nyaa.si/`  
   - 关键词优先：`规范化番号`，其次官方/资料站标题。
3. **OneJAV** — `https://onejav.com/search/?q=关键词`（搜索格式已验证）  
   - 真磁力/torrent 源（页面带体积 GB/MB + Torrents 标签）。番号搜不到时用**日文原标题 / 卖家名 / 女优名**再搜；适合官网下架、JavDB+sukebei 都无收录的冷门 FC2。
4. **JAVHouse** — `https://javhouse.org/`（需登录，用户已手动登录过）  
   - 搜索必须用首页 POST 表单：`do=search&subaction=search&story=关键词`；URL 路径 `/search/番号` 无效会报 not found。
   - 真磁力源：详情页 `https://javhouse.org/video/<id>-<code>.html` 有 **Download Magnet**（完整 `magnet:?xt=...&tr=...`）+ **Download Torrent**。点结果里的视频链接可能跳外部广告页，要直接 goto 详情页 URL。

前一步已有足够优质磁链（≥1 条体积合理、非明显广告名）可结束；否则必须跑完第 4 步再下结论。仍无可用磁力时走下面「无磁力 → 在线视频兜底」，不要直接下『未找到』结论。

---

### 无磁力 → 在线视频兜底（仅三次元）

**触发条件**：三次元番号跑完 JavDB（javdb-cli）→ sukebei → OneJAV → JAVHouse 四源后仍无可用磁链（或 `magnets_count=0`）。FC2 PPV「原盤送付」类商品惯例卖文件不挂 BT，各流站只有在线页、无磁力属正常现象——兜底是常规出口，不是异常。

官方预览型作品不需要跑本兜底流程（也无需磁力链搜索）；这些站点仅在**核对最终结果时做预览/图片对比**。

**步骤 0：官方预览型判定**

作品来自官方付费源——FC2 PPV（原盤送付、卖文件不挂 BT），或 moodyz.com / video.dmm.co.jp/av/ 等 AV 正版官方收费站——且其在线渠道最终都跳转到 FC2 官方播放器（`https://adult.contents.fc2.com/embed/<纯数字>`，免费约60秒预览）或该官方付费页时 → 判定为「官方预览型」：**不需要**做在线视频搜索，也**不需要**做磁力链搜索；这些站点仅在**核对最终搜索结果时**用于预览/图片对比（身份核验：番号、标题是否一致，播放器有没有跳到别的作品）。

**步骤 A：按名字搜在线视频**。用日文标题中最独特的短语（从 JavDB `javdb detail <纯数字>` 的 `origin_title` / `title` 取；避开「中出し」「素人」这类通用词）做 web_search / 各站站内搜索；可用 **番号**、**女优名/扮演者名**、**作品名** 三种关键词交叉。FC2 号在 JavDB 只输纯数字（如 `javdb detail <纯数字id>`），整串 `FC2-PPV-xxxxx` 会假阴性。

**步骤 B：已验证的在线视频源（2026-09 实测）**

| 站点 | 搜索 / 入口方式 | 备注 |
|------|----------------|------|
| xjav.jp | `https://xjav.jp/?s=<番号或数字>` | 结果页 `/videos/<id>` |
| miss-jav.com | `?s=` 搜索 | 条目页 `/videos/<id>/` |
| shirouto-kantei.com | 条目页 `/works/fc2-<纯数字>/` | 带评分与价格 |
| glamoroustube.com | 站内按作品名/女优名搜 | — |
| FC2 官方 embed | `https://adult.contents.fc2.com/embed/<纯数字>` | 免费预览；完整片需 FC2 コンテンツマーケット购买 |

注意：这些流站静态 HTML 常无 `<video>` 标签（JS 懒加载）；要拿时长/确认可播放时，用 browser_exec 打开页面滚动或点播放后读 `video.duration`。

**步骤 C：返回视频时长 + 区分预览/完整版（用户硬性要求）**
- 必须给出 **视频时长**；只找到预览片段时明确标注「预览」并附可得的时长。
- 打不开链接不要直接丢弃：检查该页标题、播放器加载后是否跳转到其他作品的预览页（embed 可能载入别的片）；用页面 title 里的番号/标题与目标核对身份一致后才交付。

**步骤 D：同作品旧号**。FC2 PPV 常换号重上架，同一作品可能有旧号。把日文独特短语搜出的 **全部命中** 都记下来；若发现旧号（如 `FC2-PPV-{旧id}` 与 `{新id}` 为同作品），旧号的在线页、搜索结果乃至磁力链一并返回，并注明新旧号关系。

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

- 不要伪造 magnet hash。
- 不要在未获用户确认时调用下载器开始下载。
- 二次元不要只查一个站就结束（至少两端交叉）。
- 三次元不要跳过 JavDB 直接只搜 sukebei；JavDB 优先走 javdb-cli，CLI 不可用再降级网页（须在输出注明）。
- FC2 号在 JavDB+sukebei 都搜不到、且官网显示「找不到商品」（下架）时**别过早下结论**：先用日文原标题/女优名在 OneJAV 交叉一次；该系列可能换号重上架，可在输出里提示用户。
- 不要把 JavDB 当 FC2 官网；官网对比仍归番号 skill。
- 不要在二次元搜图闭环里自动搜磁（Router 默认禁止）；用户明确要磁力除外。
- 不要为翻页循环 `new_tab`；读完当前页用 `goto_url` 或关掉。
- 官方预览型（FC2 PPV / moodyz·dmm 等官方付费源，流站最终都跳 FC2 官方 embed）不要再跑在线视频/磁力搜索；这些站点只在核对最终结果时做预览图/图片对比。
