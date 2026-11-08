# 网盘档（云盘档）清点配方 — Getchu/DLsite 同人動画

适用：已确认作品来源（Getchu/DLsite/FANTIA 同人作者），用户接着问「有没有网盘档」。

## 先判作者态度
商品页正文里的 `NO UPLOAD / NO P2P / NO mediafire etc.` 是关键信号：作者禁止上传/放流时，
公开磁力与网盘档基本不存在，检索只做「确认不存在」而不是「多试几个站」。

## 有效检索渠道（按性价比排序，实测）
1. `868888.net` hex 搜索：`/search/<关键词hex>-1-id-s.html`，对日文标题、番号（如 `TSAK-028`）都可用。
2. `sukebei.nyaa.si`：只有 `?q=<关键词>&f=0&c=0_0` 是搜索（2026-11-07 实测 200）。`?query=` 被忽略 → 回首页最新列表（实测 ~134KB / 75 行无关条目）；`?rss=1&q=` 也被忽略（~45KB HTML / 0 `<item>`）；RSS 只有 `?page=rss&q=` 可用（~20KB / 有命中即 19 items）。**这两种错误参数回的都是「看着正常的页面」，解析出 0 条就会误判「无资源」**。下结论前先跑对照词 `MIDE-599`（应 19 行 / ~45KB），或直接跑 `<HERMES_HOME>/skills/acg-magnet-torrent-search/scripts/sukebei_search.py`（自带对照 + 回显校验 + gzip 解压）。命中后的磁力要进 `/view/<id>` 页取（带 dn/tr），列表页只能拿到 hash。
3. 中文搜索引擎：Sogou（`www.sogou.com/web?query=`，走 10808 代理可通，结果正则 `<h3 class="vr-title">` + `/link?url=`）、Yahoo（`search.yahoo.com/search?p=`，正文关键词计数比解析链接可靠）、Bing（浏览器 `#b_results .b_algo`；生僻词直接回「没有与此相关的结果」，这是有效的否定证据）。Baidu 常回「百度安全验证」，Yandex 常回 smart-captcha，两者基本不可用作中文资源检索。
5. 中文 ACG 资源站 search 端点：`?s=`（WordPress 类）或 `search.php?searchsubmit=yes&srchtxt=`（Discuz 类）。多个站（gentlefield/kivimoe/acg1999/missb/ciyuanjiev/catcloud）DNS 直接不解析或 403，别在此耗时间。
5b. **VikACG（vikacg.com）**：SPA 站，直取首页/`?s=` 都是 403。真实入口是浏览器里 `https://www.vikacg.com/search?s=<kw>`（内部调 `api/vikacg/v1/comprehensiveSearch`），结果区出现 `没有相关搜索结果哦~` 就是零命中；用 `goto_url` + 读 `main.innerText` 判定，别用 curl。它的 `/api/vikacg/v1/*` 带客户端签名校验，直接 fetch 回 `400 非法的客户端，请下载官方版本`；`/mcp` 是页面内 webmcp 而非服务端 MCP，curl 不通。
5. 同人動画搬运博客（`avplay.net`、`avsake.com`、`xasiat.com`）：能命中作品全文简介，但**不是网盘**——它们靠 SubyShare/BunFile 会员制或 VIP 在线观看，正文里没有 网盘/提取码 行。判断「有没有网盘」时看正文有无 `网盘/115/夸克/百度/迅雷/pikpak/提取码` 关键词。

## 已知陷阱
- 求档帖里的 GoFile/网盘链接多半已失效：gofile 分享页会渲染成 `This content does not exist`（闲置后被删）。用浏览器打开后读 `performance.getEntriesByType('resource')` 可直接看到 `api.gofile.io/contents/<id>?...` 调用与页面文案，比猜 wt/token 快。
- `archiveofsins.com/t/search/text/<kw>` 连真实浏览器都吃 Cloudflare 挑战（curl 403）；只有直接 thread URL 偶尔可取。
- 中文论坛（老王 / a41415 / 4k2 / sjs96）对这类 2022–2023 小众同人動画通常零命中，但**必须单独查司机社（xsijishe.net）**：它对访客 403/搜索需登录，正确姿势是浏览器 + Google `site:xsijishe.net <作品名>`（Google 能索引到 thread），再直开 `thread-<tid>-1-1.html` 读帖。求出处帖往往在回复里就贴了磁力。
- 番号类线索（如 `TSAK-###`）来自搬运站标签，不是官方编号，别当 JavDB 番号查。

## 交付口径
找不到就直说「公开侧没有网盘档」，并列证据表（查过哪些渠道、各自结果），再给可行动作：官方 DL（Getchu/FANTIA/XCREAM）、会员制网盘（SubyShare/BunFile）、实体 DVD（駿河屋）、或去求档板块发帖。别把「某站有该作品的 VIP 播放页」说成「有网盘档」。
