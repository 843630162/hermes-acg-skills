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

- 裁成一行（「女奴隷　土屋李央」这种）→ 读字，搜 **声优/角色/职员表**（`土屋李央 声优`、`女奴隷 土屋李央 动画`）。字体/翻译和整屏片尾对不上，SauceNAO/Lens 容易被背景噪声带偏，**不要硬传**。
- 同一句在 **整屏 1080p 片尾** 里 → 文字定锤 + 可以顺便以图碰运气。

流程（太碎，或删字后没辨识度，且不是整屏片尾）：

1. 用已附带的视觉描述或 `vision_analyze` **把字读全**。原文优先（日/英/中都保留，不要先翻译再搜）。
2. 关键词：声优名、角色名、完整台词、作品名、独特短语。丢掉「下一集」「字幕组」「请勿转载」。
3. **`web_search` / `web_lookup`**。职员条优先搜声优表，不是搜图。
4. 命中作品/集数/出处 → **不要再开搜图引擎**。
5. 字太泛（「おはよう」「谢谢」）且画面有清楚角色/场景 → 走下面的搜图主链。
6. 又碎又读不出独特字、也没有可搜视觉 → 说明无法定位，**不要空跑 Lens**。

## 第 0 步：先跑 HTTP 探针，浏览器只做兜底

`scripts/soutu_http_probe.py`（纯标准库、零依赖）把五个源做成免浏览器调用，**动手前先跑它**：

```bash
cd <HERMES_HOME>/skills/acg-reverse-image-search
python scripts/soutu_http_probe.py yandex   --image <图> --top-k 6        # yandex.ru 直传，免 key，~5s
python scripts/soutu_http_probe.py soutubot --image <图> --factor 1.2
python scripts/soutu_http_probe.py saucenao --image <图> --dbmask 0 --api-key <key>
python scripts/soutu_http_probe.py ascii2d  --image <图> --bovw
python scripts/soutu_http_probe.py safebooru --tags "cat_ears 1girl"
python scripts/soutu_http_probe.py auto     --image <图> --json           # yandex+soutubot[+saucenao]
python scripts/soutu_http_probe.py --self-test                            # 离线自检，改脚本先跑
```

- 协议、阈值、掩码、坑点全在 `references/reverse-search-http-protocols.md`。
- 撞 CF（403 `Just a moment`）→ 先按 [turnstile-bypass](../web/turnstile-bypass/SKILL.md) 拿 jar，再 `--cookie-jar jar.txt --ua "<解挑战时的 UA>"`；UA/出口必须一致，否则依旧 403。
- 只有这两种情况才开浏览器：① 站点要登录态；② 需要页内 AI / 顶部「Image appears to contain」标签 / js 渲染结果（Lens、谷歌 AI 模式、Yandex 自动标签）。

## 维护：吸收外部实现（别人的插件 / 开源客户端）

用户丢来一个搜图插件或客户端让你「看看有没有值得借鉴的」时，按这条走，别读 README 就下结论。**先交报告、等点头再动手**：报告分三段——值得借鉴（每条附「省了哪一步」）、我们现有更强/不能照搬的部分、建议改哪里——这类「看看/评估」默认是要报告，不是直接改库：

1. **直接拉 `core/` 源码**（`raw.githubusercontent.com/<repo>/main/core/<x>_client.py`），从实现里抠四样硬事实：端点与必填参数、multipart 字段名、置信阈值/位掩码、标题与链接的回退链。README 只当索引——实测必填的 `prg=1` / `request={"blocks":[...]}` / `metadata_mode` 这类参数它常不写，抄漏了就是整条源空结果。
2. **改写成 stdlib 脚本落在 `scripts/`**，解析函数做成纯函数 + fixture 自检（`--self-test`），再逐源真机跑一遍。
3. **只有真跑通的源才写进 SKILL.md 正文**；403/需 cookie 的源写成「需 cf_clearance / 未验通」，不能因为「协议照抄对了」就当成可用能力。
4. 结论按「省了什么」写：免图床直传、免浏览器解析、结果分选去噪、配额/错误的语义不对称。说不出省了哪一步，就不值得加进链路。
5. **脚本与文档必须同源**：改脚本先 `--self-test` 再单源真机各跑一次；SKILL/reference 里关于它的每条声明（参数名、默认值、请求头、失败时机）都实跑核过。冲突时先判断谁对——文档写的是更合理行为（日本站发 `Accept-Language: ja`、没 key 在取图前就退出）就**改代码**，否则改文档。实现坑清单见 `references/reverse-search-http-protocols.md` §8。

## 浏览器卫生

1. 引擎页能 URL 上传就用 `?url=` / `uploadbyurl`，避免文件选择框。**Yandex 已不必先传图床**：`scripts/soutu_http_probe.py yandex` 直接 multipart 上传（见「第 0 步」）。只有要把公网直链喂给**只收 URL** 的引擎（Lens `/uploadbyurl`、Yandex 页面 `?rpt=imageview&url=` 兜底）时才传 uguu.se：`curl -F "files[]=@/abs/path.png" https://uguu.se/upload` → JSON 取 `files[0].url`（形如 `https://n.uguu.se/xxx.png`），然后 `goto_url("https://yandex.com/images/search?rpt=imageview&url=<直链URL编码>")`，全程无文件选择框。uguu.se 免账号、几百KB 秒传；catbox.moe 要 uploader 账号（回 "Invalid uploader"）、pixeldrain 大图会 413——别在这两个上浪费时间。
2. **只**用 `browser_exec` 开浏览器。禁止 `terminal` 里 `Start-Process`/`msedge`/`chrome`、禁止 `--remote-debugging-port`、禁止 `export BU_CDP_WS`（传不到 `browser_exec`）。禁止杀用户正在用的 Edge/日常 Chrome。禁止 `hermes config set browser.use_real_profile true`（日常浏览器开着时会锁配置，复制失败或一直超时）。`browser_exec` 报 IPC timeout / "daemon may still be working" 时禁止原样重试、禁止再开第二个浏览器，停下来让用户完全重启 Hermes。Chromium missing 是安装/缓存问题，让用户完全重启 Hermes，不要去拷正在用的 Edge 配置。Google 登录只在 Hermes 拉起的**本机 Google Chrome**（`<HERMES_HOME>/chrome-profile`）里做，不要用 Playwright Chrome for Testing，也不要拷日常 Edge。人机验证时停下来让用户在该窗口里登录，不要解 captcha。
3. `browser_exec`：**一次** `new_tab(url)`，立刻 `print(page_info())`，**不要**再 `wait_for_load()`（会在 `about:blank` 或 Google 上无限等）。若 URL 仍是 `about:blank`，马上 `goto_url(同一 url)`。之后一律 `goto_url`。读完结果立刻 `goto_url` 下一引擎或关掉当前 Target。禁止翻页循环 `new_tab`。
4. 同时最多 3 个标签。**agent Chrome 实例（带 `--user-data-dir=<HERMES_HOME>/chrome-profile`）全机同时最多 3 个**（主代理+子代理合计）：开浏览器前先数一下现有 agent 实例，超过就先协调/停掉再开。锁住或卡死时先用父进程链查占用方是主代理还是哪个子代理，多沟通再处理；绝不杀用户日常 Chrome（不带 user-data-dir 参数的那个）。报 `Chrome exited early (exit code: 0) without writing DevToolsActivePort` 时是 profile 被别的 agent 实例占着：列一遍带该 `--user-data-dir` 的 chrome 进程和它们的父 `agent-browser-*.exe`，**父进程已经消失的孤儿 daemon** 就是占用方，杀掉这个孤儿 daemon 连同它的 chrome 树即可恢复（杀完确认 chrome 进程数为 0 再重试浏览器）；父进程还活着的是在岗会话，不要杀。
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

1. **onegai.moe** — `https://onegai.moe/`（浏览器；CF 边缘）
2. **soutubot.moe** — 本子 / 同人。**优先 `soutu_http_probe.py soutubot`**：schema 2.2，`factor` 1.4→置信阈值 35 / 1.2→45，`path_segments` 非空才算命中，标题优先 `japanese_or_alias`（日文原名，避免全出英文译名）。撞 CF 就按 turnstile-bypass 跑一次 `human_click.py --cookie-out jar.txt`（2026-11-01 实测点一次即过、jar 可用），再 `--cookie-jar jar.txt --ua "<Camoufox UA>"`。
3. **Google Lens** — `https://lens.google.com/`（**只收视觉匹配 / Exact matches**；不做页内 AI）
4. **Yandex Images** — **`soutu_http_probe.py yandex` 优先**（`yandex.ru` 直传 + `data-state` 解析，免 key，约 5s）。脚本已按「图库/官方/画师=high、Pinterest 全系=low」排序并按域去重；结果里没有 high 来源时会明说「只是相似图」，不会把转载图当出处。**但分级只按域名**：噪声图实测也能命中 `wikipedia` 的相似图页并判 high，所以 high 只代表优先看，定锤仍要开页核对或比对缩略图。要看顶部「Image appears to contain」自动标签时才开浏览器。
5. **SauceNAO** — `soutu_http_probe.py saucenao`：`dbmask=0` = 全库且**省略该参数**（别发 `0`）；`96` = pixiv + pixiv 历史库（历史库多为已删/老作，结果里容易混进老图，不是"搜不到新图"）；Twitter 索引 **2019-12 起停更**。没配 key 时脚本在取图前就退出、不读盘不发请求。
6. **trace.moe** — `https://trace.moe/`
7. **ascii2d** — `soutu_http_probe.py ascii2d`（加 `--bovw` 走特征检索，治裁剪/旋转/调色；不加走 `/color/` 色彩检索）。**注意 2026-11-01 实测：挑战能解、cf_clearance 能拿，但 `POST /search/file` 仍被 CF WAF 拦 403 `Attention Required!`（urllib + 页内 fetch 都一样）**——搜索只能浏览器里手动上传，或换日本住宅 IP，别在自动化这条路上反复试。

全空 → **AI 生成鉴定**。二次元不要因此搜磁力。

补充：角色名用 AnimeTrace；水印先 Lama 再从第 1 步重跑。不要 TinEye / Copyseeker。

---

## 三次元搜图（严格按序）

不要把 SauceNAO/trace.moe 当三次元主链。先分流：**AV**（用户说女优 / 番号 / JAV / 实拍，或画面疑似 JAV 截图）走 AV 链；**非 AV**（cosplay、直播/录屏帧、写真、普通真人图）走非 AV 链，**不进任何 AV 站**。

X 上搬运的付费 coser 套图片段（无名字、别名一堆、卖家裁剪加水印）：走 `references/coser-identity-attribution.md`——fxtwitter 媒体 id 对比定同源 → 整帧 + 裁脸双路反搜 → 泄露站按角色枚举全部 cosplayer 专辑 → dHash 排序 → CN 别名表（同一人多个号）。

### 非 AV 三次元（cosplay / 直播 / 写真 / 普通实拍）

1. **谷歌搜图 AI 模式**（见下文专节「谷歌搜图 AI 模式（三次元首选）」；被拒绝则跳过，不重试）。
2. **Google Lens** — `https://lens.google.com/`（**必做**。只收视觉匹配 / Exact matches，不做页内 AI；上传失败记失败继续下一引擎）。
3. **Yandex Images** — `https://yandex.com/images/`（**必做**。对直播帧、网页截图最对口：能反搜到视频缩略图、Telegram/Telegraph 镜像、微博水印源站）。操作：**首选 `soutu_http_probe.py yandex --image <图>`**（`yandex.ru` 直传 + `cbirSites` 解析 + 来源分级，约 5s，见「第 0 步」）；要在页面上看「Image appears to contain」自动标签或 similar 网格时才开浏览器，走 `?rpt=imageview&url=<uguu.se 直链>`（本地图托管方法见「浏览器卫生」第1条，全程无文件框），兜底才点 "Image search" 相机按钮 → CDP `DOM.setFileInputFiles`。结果重点看 **sites** tab（`.CbirNavigation-TabsItem` className 含 sites）里的来源域名/页面链接，比 similar 图列表更有用。**Yandex 顶部自动标签（人名/作品名/题材词）是很强的身份交叉核验信号**——直接和候选演员表/标题对得上即可定锤。

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

### 二次元单页/本子出处：Lens 网页结果 → 求物帖 → 作者 X 回复

新角色/新作（上线几天内）的单页漫画**基本进不了以图索引**——onegai / SauceNAO / iqdb / Yandex / 百度识图全空是常态，全空不等于找不到。**Lens 的 `/search?...&udm=26` 结果页除「完全匹配」，下面还有「网页搜索结果」块**，常直接命中「这张 XXX 有出处吗？」的求物帖，比继续跑剩下的引擎高效：

1. Lens 上传后先读整页文本（`js("document.body.innerText")`）。出现求物帖链接就停下，直接 curl 帖子，别再开下一个引擎。
2. **南+ South Plus（`bbs.spring-plus.net`）是中文二次元求物的高产地**：免登录简版 `https://bbs.spring-plus.net/simple/index.php?t<tid>.html` 直接 curl 可读；答复常在发帖后几十分钟内出现，**下结论前重取一次**（同一帖可能刚从「顶一下」变成答案）。
3. 帖子图用 `grep -oP 'data-original-src="[^"]+"'` 取真实地址，**先比对尺寸/内容**——求物帖问的可能是同一本子的另一页（如 371×750 竖版 vs 用户 2048×899 横版裁切），尺寸不同不代表线索无效，但采信答案前要确认是同一作品。
4. 拿到作者 handle 后去 X 核实，**必须读回复串**：`twitter tweet "<原推URL>" --json` 的 `data` 里除主推还带回复，中文翻译版/补页常由他人在回复里贴出（关键词「中国語翻訳版」「中文」「translation」）。只看作者 timeline 会漏掉用户手上那张翻译版。
5. 定锤后再判形态：作者 Pixiv/时间线只有这一张 = **单页短篇**；要确认是不是成册本子，查作者 DLsite 社团页与 Fanbox。新角色刚出时多半还没成册，**不要向用户承诺「多页本子」**，直接说明是 1P 及作者是否在筹备。

## 本子单格截图溯源：soutubot 定名 → 页级模板匹配定页（实测最快）

单格/裁切的本子截图，Lens/Yandex/iqdb/SauceNAO 常全空（页级图未进索引）。**soutubot.moe 才是本子专用主链**，但它对数据中心出口是硬 CF 墙——浏览器里怎么点都过不去时，走下面这条纯命令行链：

1. **解 CF 拿 cf_clearance**（soutubot 专用，别在浏览器里硬试）：
   `cd <HERMES_HOME>/skills/web/turnstile-bypass && ./.venv/Scripts/python.exe scripts/human_click.py --url "https://soutubot.moe/" --timeout 45 --rounds 3 --cookie-out <HERMES_HOME>/cache/scratch/soutubot_jar.txt`
   输出 `ok: true, cookies: [cf_clearance]` 即成功（humanize 点击一次就过）。**报 `Browser.close: Connection closed while reading from the driver` = 这一轮拿不到 cookie**：同一 URL 最多重试一次，仍崩就换住宅出口或先修 turnstile-bypass，然后把 soutubot 记成「本轮未验通」转去别的源——不要在过挑战这一步无限重试。
2. **命令行调它的 API**（优先脚本，已含全部解析规则）：
   ```bash
   python <HERMES_HOME>/skills/acg-reverse-image-search/scripts/soutu_http_probe.py soutubot \
     --image "<图片绝对路径>" --factor 1.2 \
     --cookie-jar <HERMES_HOME>/cache/scratch/soutubot_jar.txt \
     --ua "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:152.0) Gecko/20100101 Firefox/152.0"
   ```
   裸 curl 等价写法（脚本不在时）：
   ```bash
   UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:152.0) Gecko/20100101 Firefox/152.0"
   curl -s -b soutubot_jar.txt -A "$UA" -H "Accept: application/json" -H "Referer: https://soutubot.moe/" \
     -F "file=@<图片绝对路径>;type=image/jpeg" https://soutubot.moe/api/search -o res.json
   ```
   **UA 必须等于 Camoufox 的 Firefox UA**（cookie 绑 UA+出口 IP）；换 UA 立刻 403。返回 JSON：`results[].score`（百分比×100，≥90 可定名）+ `raw_path`（形如 `/www/nhentai_cn/nh26/[590677][Bannou] Rio wa Shitto Suru .../0031.webp`，车号/标题/页码全在路径里）。`status: partial` 常由某个源库 connect timeout 造成，重发 1–2 次即出高分结果。
3. **API 与 cookie-jar 都失败时的唯一验通路：Camoufox 里走页面表单**。实测 2026-11-05：`--cookie-jar` 复用后 API 仍回 `http=520`、脚本侧 `IncompleteRead(8261 bytes read, 124346 more expected)`，浏览器里点 Turnstile 也没用；改用 turnstile-bypass 的 Camoufox（`hc.SOFTWARE_GL_PREFS` + `humanize=True`）打开站点 → `hc.find_widget`/`hc.human_move`+`hc.human_click` 过挑战 → `page.set_input_files("#file-input", 本地图)` 提交 → 等约 60s 后 URL 变成 `/results/<id>`，`page.inner_text('body')` 里直接带 `32.84%`、`NHentai #609138 Pages 69` 与标题/标签，`a[href]` 里就是 nhentai/e-hentai/18comic 页级直链。别在 API 这条路上反复重试。
   - **SauceNAO 同一个 Camoufox 配方能过墙**：挑战一次即清（title 变 `SauceNAO Reverse Image Search`），`#fileInput` 上传 → 结果页标题 `Sauce Found?` 且正文出现「Low similarity results have been hidden」而 `.SimilarImageList` 为空 = **零命中**（不是失败，别重试）。零命中本身就是「该图不在 Pixiv/booru 索引里」的证据。
4. **定页**：nhentai 走 v2 API `https://nhentai.net/api/v2/galleries/<id>`（旧 `/api/gallery/<id>` 已 403），`pages[].path` + `https://i.nhentai.net/<path>` 拉全页；JM 侧用 jmcomic 下整本。
4. **页级匹配（关键坑）**：模板匹配必须**缩放模板**（`cv2.resize(query, fx=ts)`，ts 0.8–3.2 步长 0.05），**不要按页宽循环缩放整页**——同一格在不同版本页面上占比不同，按页宽扫会在正确页上只报 0.4 的假阴性（实测踩过一整轮）。同一格不同汉化的正常得分：NCC 0.88–0.93 / SSIM 0.6–0.77（文字被换掉会拉低 SSIM，别当不匹配）。
5. **认翻译版本**：同一格的中文版措辞各汉化组不同（例：黎歐「这是怎么了」/ nhentai中文「您感觉如何呢」/ 用户手图「怎麼樣」），**别用文字定版本**；用 bubble 区域分块 SSIM 比哪份最接近，再如实说明可能是第三份汉化。
6. **页码口径**：nhentai 的 `number` 含跨页（1678×1199 这种是双页图），JM 的 `00031.webp` 与 nhentai 页码通常不等——报页码时注明来源与总页数。

## webp / 非标图片格式处理

遇到 `.webp`，或文件声称是图但 `file` 显示 "data"/webp 魔数（CDN 缩略图常见）：**先调一次 `skills_list`，使用 [image-format-conversion](image-format-conversion) skill 转成 jpg/png 再** vision_analyze / 比对——不要直接喂 webp 原图，也不要反复临时试 ffmpeg。转换后仍识别不了（如 XOR 混淆的 CDN 图）就不纠缠，降级到多镜像文字佐证。

## 视频帧（9:16 短视频截图）反搜定位

搜图结果若落到「AI cos 视频 / 竖屏短剧」类 UP 主合集（如 B 站「ai cos」系列），需定位到具体视频+时间点：

1. **B 站取片**：`api.bilibili.com/x/web-interface/view?bvid=` 拿 `cid` → 老接口 `x/player/playurl?bvid=&cid=&qn=16&fnval=1`（wbi 新接口要签名，直接用老接口取 480p durl 分段拼接 mp4）。
2. **全片扫描**：`ffmpeg -vf "fps=1,crop=<9:16中心裁剪>,scale=100:180"` 抽小帧 → PIL 逐帧算颜色指纹（目标物色块占比：如红椅=红色像素、赤膊男=底部肤色、米色墙=低饱和亮色）排序出候选段，比「拼大图给视觉模型认场景」可靠——小格拼图里视觉模型常把天台护栏认成米色墙、把麦田暖光认成肤色。
3. **候选段高清复核**：对候选时间点 `-ss <t>` 抽 400x720 帧逐张 vision 比对用户原图（发型/发夹/工牌/椅子色/挂画逐项对）。
4. 注意：横屏(16:9)合集视频与用户 9:16 帧可能只是同项目横竖版，定锤时注明「同角色同系列，竖版未逐一比对」，不要硬断同一文件。

## X 传播 AI 短视频（真人风 AI / deepfake）溯源

画面是真人风 AI 短视频（X 多账号传播、卖家裁剪加水印、非真 JAV）时：

1. **avscan / iqdb 只作参考**：AI 片 top 分普遍 70–72%，top5 候选缩略图几乎都不同场景——不要定锤候选番号、不要拉磁力，转 Lens 完全匹配主线。
2. **Lens 完全匹配是主线**：`https://lens.google.com/uploadbyurl?url=<uguu 直链>&safe=off`，sleep 8s 后点「完全匹配」tab。结果卡缩略图是 base64 内嵌（img src / background-image 提取都空）→ 按锚点 `innerText.length>=10` + `href` 提取文本与链接即可：常命中原帖（x.com status）、官方账号、司机社/whos.tv 求出处帖、bad.news 镜像帖——**论坛帖的评论区常直接给出系列名/账号**。
3. **多账号同 amplify_video 定原帖**：多个账号发同一个 `amplify_video/<videoId>` 时，按雪花 ID 时差取最早（视频上传一般早于原帖几十秒内）为原帖；bad.news 是 X 帖镜像（`bad.news/t/<数字id>`），直接 curl 可拿帖文与 `video.twimg.com` 原片直链（960x720 原版 mp4 + m3u8）。
4. **AI 生成快速核验**：`ffprobe` 音频采样率 = 96kHz（常见视频 44.1/48k）+ faster-whisper small 跑 ja/zh/en 全部幻觉输出（低语/呻吟、无有效语音）→ 可定锤 AI 生成/deepfake。whisper 环境：`uv run --python 3.12 --with faster-whisper`（av 版本冲突 → `wave`+`numpy` 手动解 16-bit PCM；`vad_filter=False` + `beam_size=1`）。
5. **FANZA 同人 AI 包溯源**：hitomi-dojin.com 是 SEO 联盟站（条目页 = 封面 og:image `d_<cid>pl.jpg` + 10 张免费样本图，**无 raw 下载**）；FANZA 官网 `www.dmm.co.jp/dc/doujin` 封数据中心 IP（跳 special.fanza.jp/not-available-in-your-region）→ 用 hitomi-dojin 的封面/样本 + FANZA cid 定来源。无磁力、仅数字下载（单条 ~20 日元、50 本装 ~1.67GB）。
6. **定具体哪一卷**：封面人物与目标帧 vision 对比（齐刘海/脸型/痣），放大核验痣的相对位置（相对眼/鼻/颧骨）；样本图是 2x2 四帧拼接图，命中即确认该卷；封面图 curl 不通时用浏览器 in-page `fetch` + btoa 批量取。
7. **卖家漏斗**：X 卖帖 → TG 私频道（`t.me/s/<name>` 私频道只有信息页+订阅数，无公开预览）→ 淘宝水印（「完整原片搜淘宝 @xxx」）。合集磁力不存在时，TG 频道按编号查看就是此类 AI 合集唯一的「类磁力」分发渠道，如实告知用户。

## X 上的实拍短视频片段溯源（漫展实拍 / 无水印片段）

用户丢一条 X 视频推问「出处」时，文字侧先跑完再跑图——图往往是最后才有效的一环：

1. **取原片与元数据**：`twitter tweet "<推URL>" --json` 的 `media[].url` 就是 `video.twimg.com/amplify_video/...mp4` 直链，带代理 curl 下来 `ffprobe` 记时长/分辨率。同一 `amplify_video/<videoId>` 出现在多个账号时按雪花 ID 取最早那条。
2. **读回复串定传播网**：同一 JSON 的 `data` 里除主推还带全部回复。回复里的 @mention 与「保存视频」类 bot 调用就是同一素材的传播节点，顺藤摸出矩阵号与它们的 TG 枢纽频道；`t.me/s/<频道>` 取不到任何消息 = 作者关了公开预览，如实说明而不是当频道不存在。
3. **文案唯一性测试（判原创还是转抄）**：把推文文案切成 2–3 个独特短语做精确短语检索（`twitter search "<短语>" --max 60 -t top` + `web_search`）。全网只有这一条 → 该推就是最早节点，别再找「上游原帖」；出现多条同文案 → 按日期取最早那条才是上游。
4. **抽帧 + 水印普查**：`ffmpeg -vf "fps=1,scale=360:-1,tile=4x4"` 出 16 格拼图，另抽 0.5/3/6/12s 单帧；`vision_analyze` 要求逐字抄出所有水印/编号/平台 ID/账号名（含角落小字、镜面/瓷砖/马桶盖上的字），没有文字必须明说「无文字」。无水印 = 只剩以图 + 文字侧证据，先告诉用户这一点。
5. **Yandex 无浏览器预检（省一轮浏览器）**：先 `python <HERMES_HOME>/skills/acg-reverse-image-search/scripts/soutu_http_probe.py yandex --image <帧>`——命中就白拿来源，0 条再走文字/论坛证据线，不必开浏览器。只有必须走 URL 方式时才传 uguu 拿直链，再 `curl -sL --proxy <代理> -A "<UA>" "https://yandex.com/images/search?rws=0&url=<直链URL编码>"`，在 HTML 里查 `No images for this search`，或正文只剩 "Smart Camera / Move the frames to select the search area" 页脚 = 空结果。
6. **引擎被 NSFW 判定拒答 = 空结果，不是命中**：Lens 结果页可能只回「Polite refusal」，或给一段与来源无关的 AI 描述（把撕贴膜/拉丝认成皮肤病灶）且零条链接。同一帧不要重试，换帧或换引擎一次即可。
7. **Bing 以图：GET 不算跑过，且登录也救不了它**（实测 2026-11-05 两次，前后对比）：
   - 未登录时相机面板存在（`#sb_sbiinfbtn` → `#sb_imgpst`「粘贴图像链接」输入框），但提交后被强制跳到 `login.live.com/oauth20_authorize.srf`。
   - **用户手动登录之后，已登录变体里相机控件根本不进 DOM**（`sb_sbiinfbtn`/`sb_sbiinfb`/`sb_sbiact`/`sb_imgpst` 全 null），反而没有以图入口。登录态本身能验通：`account.live.com/proofs/manage` 直接渲染「其他安全选项」，`#id_p` 头像带出 `storage.live.com/users/0x…/profilephoto`。
   - 三条 GET 直连全部退化：`q=imgurl:<url>` 页里 `murl`/`iusc` 为 0（无图结果）；`/visualsearch?q=<url>` 302 到 `explore.microsoft.com/.../bing/visual-search/` 营销页；`view=detailv2&iss=SBI&form=SBIVSP&q=…` 302 到无关关键词图搜页。
   - **结论：ACG 溯源把 Bing 当不可用**，不要为了它保留登录或写进证据表。

## 浏览器登录态：怎么确认、怎么导出复用

用户在 agent 真 Chrome 里手动登录后（profile 固定 `<HERMES_HOME>/chrome-profile`，持久）：

- **写盘证据**：`Default/Network/Cookies` 的 mtime 变了、里面出现 `.MSA.Auth` / `__Host-MSAAUTHP` / `MSPAuth` / `MSPProf` / `WLSSC` / `SDIDC`，过期时间 2026-12～2027-11 → 跨会话、跨 Hermes 重启都能复用，不用重登。
- **登录是否生效的验法**（别靠猜）：浏览器开 `account.live.com/proofs/manage` → 出「其他安全选项」= 已登录；出登录表单 = 未登录。
- **导出 cookie jar 的正确路径是 CDP，不是拷文件**：Chrome 运行时 `Default/Network/Cookies` 被独占锁，`cp` 报 `Device or resource busy`、`Copy-Item` 报「正由另一进程使用」。用 `cdp("Network.getCookies", urls=[...])` 取值，自己拼 Netscape 格式写文件（`domain\tTRUE(domain以.开头)\tpath\tsecure\texpiry\tname\tvalue`）。
- **curl 侧只能半继承**：带导出的 jar 请求 `account.live.com/proofs/manage` 会落到 `login.live.com/login.srf` 的「继续」短页（2 KB），不带 cookie 则是完整「Sign in to your Microsoft account」（33 KB）——会话确实带过去了，但 Microsoft 登录还需要 JS/指纹，纯 curl 不能完整继承登录态。**要登录态就留在浏览器路径里做。**

## 核实「疑似某 X 漫画作者」

反搜/Lens/Onegai 指向某个 X 漫画账号时：**先调一次 `skills_list`，使用本 skill 的 `references/x-manga-author-verification.md`**（twicomi 作者页批量拿标题+日期+推文 ID → 用题材词筛标题 → fxtwitter 取原推图 vision 比对，全程命令行、不开浏览器）。要点：标题表里没有题材关键词就直接排除该作者；画风像但分镜不同只能写「同风格作者」，不能当出处。
8. **百度识图不要手搓参数**：`graph.baidu.com/upload` 纯 multipart POST 回 `{"status":1002,"msg":"Params illegal"}`（新版要 sign/token 签名），`pcpage` 入口直接 400。需要百度就走浏览器上传流程，一次不通即放弃。
9. **收口**：引擎全空 + 文案全网唯一 + 题材是已知付费私源系列（漫展厕拍/走光这类只在 TG 私频道与付费论坛流通）→ 结论写「公开搜索引擎无索引，属私源/付费素材」，并给可执行的下一步（买论坛帖核对 / 在求出处版发帖 / 进 TG 频道）。不要把跑空的一串引擎写成「推荐方法」。

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

## 反搜全空时先查「太新」，再查平台站内（实测 2026-11-05/06 踩过一次误判）

**索引滞后是天，不是小时**：一张 Pixiv 新作（实测 2026-11-04 00:06 发布）在 24h 内 SauceNAO / onegai / soutubot / Lens / Yandex / IQDB **全部零命中**，但它是真实发布的作品。所以「全引擎空」的第一解释必须是**太新**，不是「AI 生成」、不是「无出处」。

- 先问/先看图的**新旧线索**：用户说「比较新」、图里有平台水印、或元数据只剩 `jfif_*` 而无 EXIF → 直接进平台站内检索，不要停在「找不到」。
- **Pixiv 角色标签翻页**（用户给出的方法，但要注意它只在**网页端**可靠）：网页端真实端点（从 Pixiv 页 `performance.getEntriesByType('resource')` 抓到的调用，自己猜的 `/search/illust?word=…` 会 404）：`https://www.pixiv.net/ajax/search/artworks/<标签>?order=date_d&mode=all&p=1&ai_type=0&csw=0&s_mode=s_tag_full&ratio=&lang=zh`，结果在 `body.illustManga.data`（每页 60 条，另有 `total`/`lastPage`），**id 字段叫 `id`，不是 `illustId`**（写成 `illustId` 全是 undefined，很容易误判成「搜不到」）。App API 的 `search_illust` 会**漏掉**这类作品：实测该作品打了 `十六夜咲夜` 标签，按 `date_desc` 扫到 1200 条（覆盖 11-05→08-17）仍没有它；换 `search_ai_type=0/1`、加 `start_date/end_date` 窗口（27 条）也没有；同一作者的其它作品在 `博麗霊夢`、`極上の女体` 标签前 300 条里也全都不出现 → **R-18 和 AI 都不是原因**（登录态下用网页端端点实测：同一标签新着排序第 1 页 60 条里 xRestrict=1 呌 9 条、illustType=2 有 4 条，R-18/AI 作品照常进搜索）。真正原因是**作者/作品级别的「不在 Pixiv 搜索和排行榜中显示」设置**，与新旧、R-18、AI 无关——网页端也一样搜不到（实测新着排序 p=1..8，覆盖 11-05→10-05，目标不在其中）。
- **绕开搜索的办法（真正可靠的一条）**：拿到作者后走 `user_illusts(uid)`（实测一次返回该作者最近 30 张，全都在），或直接用用户给的 id 取 detail。配方在 `pixiv-image-download`（`<HERMES_HOME>/tools/pixiv-cli/pixiv.py`）。
- **验源要像素级**：下载候选原图（Pixiv 原图要 App UA + Referer）后与用户图算 `ImageChops.difference` 的 mean abs diff；实测同一张图（用户 jpg vs `img-original` png）= **2.64/255**，尺寸 832×1216 完全一致。差值 <5 就是同一张；几十以上只是相似。**这比 vision 模型说「构图相似」可靠。**

## 末步：AI 生成鉴定（仅全链未找到来源）

已有高置信来源时不要做。

1. 搜图空白 ≠ 一定是 AI。
2. 列出画面异常（若有）：多余手指、文字扭曲、饰品熔接、皮肤过滑等。
3. 输出：很可能 AI / 很可能实拍或手绘 / 无法判断 + 依据。禁止 100% 断言。
4. **两条硬旁证**（实测 2026-11-05，一张东方咲夜/芙兰朵露两格漫画，832×892、EXIF/XMP 全空、无任何署名水印）：
   - soutubot 全库最高分只有 **32.8%**，而那个最高分对象自己带 `ai generated` 标签（nhentai 609138「Changli - Wuthering Waves [AI Generated]」），其余 48 条 <28%。索引里最近的邻居都是 AI 图集 → 强烈支持 AI 生成。
   - 把气泡区 3× 放大逐字检查汉字笔画：出现缺笔/部件错位/不成字（「您不舒服吗」整串崩坏）→ 文字是**生成在图里**的，不是人工嵌字。注意同一张图不同区域可能给出相反结论（另一格文字完全规范），单区域结论不足以定锤，至少核两处再判。
5. **元数据与尺寸只是旁证**：`PIL` 读 `im.info`/`getexif()`，只剩 `jfif_*` 而 EXIF/XMP 全空 = 被平台重压缩或本就是生成图（实测那张 Pixiv 图就是这样，仍无法靠它定 AI）；尺寸不是扫描页常见值也只说明不像扫描。**不要拿这两条当结论依据。**
6. **平台官方标记比画风可靠**：Pixiv 的 `illust_ai_type`（`illust_detail` 字段，App API 可取）——对照组实测：手描き作品 151720445 / 151726154 = **1**，本案例 151654632 = **2**（AI）。所以「反搜全空 + 文字崩坏」只能算旁证，**能取到 `illust_ai_type=2` 才算定锤**；取不到就写「疑似 AI，未证实」。
7. **误判存档（教训）**：同一张图（东方 咲夜+芙兰朵露 两格）当时按「全引擎零命中 + 无水印 + 手部/文字崩坏 + soutubot 最近邻是 AI 图集」判成「AI 生成、找不到出处」。前半对（Pixiv 官方 AI 标记），后半错——它其实是 `pixiv.net/artworks/151654632`，作者 **sanane**（uid 115693601），2026-11-04 00:06 JST 发布，R-18，标签 `東方Project / 十六夜咲夜 / フランドール・スカーレット / ふたなり`。**结论纪律：「找不到出处」只能写「当前工具链没找到」，不能写成「没有出处」。**
6. **分格线穿出图边 = 用户图是从更大页裁出来的**：面板边框线一直延伸到图像左右边缘而未在画面内收束、气泡轮廓在边缘被截断未闭合 → 原页比这张图更大。这时不要在裁切图上找「原页」，先告诉用户需要未裁切的原图（含页边/署名）才能定作者。

---

## 执行方式

1. 确认没有可先用的文字线索。
2. 太碎或纯字横条 → 读字 → 网页搜（职员条搜声优表）；不要开搜图引擎。整屏片尾可以文字 + 以图两边做。
3. 分类后只跑对应主链。**每个引擎先试 `scripts/soutu_http_probe.py <源>`（HTTP 版），失败/撞墙再开浏览器**——省时间也省 agent Chrome（全机上限 3 个）。
4. 至少前 2 个引擎（除非第 1 个已高置信）。二次元前 2 个 = onegai.moe + soutubot.moe。
5. 低相似度说「低置信」，不要假确定。
6. vision_analyze 用 `region` 裁剪前，**必须先拿到图片真实尺寸**（`file <path>` 或 PIL 的 im.size），再按实际像素算裁剪框；不要凭视觉印象猜坐标——实测曾因不知道图是 1920×1280 而连裁两次黑边浪费两轮。
7. **缩略图对比优先（所有带预览的反搜引擎通用）**：反搜结果自带候选帧/封面 URL 时（avscan 的 frames[].thumbnail_url、JavDB 的 cover_url/preview_images、Lens/Yandex 结果页图片），**先直接 vision_analyze 这些返回的缩略图与用户原图对比**（发型/制服/场景/表情任一明显不符 → 该候选置信度进一步降低；top 分 <85% 或与第二名差 ≤2 分时定锤前必须核验）。核验通过后才值得拉该候选的 detail / 磁力链——不要先拉磁力再验证。此规则对 avscan.cc、JavDB、Google Lens、Yandex 等一切带预览图的搜图站同等适用；若 CDN 图片格式非标（ffmpeg/PIL 都识别不了）导致核验失败，不纠缠，降级到多镜像文字佐证。

## 输出格式

1. **画面类型**
2. **结论**（无则「未确定」）
3. **证据**（按调用顺序；若走了读字幕/网页搜，先写读到的字和检索词，并注明未搜图）**跑过的每一个以图引擎都要逐条列出结果状态：命中 / 空结果 / 被 NSFW 拒答 / 未跑通**。用户会直接追问「你有没有搜过图」，只列命中不列空跑等于没交代。
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
- 二次元新作单页搜图引擎全空就报「找不到」——先看 Lens 结果页的「网页搜索结果」块有没有求物帖，再下结论。
- 遇到 webp / 非标格式图片直接喂 vision 或反复试 ffmpeg——先调 skills_list 加载 image-format-conversion 转换后再处理。
- whos.tv 用手敲密码登录（应走 browser_vault），或同一张图反复上传浪费积分。
- 以图引擎全空时把「试过 Lens/Yandex/Bing/百度」的失败清单包装成方法推荐——如实写「都空，属私源未索引」，再给可执行的下一步。
- 没做文案唯一性测试就断言「这条是转抄的 / 上游还有原帖」。
