# 社交帖 → 来源与店铺溯源（X / Bluesky 截图）

适用：用户丢 X/Twitter/Bluesky 帖子截图或文字（发帖人预告新 Live2D 模型、新作品、新资源），要定位原帖、确认发帖人身份、查店铺（VGen / BOOTH 等）上架状态。快路径纪律：先答「帖子说的啥 + 原帖链接 + 发帖人」，再追店铺/领取渠道。

## 1. 定位原帖

1. web_search 并行两条：`"发帖人 handle"`（带引号）+「handle + 主题关键词」。首条命中通常就是 x.com 原帖链接（含 `/video/1` 后缀变体）。
2. X 原帖免登录直接拿：
   ```bash
   curl -s "https://api.fxtwitter.com/{screen_name}/status/{id}"
   ```
   JSON 里可直接用的字段：
   - `tweet.text` / `raw_text`（含 t.co 原始链接）；`created_at`（核时间线）
   - `replies` / `retweets` / `likes` / `views`（判断是否出圈、转述可信度）
   - `author.name` / `description` / `website.url`——**website 字段常就是发帖人的店铺或主页（VGen / BOOTH / 个人站），是下一步最强线索**
   - `media.all[]`：`url` 为直链（video.twimg.com / pbs.twimg.com，curl 可直下）；`thumbnail_url` 海报帧；`duration` / `width` / `height`
   - X 页面本身是 SPA，curl 只拿得到壳 → 走 fxtwitter，不要开浏览器
3. Bluesky 截图：同帖文案与 X 跨帖一致，直接把截图里的文字当 X 文案检索。
4. bsky 公共 API（`public.api.bsky.app/xrpc/app.bsky.actor.getProfile`、`atproto.identity.resolveHandle`）对普通 handle 会报 `Invalid AT identifier` / `MethodNotImplemented`——不要反复试 handle 变体（裸 handle、全 handle 都试过），转 X 侧（fxtwitter）。

## 2. VGen 店铺核查（Live2D 模型）

- 艺术家主页：`https://vgen.co/{USERNAME}`（大写账号名；发帖人 X bio/website 通常直接指到这里，优先从 fxtwitter 的 `author.website` 拿，不要猜）。
- curl 带浏览器 UA 即可，不开浏览器。页面是 Next.js SPA，数据在 `__NEXT_DATA__` script 里：
  - script 标签带额外属性（`crossorigin="anonymous"` 等），严格正则 `id="__NEXT_DATA__" type="application/json">` 匹配不上——用 `html.index('__NEXT_DATA__')` 定位后取其后第一个 `>` 到 `</script>` 之间的 JSON。
  - `props.pageProps.user`：`displayName` / `username` / `created`（店铺开设日期，判断是不是新开的店）/ `languages` / `moderation.discoveryStatus` / `socials[]`（每项 `{name, link}`，含 Twitter / bilibili / 个人站等）/ `announcement`。
  - `props.pageProps.products[]`：`productName`、`basePrice`（0 = 免费）、`currency`、`status`（PUBLISHED = 已上架）、`created`、`details`（授权条款段落，JSON 字符串）、`messageToCustomers`。
- 判定：帖子里预告的关键词没有对应 product → 报「**尚未上架**」+ 帖子承诺的发布窗口，不要写「未找到」；授权条款（是否可再分发/商用/直播）以 `details` 原文为准。

## 3. BOOTH（booth.pm）

- 搜索 URL 只有这个形状有效：`https://booth.pm/en/search/products?keyword={kw}`（200，HTML）；`https://booth.pm/en/search?keyword=` 与 `https://booth.pm/search?keyword=` 均 404（「お探しのページが見つかりませんでした」页）。200 搜索页的条目提取未验证，按页面文本列条目。
- 店铺 / 用户页形状：`booth.pm/en/shops/{id}`、`booth.pm/en/users/{id}`，id 从搜索页找。

## 4. 转载视频帖 → coser 出处（X 转帖 cos 短视频）

适用：用户丢来的 cos 短视频帖出自搬运/卖图号，问「视频出处是谁」。主工具是 reverse-image-search skill（抽帧→Yandex/Lens→身份核对），本节补转帖特有的纪律：

- 识别搬运号：bio 是约拍/卖图链接、正文全是泛化标签（巨乳/露出/cos）——这类帖用文案关键词搜不到原发，身份必须走搜图链。
- **时间轴校验**：fxtwitter 各拉主推与候选原帖的 `created_at`，候选必须早于转帖才可能是源；coser 公开 X 帖晚于转帖时，源大概率是其付费渠道（微博付费合集 / Fantia / Patreon）。
- leak 聚合站（cosplayboobs / ocosplay / miaitu / quhuage 等）命中同角色+同配色的专辑只是「相似」不是身份证据；要下载候选 coser 本人照片做全分辨率并排逐项核对（发饰、垂布、腰封、纱、choker 这些款式级元素）。
- **镜像图内水印是最短路径**：裁图片底部 ~15% 放大 2× 读字，得到微博 @CN名 + t.me 搬运频道；再用聚合站档案页（92cos.com/creator/…、kanmeiba 标签页）拿 CN名 → 微博/X/抖音 跨平台链接一览，别一个个猜 handle。
- 微博付费合集（V+）里的自拍短视频通常全网无索引（telegra.ph 镜像只有照片）：回答落到 coser + 套装（角色/造型）+ 付费平台即可；「未能定位视频本体的精确原始 URL」是合法结论，不要继续重试搜图引擎。

## 5. X 视频切片 → 付费页出处（myfans / 裏垢系素人流出）

适用：用户丢一条 X 视频帖（多是搬运号/梗号发的几秒预览切片），问「出处是谁 / 有没有番号 / 有没有磁力」。

1. **先读回复串，再动搜图。** `twitter tweet "<URL>" --json` 的 `data` 含该帖的回复与引用；求出处时源链接通常由他人在回复里贴出（「ふる↓」「ソース」「full」这类标记），发帖人紧接着回 👍 / 感谢回复 = 发帖人确认该链接，可作定锤证据。这一步比反搜图便宜且更准，先做。
2. **回复里的源链接常是「跳转页」而非目标页**：WordPress 短链（`loknote77.com/171-2/` 这类）正文里嵌着一整段被 `<br />` 转义的 HTML，真目标只出现在其中的 `window.location.href = "https://…"`。`curl -sL` 不跟 JS 跳转、`curl -sI` 也看不出来——必须 grep 页面里的 `window.location` / `og:` / `setTimeout` 取真链接。页面显示「(タイトルなし)」不等于没内容。
3. **目标站是 Next.js SPA（myfans 等）时不要开浏览器**：GET 帖子页，从 `__NEXT_DATA__` 的 `props.pageProps.metadata` 取 `og_title` / `og_description`（完整标题、作者名、`kind`、`published_at`）与 `og_image_url`；或直接 GET `https://<host>/_next/data/<buildId>/<locale>/posts/<postId>.json`（buildId 抄自同一份页面 HTML），返回同一份 JSON。`/api/…` 猜测路径通常只回 SPA 壳，不要据此判定「没有接口」。
4. **规格与作者档案走第三方站**（游客可见、curl 直读）：`fans-log.jp/creator/<handle>/<postId>/` 给正片时长、单品价、浏览量、排名；`fans-log.jp/creator/<handle>/` 列全部投稿标题与作者 bio 原文（含「已删除的编号」清单）；`myxeromovie.com/creator/<id>/` 给作者介绍、套餐价格、官方 SNS 链接。用它核对「时长 / 价格 / 是否同一作者」。
5. **视觉核对用并排图**：推文抽帧与目标站 og 封面 hstack 并排交 vision 判读。`hstack` 要求两输入同高——先各自 `scale=-2:400` 再拼，否则报 `Input 1 height … does not match`。付费站封面多是刻意模糊的遮罩图，仍能比对**场景级特征**（背景帘布/床品的花纹、发色发型、是否裸身），吻合即可佐证；别因为它模糊就跳过这一步。
6. **结论形态**：myfans / 裏垢系「合法素人ハメ撮り」类**没有 JAV 番号**，唯一编号是作者自定的 `Page.NN`（不是番号，别写成番号）；磁力通常也没有——按 ③ 链路各查一次（`javdb search <标题词>`、sukebei、`laowang search`）全空即定「无番号、无磁力、仅站内串流（单品价 / 月费套餐）」，不要反复换关键词重试。交付 = 作者页链接 + 具体投稿页链接 + 正片时长与价格 + 明确的「无番号/无磁力」结论。
7. **搬运号的「新闻卡」不是证据**：同一素材常被包成新闻截图（标题、姓名、年龄、剧情、「退学处分」等）作引流。这些姓名与剧情按「该搬运号的说法」引用并注明未能独立核实，不要当作已确认的出处信息。
