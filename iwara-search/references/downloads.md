# 下载与完整版线索（2026-10 实测）

- **按作者拉全部视频**：`/profile/{username}` → user.id → `/videos?user={uuid}&page=N&limit=32`。作者全是 premium/private 时 `/search?type=users` 搜不到，但这条能列全。
- **CDN URL 两跳**：video API 的 file.url 是 filesq manifest（JSON），直接 curl 得到的是 JSON 不是 MP4；需解析 manifest 取实际文件 URL 再下。
- **匿名下载最高档实测**：`*.iwara.tv/view?hash=…&filename=<uuid>_540.mp4`（540p/360p）；用户自己浏览器里可读 DOM video.currentSrc 或网络请求捕获拿实际 URL。
- **赞助版线索在 body 字段**：常写「赞助获取 2k 完整版」+ Unifans/Fansky/Patreon/Fantia 直链；预览片尾几秒会提示完整版时长。用户要「找完整版」时先读全部 body，再去对应平台/流出站（见 patreon-free-content-sites skill 的 Unifans/VikaCG 节）。
