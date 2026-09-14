---
name: ACG reverse image search
description: 用户丢来图片、截图或说「搜图」「以图搜源」且没有可用标题/番号时使用。太碎或一行职员条先读字网页搜（搜声优表），不要硬传搜图；整屏片尾可文字+以图两边做。二次元：onegai → soutubot → Lens → Yandex → SauceNAO → trace.moe → ascii2d。Lens 喂 encoded_image。
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

1. 确认图片可用：本地路径、`https://` URL，或已落盘附件。
2. **先扫用户文字**：已有番名/番号/TM 标题 → **停止**，回去做网页检索。
3. 只给文字没有图：说明本 skill 需要图，改走文字搜索。
4. **先看图本身**：太碎、或删掉字以后没辨识度 → **停止搜图**，走「读字 → 关键词网页搜」。

## 第 0 步前：太碎 / 纯字图 → 文字检索优先

像素数字是实操启发式，不是硬阈值。以图引擎吃的是视觉指纹（脸、立绘、分镜、道具），不是职员表字体。

**「小」怎么判**

| 级别 | 大致尺寸 | 怎么走 |
|------|----------|--------|
| **太碎** | 最短边 < ~100px，或高度只有几十～一百多的细横条（例：约 340×80、数 KB 的一行职员条） | **不要搜图**。读字 → 网页搜 |
| **偏小** | 最短边 ~100–300px | 有清楚脸/立绘/分镜可以试搜图；仍是裁切字条则走文字 |
| **够用** | 最短边 ≥ ~400px，或整屏 720p/1080p | 正常搜图 |

不要单靠文件 KB：压过的整帧也可以只有几十 KB，角色清楚就仍搜图。KB 很小 **加上** 细横条，才是信息量不足的旁证。

**「纯字图」看结构，不看底色是不是蓝**

删掉字以后画面几乎没辨识度 → 以文字为主：

- 没脸、没立绘、没场景道具、没独特构图
- 大面积均匀/弱纹理底（纯色、虚化、星点蓝底也算）
- 信息几乎全在字上（角色名、声优、台词、标题）

**职员表 / 声优条**

- 裁成一行（「角色名　声优名」这种）→ 读字，搜 **声优/角色/职员表**（`{声优} 声优`、`{角色} {声优} 动画`）。字体/翻译和整屏片尾对不上，SauceNAO/Lens 容易被背景噪声带偏，**不要硬传**。
- 同一句在 **整屏 1080p 片尾** 里 → 文字定锤 + 可以顺便以图碰运气。

流程（太碎，或删字后没辨识度，且不是整屏片尾）：

1. 用已附带的视觉描述或 `vision_analyze` **把字读全**。原文优先（日/英/中都保留，不要先翻译再搜）。
2. 关键词：声优名、角色名、完整台词、作品名、独特短语。丢掉「下一集」「字幕组」「请勿转载」。
3. **`web_search` / `web_lookup`**。职员条优先搜声优表，不是搜图。
4. 命中作品/集数/出处 → **不要再开搜图引擎**。
5. 字太泛（「おはよう」「谢谢」）且画面有清楚角色/场景 → 走下面的搜图主链。
6. 又碎又读不出独特字、也没有可搜视觉 → 说明无法定位，**不要空跑 Lens**。

## 浏览器卫生

1. 引擎页能 URL 上传就用 `?url=` / `uploadbyurl`，避免文件选择框。
2. `browser_exec`：**一次** `new_tab`，之后 `goto_url`。读完结果立刻 `goto_url` 下一引擎或关掉当前 Target。禁止翻页循环 `new_tab`。
3. 同时最多 3 个标签。
4. **不要**点击/填写 Lens 页里的 Google AI / Gemini /「询问这张图片」输入框。MCP 操作不了，会空转。

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

1. **Google Lens** — `https://lens.google.com/`（**必做**。只收视觉匹配 / Exact matches，不做页内 AI；上传失败记失败继续下一引擎）。
2. **Yandex Images** — `https://yandex.com/images/`（**必做**。对直播帧、网页截图最对口：能反搜到视频缩略图、Telegram/Telegraph 镜像、微博水印源站）。操作：点 "Image search" 相机按钮 → 页面出现 `input[type=file]` → CDP `DOM.setFileInputFiles` 喂本地文件；结果重点看 **sites** tab（`.CbirNavigation-TabsItem` className 含 sites）里的来源域名/页面链接，比 similar 图列表更有用。

非 AV 三次元只跑 Lens + Yandex 两个引擎，不碰 whos.tv / iqdb / avscan.cc（都是 AV 向搜图站）。Lens、Yandex 都要跑完再下结论：即使 Lens 已命中也要补 Yandex（反之亦然），两者索引面不同（Lens 偏通用视觉，Yandex 偏网页/视频源）。

### AV 三次元

1. **iqdb** — `https://www.iqdb.org/`
2. **avscan.cc** — `https://www.avscan.cc/`（JAV 番号反搜：截图直接出番号，索引 4万+ 片 / 1.6亿帧；有水印先 Lama 去水印再搜。命中番号 → 交 [JAV bangou lookup FC2](jav-bangou-lookup-fc2) 核对）
3. **Google Lens** — `https://lens.google.com/`（只视觉匹配）
4. **Yandex Images** — `https://yandex.com/images/`
5. **whos.tv** — `https://www.whos.tv/`（最后；低置信不要覆盖已有标题结论）

全空 → AI 鉴定，交回 Router。不要在本 skill 里搜磁。

补充：xslist 认人；avscan.cc 命中或已有番号 → 交 [JAV bangou lookup FC2](jav-bangou-lookup-fc2) 核对。

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

## 输出格式

1. **画面类型**
2. **结论**（无则「未确定」）
3. **证据**（按调用顺序；若走了读字幕/网页搜，先写读到的字和检索词，并注明未搜图）
4. **候选**（最多 3–5）
5. **引擎最高置信结果**：必做引擎逐个列出最佳命中（Lens / Yandex），各附相似度或来源 URL；并分析命中是否同源——同一视频缩略图、Telegram/Telegraph 镜像、原帖水印 vs 转载，区分「原始发布」与「转载」
6. **AI 鉴定**（仅全空时）

## 不要做的事

- 不要用户已经给了 TM 标题/番号还先跑本链。
- 不要把一行职员条/太碎纯字图丢给 SauceNAO 或 Lens；先读字搜声优表或台词。整屏片尾除外（可两边做）。
- 不要把文件喂给 Lens 页上第一个 `input[type=file]`；不要在「已添加 N 张图片」时点首页「搜索」。
- 不要操作 Lens 页内 Google AI。
- 不要循环开新标签。
- 不要对三次元主跑 SauceNAO/trace.moe；whos.tv 是 AV 向搜图站，只对 AV 三次元用，二次元和非 AV 三次元都不用。
- 非 AV 的三次元图不要去 iqdb / avscan.cc / whos.tv（都是 JAV/AV 反搜站）。
- Lens、Yandex 两个必做引擎只跑一个就下结论——都要出结果，各报最高置信命中再比较。
- 不要编造 id；不要自动下种子。
- 搜图命中「官方预览型」（FC2 官方 embed 页 `adult.contents.fc2.com/embed/<纯数字>`、moodyz.com / video.dmm.co.jp/av/ 等官方付费页）时，不再继续做在线视频 / 磁力链搜索；这些站点仅在**核对最终结果时**用于预览/图片对比（身份核验：番号、标题是否一致）。
