---
name: patreon-free-content-sites
version: 1
when_to_use: "用户要找 Patreon(或 Fanbox/Gumroad/SubscribeStar 等平台)的免费资源、免登录看付费帖、Kemono 不全时找替代站时使用。"
description: "Patreon 白嫖/Kemono 不全：Free Tier→镜像→Pawchive→Coomer。"
---
# Patreon 免费资源站检索

用户要「白嫖」Patreon / Fanbox 等付费平台内容时的固定站点顺序。**归档站全靠会员主动上传，所以「不全」是常态——有活跃订阅时 importer 自传永远比等别人传全。**

## 第 0 步：先走官方免费渠道（最干净）

1. **Free Tier**：创作者主页 → Become a member → 选 $0 档，注册后直接看该档帖子。很多作者留了免费档。
2. **Public Posts**：单帖设 Public 的无需登录，`patreon.com/@creator/posts/...` 直开；在帖子列表找无锁图标的。
3. **Explore 页**：`https://www.patreon.com/explore` 可按 Free 筛创作者，适合挖新目标。
4. 作者自己的 Discord/Twitter/X 常放 free preview / 限时公开帖——搜 `作者名 + free/preview` 经常有货。

## 第 1 步：第三方归档站（固定顺序）

| 序 | 站点 | 说明 |
|---|------|------|
| 1 | **Kemono** | kemono.party / `kemono-party.com` / kemono.su / kemono.cr，同一站多镜像/换壳。哪个打不开或图裂了换下一个域名试。按创作者名 + 平台 + 标签索引，覆盖 Patreon/Pixiv Fanbox/Fantia/Gumroad/SubscribeStar/Boosty。 |
| 2 | **Pawchive**（`pawchive.pw`） | 「新 Kemono」：原版源码重建、UI 几乎一样。支持 Patreon + Fanbox importer；有体积上限（按收藏数分档约 100MB/1GB/5GB），免费帖只存文字。**Kemono 缺的优先来这里找。** |
| 3 | **Coomer**（`coomer.su`） | 老牌聚合，偏图片 + 下载链接风格，索引多平台。 |
| 4 | **Moxxy** | 2026-07 起的统一站：Kemono+Coomer+Pawchive 整合成单一搜索引擎（Patreon/OF/Fansly/Candfans/Gumroad/Fantia/Boosty…）。封闭 Alpha、Monero 赞助开发中，方向是「一站搜全平台」，可用但注意未 GA。 |

**检索动作**：直接按创作者名搜（先 Kemono → 缺了 Pawchive → 再 Coomer），不要一次只查一个站就下结论。

## 第 2 步：有活跃订阅时——importer 自传

Kemono / Pawchive 都提供 importer（登录自己的订阅账号把帖子导进去）。这是覆盖最全的路子：

1. 用有订阅的账号跑 importer；Pawchive 只存付费档文件、免费帖只留文字/链接。
2. Pawchive 显示灰图 = 下载失败或超体积上限，可在创作者页留言请求作者解除该创作者的上限。
3. 各站账号不互通（Kemono 登录 ≠ Pawchive），需要分别建号/导入。

## 第 3 步：长期跟踪 / 批量抓取工具

- **splitbrain/patreon-rss**（GitHub）：给创作者生成 RSS。Public 文字帖有全文，付费帖只有标题——适合盯更新节奏，别指望拿正文。
- **RSS-Bridge PatreonBridge**：自建桥接公开帖子源。
- **浏览器扩展**：Readeon（免费开源，连载网文向，装完直接读、不用登录）；patreon-helper / Patreon Downloader（浏览时自动抓媒体文件批量下载）。配合 Free Tier 或借号最好用。

## 第 4 步：盯站况动态

- **r/kemonopiracy**（注意拼写，不是 r/kemono_piracy）：专门跟踪 Kemono.su / kemono.cr / Pawchive / Coomer 换域名、挂掉、新站的版块。站点又挂了/换了壳先去这里问。
- Kemono 系站经常整体宕机或图床裂开（「能进但下载不了」是典型症状），别在单站上死磕，直接切下一镜像/下一站。

## 输出约定

1. **走了哪条路**：官方 Free Tier/Public、归档站名、importer、RSS/扩展，各一行。
2. **命中情况**：哪个站的哪些内容找到了；没找到的创作者点名列出。
3. **总状态**一行，例如 `Kemono 缺 → Pawchive importer 自传补齐 → Coomer 补视频`。

## 不要做的事

- 不要在 Kemono 一个镜像裂图时就宣布「没有」；先换域名（kemono.su / kemono.cr），再切 Pawchive/Coomer。
- 不要拿 RSS 工具当正文来源——付费帖只有标题。
- 不要替用户登录归档站 importer（要密码/2FA 时走 vault 流程或让用户在可见窗口里完成）。
- 不要把 Moxxy 等未 GA 的站当成唯一可靠源；关键内容以 Kemono/Pawchive/Coomer 为准。
