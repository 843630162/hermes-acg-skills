---
name: ACG reverse image search
description: 用户丢来图片、截图或说「搜图」「以图搜源」且没有可用标题/番号时使用。二次元顺序：onegai.moe → soutubot.moe → Google Lens → Yandex → SauceNAO → trace.moe → ascii2d；三次元非 AV 必做 Lens + Yandex（不进 AV 站），AV 走 iqdb/avscan.cc。有用户文字时先网页检索。Lens 只看视觉匹配，不要操作页内 Google AI。
---
# ACG 反向搜图

当用户提供图片且 **没有** 足够文字线索（标题 / 番号 / 卖家 / 明确站点+分集）时使用。目标：定位插画/番剧来源，或三次元作品/女优线索。

**有标题或番号时不要进本 skill 当第一步。** 交给 [ACG resource search router](acg-resource-search-router) 的网页检索。本 skill 是补漏。

## 安全

- 仅处理用户主动提供的图；不主动爬取他人私密图。
- 结果里区分「官方/作者源」与「镜像/转载站」，优先标作者与作品名。

## 输入

1. 确认图片可用：本地路径、`https://` URL，或已落盘附件。
2. **先扫用户文字**：已有番名/番号/TM 标题 → **停止**，回去做网页检索。
3. 只给文字没有图：说明本 skill 需要图，改走文字搜索。

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

入口 `https://lens.google.com/`。

1. 上传图片，等结果页。
2. 优先 **完全匹配 / Exact matches**，再看相似图标题里的作品名/番号。
3. 账号错误（图片未与账号关联）或 MCP 无法上传：记失败，进入下一引擎，**不要重试 Gemini 聊天框**。
4. 视觉匹配已经高置信 → 结束 Lens。没有匹配也结束 Lens，不要滚去「问 Google AI」。

---

## 末步：AI 生成鉴定（仅全链未找到来源）

已有高置信来源时不要做。

1. 搜图空白 ≠ 一定是 AI。
2. 列出画面异常（若有）：多余手指、文字扭曲、饰品熔接、皮肤过滑等。
3. 输出：很可能 AI / 很可能实拍或手绘 / 无法判断 + 依据。禁止 100% 断言。

---

## 执行方式

1. 确认没有可先用的文字线索。
2. 分类后只跑对应主链。
3. 至少前 2 个引擎（除非第 1 个已高置信）。二次元前 2 个 = onegai.moe + soutubot.moe。
4. 低相似度说「低置信」，不要假确定。

## 输出格式

1. **画面类型**
2. **结论**（无则「未确定」）
3. **证据**（按调用顺序）
4. **候选**（最多 3–5）
5. **引擎最高置信结果**：必做引擎逐个列出最佳命中（Lens / Yandex），各附相似度或来源 URL；并分析命中是否同源——同一视频缩略图、Telegram/Telegraph 镜像、原帖水印 vs 转载，区分「原始发布」与「转载」
6. **AI 鉴定**（仅全空时）

## 不要做的事

- 不要用户已经给了 TM 标题/番号还先跑本链。
- 不要操作 Lens 页内 Google AI。
- 不要循环开新标签。
- 不要对三次元主跑 SauceNAO/trace.moe；whos.tv 是 AV 向搜图站，只对 AV 三次元用，二次元和非 AV 三次元都不用。
- 非 AV 的三次元图不要去 iqdb / avscan.cc / whos.tv（都是 JAV/AV 反搜站）。
- Lens、Yandex 两个必做引擎只跑一个就下结论——都要出结果，各报最高置信命中再比较。
- 不要编造 id；不要自动下种子。
