---
name: ACG reverse image search
description: 用户丢来图片、截图或说「搜图」「以图搜源」且没有可用标题/番号时使用。太碎或一行职员条先读字网页搜（搜声优表），不要硬传搜图；整屏片尾可文字+以图两边做。二次元：onegai → soutubot → Lens → Yandex → SauceNAO → trace.moe → ascii2d。Lens 喂 encoded_image。三次元先试谷歌搜图 AI 模式，拒绝则回退原链。
---
# ACG 反向搜图

当用户提供图片且 **没有** 足够文字线索（标题 / 番号 / 卖家 / 明确站点+分集）时使用。目标：定位插画/番剧来源，或三次元作品/女优线索。

**有标题或番号时不要进本 skill 当第一步。** 交给 [ACG resource search router](acg-resource-search-router) 的网页检索。本 skill 是补漏。

**一行职员条 / 太碎纯字图不要进搜图主链。** 读字 → 当关键词网页搜（见下方「第 0 步前」）。整屏片尾可以文字定锤、以图碰运气两边做。

## 安全

- 仅处理用户主动提供的图；不主动爬取他人私密图。
- 结果里区分「官方/作者源」与「镜像/转载站」，优先标作者与作品名。

## 免责声明

本 skill **仅供学习与技术参考**。不提供、不保证任何来源或资源的合法性；使用者须自行遵守所在地法律与站点条款。疑似未成年内容必须拒绝。

## 输入

1. 确认图片可用：本回合的 `@file:` / `@image:` / `image_url`，或桌面附件目录 `%APPDATA%\Hermes\composer-images` 里**刚刚写入**的文件。禁止用 `<WORK_DIR>`、Downloads、Pictures 里「最近改过的图」当附件——那会把昨天的 `09142233.png` 当成新图。没有本回合路径就先问用户，或只检查 composer-images 里最近几分钟的文件并用 `vision_analyze` 核对。
2. **先扫用户文字**：已有番名/番号/TM 标题 → **停止**，回去做网页检索。
3. 只给文字没有图：说明本 skill 需要图，改走文字搜索。
4. **先看图本身**：太碎、或删掉字以后没辨识度 → **停止搜图**，走「读字 → 关键词网页搜」。

## 第 0 步前：太碎 / 纯字图 → 文字检索优先

像素数字是实操启发式，不是硬阈值。以图引擎吃的是视觉指纹（脸、立绘、分镜、道具），不是职员表字体。

**「小」怎么判**

| 级别 | 大致尺寸 | 怎么走 |
|------|----------|--------|
| **太碎** | 最短边 < ~100px，或高度只有几十～一百多的细横条（例：342×83、约 8KB 的一行职员条） | **不要搜图**。读字 → 网页搜 |
| **偏小** | 最短边 ~100–300px | 有清楚脸/立绘/分镜可以试搜图；仍是裁切字条则走文字 |
| **够用** | 最短边 ≥ ~400px，或整屏 720p/1080p | 正常搜图 |

不要单靠文件 KB：压过的整帧也可以只有几十 KB，角色清楚就仍搜图。KB 很小 **加上** 细横条，才是信息量不足的旁证。

**「纯字图」看结构，不看底色是不是蓝**

删掉字以后画面几乎没辨识度 → 以文字为主：

- 没脸、没立绘、没场景道具、没独特构图
- 大面积均匀/弱纹理底（纯色、虚化、星点蓝底也算）
- 信息几乎全在字上（角色名、声优、台词、标题）

**职员表 / 声优条**

- 裁成一行（「{角色名}　{声优名}」这种）→ 读字，搜 **声优/角色/职员表**（`{声优名} 声优`、`{角色名} {声优名} 动画`）。字体/翻译和整屏片尾对不上，SauceNAO/Lens 容易被背景噪声带偏，**不要硬传**。
- 同一句在 **整屏 1080p 片尾** 里 → 文字定锤 + 可以顺便以图碰运气。

流程（太碎，或删字后没辨识度，且不是整屏片尾）：

1. 用已附带的视觉描述或 `vision_analyze` **把字读全**。原文优先（日/英/中都保留，不要先翻译再搜）。
2. 关键词：声优名、角色名、完整台词、作品名、独特短语。丢掉「下一集」「字幕组」「请勿转载」。
3. **`web_search` / `web_lookup`**。职员条优先搜声优表，不是搜图。
4. 命中作品/集数/出处 → **不要再开搜图引擎**。
5. 字太泛（「おはよう」「谢谢」）且画面有清楚角色/场景 → 走下面的搜图主链。
6. 又碎又读不出独特字、也没有可搜视觉 → 说明无法定位，**不要空跑 Lens**。

## 浏览器卫生

1. 引擎页能 URL 上传就用 `?url=` / `uploadbyurl`，避免文件选择框。**本地图先传 uguu.se 拿直链再喂 Yandex**：`curl -F "files[]=@/abs/path.png" https://uguu.se/upload` → JSON 取 `files[0].url`（形如 `https://n.uguu.se/xxx.png`），然后 `goto_url("https://yandex.com/images/search?rpt=imageview&url=<直链URL编码>")`，全程无文件选择框。uguu.se 免账号、几百KB 秒传；catbox.moe 要 uploader 账号（回 "Invalid uploader"）、pixeldrain 大图会 413——别在这两个上浪费时间。
2. **只**用 `browser_exec` 开浏览器。禁止 `terminal` 里 `Start-Process`/`msedge`/`chrome`、禁止 `--remote-debugging-port`、禁止 `export BU_CDP_WS`（传不到 `browser_exec`）。禁止杀用户正在用的 Edge/日常 Chrome。禁止 `hermes config set browser.use_real_profile true`（日常浏览器开着时会锁配置，复制失败或一直超时）。`browser_exec` 报 IPC timeout / "daemon may still be working" 时禁止原样重试、禁止再开第二个浏览器，停下来让用户完全重启 Hermes。Chromium missing 是安装/缓存问题，让用户完全重启 Hermes，不要去拷正在用的 Edge 配置。Google 登录只在 Hermes 拉起的**本机 Google Chrome**（`<HERMES_HOME>/chrome-profile`）里做，不要用 Playwright Chrome for Testing，也不要拷日常 Edge。人机验证时停下来让用户在该窗口里登录，不要解 captcha。
3. `browser_exec`：**一次** `new_tab(url)`，立刻 `print(page_info())`，**不要**再 `wait_for_load()`（会在 `about:blank` 或 Google 上无限等）。若 URL 仍是 `about:blank`，马上 `goto_url(同一 url)`。之后一律 `goto_url`。读完结果立刻 `goto_url` 下一引擎或关掉当前 Target。禁止翻页循环 `new_tab`。
4. 同时最多 3 个标签。**agent Chrome 实例（带 `--user-data-dir=<HERMES_HOME>/chrome-profile`）全机同时最多 3 个**（主代理+子代理合计）：开浏览器前先数一下现有 agent 实例，超过就先协调/停掉再开。锁住或卡死时先用父进程链查占用方是主代理还是哪个子代理，多沟通再处理；绝不杀用户日常 Chrome（不带 user-data-dir 参数的那个）。
5. **不要**点击/填写 Lens 页里的 Google AI / Gemini /「询问这张图片」输入框。MCP 操作不了，会空转。它指 Lens 结果页内的「问 Google AI」聊天框；搜图结果页顶栏的「AI 模式」是一级 tab，两者不同，可以正常点（见下文专节）。

## CF 墙应对（打开任一引擎前先看这一节）

二次元链 7 个引擎里 onegai / soutubot / SauceNAO / trace.moe / ascii2d、以及三次元的 avscan.cc **全部跑在 Cloudflare 边缘**——平时直连 200，但随时可能收紧成 managed challenge（「请稍候」/ "Just a moment..."）。实测（2026-09）：soutubot.moe 对数据中心出口直接回 403 + Just a moment；whos.tv 同墙。iqdb.org 是 nginx、uguu.se 是 nginx，不走 CF。

**撞墙判定**（任一命中即算撞墙，不要反复刷新同一引擎）：
- HTTP 403 / 503 且 `server: cloudflare`；或页面标题/正文含 "Just a moment"、"请稍候"、"Checking your browser"
- curl 探测一条命令：`curl -sS -m 15 -o /dev/null -w "%{http_code}" https://<engine>/`，再 `grep -i 'cf-ray\|server:'` 看响应头

**处理顺序（按序走，不要跳级）：**
1. **先查出口 IP，别动浏览器引擎**。数据中心 / VPS / 云主机 egress 吃 hard challenge；住宅线或用户本机线路通常直接过。`curl https://api.ipify.org` 看当前出口，注意 v2rayN / singbox TUN 节点是否开着（开着时 curl 也走代理）。用户有翻墙环境：切到住宅节点重试一次即可。
2. **仍撞 → 调 `skills_list` 加载 [turnstile-bypass](../web/turnstile-bypass/SKILL.md)**，用其 `scripts/human_click.py`（skill venv 跑）过挑战并导出 cf_clearance cookie。复用 cookie 三要素绑定：同一 UA + 同一出口 IP + `-b jar.txt`；换节点或换 UA 就 403，TTL ~30 天。
3. **全引擎超时/失败 → 先怀疑 IP 信誉再怀疑浏览器指纹**（turnstile-bypass skill 已验证：soutubot.moe 数据中心 IP 时所有引擎 90-170s 全超时，切住宅线后 curl 直接 200）。不要在同一张图上反复重试被拒的 AI 模式或同一引擎。
4. **该引擎本轮放弃**：记下「X 撞 CF 墙 + 出口 IP 类型」，继续链上下一引擎；输出证据段注明。多个引擎同时撞墙 = 出口问题，回到第 1 步换节点重跑整条链，而不是逐个引擎硬试。

## 第 0 步：二次元还是三次元

| 判定 | 典型特征 |
|------|----------|
| **二次元** | 动漫/插画/厚涂、赛璐璐、漫画分镜、Gal/立绘、里番截图 |
| **三次元** | 真人照片、实拍截图、写真、直播/视频帧 |

- 输出一行：**画面类型：二次元 / 三次元 / 不确定**。
- 不确定：先 2D；前两个引擎都空再 3D。鉴定只在两条都空之后。
- 用户说搜番/P站/本子 → 强制 2D；说女优/番号/实拍 → 强制 3D。

---

## 二次元搜图（严格按序）

前一个已高置信（作者+作品或明确集数）可结束。

1. **onegai.moe** — `https://onegai.moe/`
2. **soutubot.moe** — `https://soutubot.moe/`（本子 / 同人）
3. **Google Lens** — `https://lens.google.com/`（**只收视觉匹配 / Exact matches**；不做页内 AI）
4. **Yandex Images** — `https://yandex.com/images/`
5. **SauceNAO** — `https://saucenao.com/`
6. **trace.moe** — `https://trace.moe/`
7. **ascii2d** — `https://ascii2d.net/`

全空 → **AI 生成鉴定**。二次元不要因此搜磁力。

补充：角色名用 AnimeTrace；水印先 Lama 再从第 1 步重跑。不要 TinEye / Copyseeker。

---

## 三次元搜图（严格按序）

不要把 SauceNAO/trace.moe 当三次元主链。先分流：**AV**（用户说女优 / 番号 / JAV / 实拍，或画面疑似 JAV 截图）走 AV 链；**非 AV**（cosplay、直播/录屏帧、写真、普通真人图）走非 AV 链，**不进任何 AV 站**。

### 非 AV 三次元（cosplay / 直播 / 写真 / 普通实拍）

1. **谷歌搜图 AI 模式**（见下文专节「谷歌搜图 AI 模式（三次元首选）」；被拒绝则跳过，不重试）。
2. **Google Lens** — `https://lens.google.com/`（**必做**。只收视觉匹配 / Exact matches，不做页内 AI；上传失败记失败继续下一引擎）。
3. **Yandex Images** — `https://yandex.com/images/`（**必做**。对直播帧、网页截图最对口：能反搜到视频缩略图、Telegram/Telegraph 镜像、微博水印源站）。操作：**首选** `?rpt=imageview&url=<uguu.se 直链>`（本地图托管方法见「浏览器卫生」第1条，全程无文件框）；兜底才点 "Image search" 相机按钮 → CDP `DOM.setFileInputFiles`。结果重点看 **sites** tab（`.CbirNavigation-TabsItem` className 含 sites）里的来源域名/页面链接，比 similar 图列表更有用。**Yandex 顶部 "Image appears to contain" 自动标签（人名/作品名/题材词）是很强的身份交叉核验信号**——直接和候选演员表/标题对得上即可定锤。

非 AV 三次元先试谷歌搜图 AI 模式（被拒跳过、不重试），再跑 Lens + Yandex 两个必做引擎，不碰 whos.tv / iqdb / avscan.cc（都是 AV 向搜图站）。Lens、Yandex 都要跑完再下结论：即使 Lens 已命中也要补 Yandex（反之亦然），两者索引面不同（Lens 偏通用视觉，Yandex 偏网页/视频源）。

### AV 三次元

0. **谷歌搜图 AI 模式**（可选首步，见下文专节；NSFW 常被拒；被拒直接跳过，不重试）
1. **iqdb** — `https://www.iqdb.org/`
2. **avscan.cc** — `https://www.avscan.cc/`（JAV 番号反搜：截图直接出番号，索引 4万+ 片 / 1.6亿帧；有水印先 Lama 去水印再搜。命中番号 → 交 [JAV bangou lookup FC2](jav-bangou-lookup-fc2) 核对）
3. **Google Lens** — `https://lens.google.com/`（只视觉匹配）
4. **Yandex Images** — `https://yandex.com/images/`
5. **whos.tv** — `https://www.whos.tv/`（最后；低置信不要覆盖已有标题结论）。上传入口盖着登录层：先调 `browser_vault_list` 找 whos.tv 已存登录，没有就 `browser_vault_save_login` 让用户在 UI 里保存、再 `browser_vault_fill` 自动填密码——**不要用 browser_type 手敲密码**。该站**每次上传图片扣积分**：直接扣（用户已授权，不必逐次确认），但不要反复上传同一张/相似图导致积分流失过多；一次失败+换法重传即可。

全空 → AI 鉴定，交回 Router。不要在本 skill 里搜磁。

补充：xslist 认人；avscan.cc 命中或已有番号 → 交 [JAV bangou lookup FC2](jav-bangou-lookup-fc2) 核对。

## 反搜落到论坛/社区帖时（看评论区找番号答案）

引擎结果落在论坛 / 微博 / Threads / X 的帖子（有人拿这张图发帖求番号、晒截图）时，**别只看帖内图片——去读评论区**，常有人直接回答了番号：

1. **Threads 每条回复都是独立帖子 URL**（`threads.com/@user/post/<id>`）：串页被登录墙挡住时，对单条回复 URL `web_extract` 仍能拿完整文本（串页只露前几条）。高赞回复大概率是番号答案；转发帖链回原贴，优先读原串。
2. **X/Twitter**：同理；不登录用 fxtwitter/vxtwitter 抓回复内容。
3. 评论区答案是隐藏/编码形式（叙事文本、房间号/路线数据）→ **先调一次 `skills_list`，使用 [jav-number-decode](jav-number-decode) 解码提取评论里的所有番号**再核对。
4. 评论区得到的番号必须经 JavDB/资料站交叉验证后才能定锤——点赞多不等于对（实测有 AI 片被多人误认成 FC2）。

## webp / 非标图片格式处理

遇到 `.webp`，或文件声称是图但 `file` 显示 "data"/webp 魔数（CDN 缩略图常见）：**先调一次 `skills_list`，使用 [image-format-conversion](image-format-conversion) skill 转成 jpg/png 再** vision_analyze / 比对——不要直接喂 webp 原图，也不要反复临时试 ffmpeg。转换后仍识别不了（如 XOR 混淆的 CDN 图）就不纠缠，降级到多镜像文字佐证。

## 文件输出纪律（Windows）

- curl / 下载 / 托管前的本地临时文件一律放非系统盘：`<HERMES_HOME>/cache/scratch` 最佳；不要写 C: 或 `%TEMP%`。

---

## 谷歌搜图 AI 模式（三次元首选）

非露骨写真类能直接识出人物/作品并给引用链接；NSFW 常被拒，被拒回退本 skill 原链，不要在同一张图上反复试。实测：一张写真偶像照片直接识别出人物并给出 X 官方账号帖子 + 游民星空/Yahoo/鏡週刊新闻引用，全部验证存在。

1. `new_tab("https://images.google.com")` → 点 `[aria-label='按图搜索']`（英文界面是相机图标 / Upload image）→ 页面出现**唯一一个** `input[name=encoded_image]`。
2. CDP 注入：`DOM.querySelector(nodeId=root, selector="input[name=encoded_image]")` 取 nodeId → `DOM.setFileInputFiles(files=[本地路径], nodeId)`。会自动导航到 `google.com/search?vsrid=...&udm=26`（「全部」tab）。
3. 点结果页顶部横栏的「AI 模式」：找 textContent 精确等于 `AI 模式` 的叶子 span，**必须点它的 `<a>` 祖先**（class 含 XVMlrc C6AK7c）；直接点 span/div 不会导航。URL 变成 `udm=50`。等约 8 秒生成。
4. 读回答卡片「AI 模式针对"1 张图片"的回复」：找包含该标题的最小容器，clone 后去掉 script/style，过滤分享/反馈按钮噪声（复制链接 / 导出到 Google 文档 / 响应良好等）。正文通常含人名 + 描述 + 引用链接。
5. 提取引用：卡片内非 google href 的 `a[href]`（X 帖子、新闻站）。用 fxtwitter 或直接打开验证被引用的 X 帖（登录墙下标题/日期仍可见）；人名再用 web_search 交叉核对。
6. NSFW 拒绝信号：AI 回答「不能提供回答或帮助」之类措辞 → 回退本 skill 原有链（非 AV 走 Lens→Yandex；AV 走 iqdb/avscan），不要在同一张图上反复试 AI 模式。

udm 参数：`udm=26` = 「全部」tab，`udm=50` = AI 模式 tab。

---

## Google Lens（仅视觉匹配）

入口 `https://lens.google.com/`。打开后常被重定向到 `https://www.google.com/?olud`（首页 Lens 浮层），这是正常的，不要因此重开标签。

页上有 **多个** `input[type=file]`。**第一个属于首页搜索框**（`#ow16`），喂它只会显示「已添加 N 张图片」，URL 停在 `google.com/?olud`，**不会**跳到结果页。

上传（每次 `setFileInputFiles` 前都要重新 `DOM.getDocument`，旧 nodeId 会静默失败，`files.length` 仍为 0）：

1. 优先 `upload_file("input[name=encoded_image]", abs_path)`，或 `querySelectorAll("input[name=encoded_image]")` 再 `DOM.setFileInputFiles`。这条会导航到 `google.com/search?vsrid=...`。
2. 没有 `encoded_image` 时：`querySelectorAll("input[type=file]")`，**清空**搜索框那些（`files=[]`），把文件设到 Lens 对话框那个：`accept` 含 `image/*`、`multiple=false`、父链直接到 `BODY`。
3. **禁止**只 `querySelector("input[type=file]")` 打第一个。**禁止**在仍停在 `?olud` 时点首页「搜索」按钮。
4. 等最多 ~10s。成功：URL 含 `vsrid=`。失败：「已添加 N 张图片」且仍在 `google.com/?olud` → 换上一步的正确 input 再传一次，不要连点搜索。
5. 账号错误（「图片未找到 / 您用于搜索的图片未与您的账号关联」）：记失败，进下一引擎，**不要重试 Gemini 聊天框**。
6. 优先 **完全匹配 / Exact matches**（中文「完全匹配」），再看相似图标题里的作品名/番号。视觉匹配已经高置信或没有匹配 → 结束 Lens，不要滚去「问 Google AI」。

---

## 末步：AI 生成鉴定（仅全链未找到来源）

已有高置信来源时不要做。

1. 搜图空白 ≠ 一定是 AI。
2. 列出画面异常（若有）：多余手指、文字扭曲、饰品熔接、皮肤过滑等。
3. 输出：很可能 AI / 很可能实拍或手绘 / 无法判断 + 依据。禁止 100% 断言。

---

## 执行方式

1. 确认没有可先用的文字线索。
2. 太碎或纯字横条 → 读字 → 网页搜（职员条搜声优表）；不要开搜图引擎。整屏片尾可以文字 + 以图两边做。
3. 分类后只跑对应主链。
4. 至少前 2 个引擎（除非第 1 个已高置信）。二次元前 2 个 = onegai.moe + soutubot.moe。
5. 低相似度说「低置信」，不要假确定。
6. vision_analyze 用 `region` 裁剪前，**必须先拿到图片真实尺寸**（`file <path>` 或 PIL 的 im.size），再按实际像素算裁剪框；不要凭视觉印象猜坐标——实测曾因不知道图是 1920×1280 而连裁两次黑边浪费两轮。
7. **缩略图对比优先（所有带预览的反搜引擎通用）**：反搜结果自带候选帧/封面 URL 时（avscan 的 frames[].thumbnail_url、JavDB 的 cover_url/preview_images、Lens/Yandex 结果页图片），**先直接 vision_analyze 这些返回的缩略图与用户原图对比**（发型/制服/场景/表情任一明显不符 → 该候选置信度进一步降低；top 分 <85% 或与第二名差 ≤2 分时定锤前必须核验）。核验通过后才值得拉该候选的 detail / 磁力链——不要先拉磁力再验证。此规则对 avscan.cc、JavDB、Google Lens、Yandex 等一切带预览图的搜图站同等适用；若 CDN 图片格式非标（ffmpeg/PIL 都识别不了）导致核验失败，不纠缠，降级到多镜像文字佐证。

## 输出格式

1. **画面类型**
2. **结论**（无则「未确定」）
3. **证据**（按调用顺序；若走了读字幕/网页搜，先写读到的字和检索词，并注明未搜图）
4. **候选**（最多 3–5）
5. **引擎最高置信结果**：必做引擎逐个列出最佳命中（谷歌搜图 AI 模式 / Lens / Yandex，AI 模式被拒则注明拒绝并跳过），各附相似度或来源 URL；并分析命中是否同源——同一视频缩略图、Telegram/Telegraph 镜像、原帖水印 vs 转载，区分「原始发布」与「转载」
6. **AI 鉴定**（仅全空时）

## 不要做的事

- 不要用户已经给了 TM 标题/番号还先跑本链。
- 不要把一行职员条/太碎纯字图丢给 SauceNAO 或 Lens；先读字搜声优表或台词。整屏片尾除外（可两边做）。
- 不要把文件喂给 Lens 页上第一个 `input[type=file]`；不要在「已添加 N 张图片」时点首页「搜索」。
- 不要操作 Lens 页内 Google AI。
- NSFW 被拒后不要反复重试同一张图的 AI 模式；被拒不重试，回退本 skill 原链。
- 不要把搜图 AI 模式当二次元引擎用（2D 链不变）。
- 不要循环开新标签。
- 不要对三次元主跑 SauceNAO/trace.moe；whos.tv 是 AV 向搜图站，只对 AV 三次元用，二次元和非 AV 三次元都不用。
- 非 AV 的三次元图不要去 iqdb / avscan.cc / whos.tv（都是 JAV/AV 反搜站）。
- Lens、Yandex 两个必做引擎只跑一个就下结论——都要出结果，各报最高置信命中再比较。
- 不要编造 id；不要自动下种子。
- 搜图命中「官方预览型」（FC2 官方 embed 页 `adult.contents.fc2.com/embed/<纯数字>`、moodyz.com / video.dmm.co.jp/av/ 等官方付费页）时，不再继续做在线视频 / 磁力链搜索；这些站点仅在**核对最终结果时**用于预览/图片对比（身份核验：番号、标题是否一致）。
- 反搜 top hit 未做视觉核验就立刻拉 detail / 磁力链——先拿引擎返回的缩略图/预览帧与用户原图比对；top <85% 或与第二名差 ≤2 分必须核验后才可定锤。
- vision_analyze region 裁剪不先查图片真实尺寸、凭印象猜坐标。
- 反搜落到论坛/微博/Threads/X 帖子时只读帖内图、不看评论区——评论区常有现成番号答案（Threads 回复是独立 URL，可 web_extract）；隐藏番号先调 skills_list 用 jav-number-decode 解码。
- 遇到 webp / 非标格式图片直接喂 vision 或反复试 ffmpeg——先调 skills_list 加载 image-format-conversion 转换后再处理。
- whos.tv 用手敲密码登录（应走 browser_vault），或同一张图反复上传浪费积分。
