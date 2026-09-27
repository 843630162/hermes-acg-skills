---
name: iwara-search
description: Use when 用户要在 iwara 搜/收集视频图片、给收藏找新候选或问规则搜索。走 api.iwara.tv。
---

# Iwara 内容发现与收集

用户会在 iwara 维护收藏 playlist（常是影奸/NTR/silhouette 向 MMD 视频），任务形态：拉全量 playlist → 用规则搜索找新候选 → diff 去重 → 交付带链接清单。

## 核心端点（全部无需 cookie，curl/python 直连）

1. **媒体规则搜索**（真正的"规则搜索"，完整索引、可分页）：
   `GET https://api.iwara.tv/search?type=videos&query=<urlencoded>&page=N&limit=32`
   - `type` 可为 `videos` / `images`；响应 `{count, limit, page, results[]}`，results 含 id、title、user.username、numViews/numLikes、tags[{id}]。
   - **运算符语法**（官方 Search Operators 公告）：`{tags: [silhouette]}`、`{author: mmd-bug}`、`{title_zh: 影奸}`、`{body_ja: 影姦}`、`{rating: r18}`。多个 `{...}` 块用空格 AND，如 `{tags:[ntr]} {tags:[dance_and_sex]}`。query 整体 URL-encode。
   - 常用组合：`{tags: [silhouette]}`（影奸 silhouette）、`{tags: [ntr]} {tags: [dance_and_sex]}`、`{author: X}`（按作者流全量拉取）。
2. **论坛**（找社区技巧/作者推荐时）：
   `GET https://api.iwara.tv/forum/threads?limit=50&page=N` 可拉全部 ~1.2 万帖元数据。**无服务端 query 参数**——全量抓 title 存本地，再按关键词过滤。帖子详情 `/forum/threads/{id}`，正文在响应的 `results[]` 字段（不是 posts）。
3. **Playlist**：`GET https://api.iwara.tv/playlist/{uuid}?page=N&limit=32`，从 URL 里取 uuid；逐页拉完按 id 去重得唯一视频集。

## Pitfalls

- **别用 `api.iwara.tv/videos?tags[]=x` 或 `?query=` 做规则搜索**：那是小二级索引，count 恒为个位数（~4），会误判"没什么结果"。完整索引只有 `/search?type=videos&query={operators}`。
- **别硬刚 `www.iwara.tv/search/videos` 网页**：被 Cloudflare managed challenge（"Just a moment"）卡死，无复选框可点；api.iwara.tv 不受影响。浏览器 fetch 跨 origin 也会 Failed to fetch——直接 curl/python 走 API。
- 必须过网页 CF 墙时（如抓页面级数据）：先查出口 IP（数据中心 egress 吃 hard challenge，住宅线常直过），仍撞再调 `skills_list` 用 [turnstile-bypass](../web/turnstile-bypass/SKILL.md) 的 human_click.py 导出 cf_clearance；cookie 绑定同一 UA + 同一出口 IP。
- **论坛没有服务端搜索**：`?query=`/`?q=`/`?search=` 参数全被忽略（count 不变）。抓全量 title 本地 grep 是唯一可靠路。
- **分页终止条件**：以 `len(collected) >= count` 或空 results 为准，不要固定页数；大结果集（如 `{author: x}` 近千条）逐页 sleep ~0.25s 防限流。

## 工作流

1. 拉用户 playlist 全量 → 唯一 id 集合 + 统计高频 tags/作者。
2. 以高频影奸向作者（如 mmd-bug、buttercrab）的 `{author: X}` 流 + silhouette/ntr+dance/netorare 标签组合，逐组跑 `/search?type=videos`。
3. 与 playlist id diff 出"新候选"；按 tag 相关度 + views/likes 打分排序。
4. 交付 markdown 清单：分组（作者流 / 标签流），每条 = 标题、@作者、日期、views/likes、直链 `https://www.iwara.tv/video/{id}`。全量排序数据另存 JSON 供深挖。
5. 用户问"怎么搜更多"时，先去论坛全量帖 + 官方公告（Search Operators）找依据，再给方法说明——管理回复里说的规则搜索就是运算符语法。
