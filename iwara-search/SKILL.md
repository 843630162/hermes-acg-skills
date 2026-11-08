---
name: iwara-search
description: Use when 用户要在 iwara 搜/收集视频图片、给收藏找新候选或问规则搜索。走 api.iwara.tv；含 playlist「遗漏挖掘」全流程：特征归纳→同义词表→A-D判定→逐条核验→报告；含整站快照脚本（本地全量匹配+核验）；含歌单写入（登录态建单/批量加片）。
---

# Iwara 内容发现与收集（含 playlist 遗漏挖掘与写入）

用户维护收藏 playlist（影奸/NTR/silhouette 向 MMD、异域舞娘/肚皮舞向）。任务形态：拉全量 → 归纳特征 → 同义词+规则搜索找新候选 → diff 去重 → 逐条核验 → 中文报告。现成判据/同义词表/作者索引：`references/collection-themes.md`（动手先读）；挖掘细则+报告模板：`references/playlist-workflow.md`；下载/赞助版：`references/downloads.md`；歌单写入（登录态）：`references/playlist-write.md`。

## 快速路径（先读）

- **访问 API 唯一要求：完整浏览器 UA**。`curl -s -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36" <api-url>` → 所有端点 200。无 UA / curl 默认 UA / 光写 "Mozilla/5.0" → 被 CF「Just a moment」挡。
- **数据一律 curl+UA 直连 API；不要用 agent 浏览器抓 iwara**：agent 自带 Chrome 访问 www/api 都被 CF 管理挑战卡在「请稍候」（无复选框，页面里 fetch 也读不到）。罕见需要浏览器语境时 → 见 Pitfalls 的 Camoufox 路线。
- **整站快照（要「尽可能全」时）**：先 `python <HERMES_HOME>/skills/iwara-search/scripts/iwara_snapshot.py update`（32 并发、断点续拉；全量约 12 分钟）→ 再 `search 词1 词2 --out x.md` 本地全量匹配、`verify` 核验；子命令 update/search/verify/playlist/info，手册与边界见 references/site-snapshot.md。
- 默认只读：搜索/挖掘任务不点赞/不关注/不评论/不改歌单；用户明确要求改歌单（建单/加片/移除）→ 走 `references/playlist-write.md`（登录态 API，Camoufox 过 CF）。
- 见到 `[SKILL_PRUNED]` 提示＝本技能内容被上下文压缩裁剪：`skill_view(name='iwara-search')` 重载一次即可，别重复摸索。
- 大批量任务写脚本落盘 JSON（别把全量结果粘进对话）；大文档增量更新用脚本分段读写、只把结论写回。
- 维护本技能：保持 SKILL.md ≤4000 字符——skill_view 结果超 5000 会在压缩时被裁成标记引发重载 churn；细节放 references/。

## 核心端点（无需 cookie，curl/python 直连）

1. **规则搜索（唯一完整索引，可分页）**：`GET /search?type=videos&query=<urlencoded>&page=N`（limit 默认 32，实测 48/50 可用；type 另有 images/users/playlists）
   - 运算符（`{...}` 块、空格 AND、整串 URL-encode；curl 直放 `{` `}` 需 --globoff）：`{tags: [silhouette]}`、`{author: mmd-bug}`、`{title_zh: 影奸}`、`{title_ja: 逆バニー}`、`{title_en: bunny}`、`{body_ja: 影姦}`、`{rating: ecchi|general}`。**`{rating: r18}` 无效=0——匿名可见只有 ecchi/general 两档**；少用 `{title: X}`（≈全库噪声）。
   - 结果字段全：id、title、body、user{username/id}、numViews/numLikes、tags[{id,type,sensitive}]、file、createdAt。
   - count 大体可信、小结果集偶虚（count>0 而 results=[]）→ 以 results 为准、翻到空页终止。
2. **单视频核验**：`GET /video/{id}` → status=active 才收录；有 body、file、fileUrl。403/私密单列，不混入正表。
3. **Playlist**：`GET /playlist/{uuid}?page=N&limit=32` → count/numVideos 可用但可能大于实拉（已删/私密项仍被计数）；空 results 终止，缺口写进报告。**标称数>可列出数时跑 `scripts/playlist_gap_audit.py` 定性缺口**（登录不解锁；403 私密/404 已删，方法论见 playlist-write.md）。
4. **用户全量**：`GET /profile/{username}` → user.id(uuid) → `GET /videos?user={uuid}&page=N`；该用户全部列表 `/playlists?user={uuid}&limit=64`（/users/… 路径 404）。
5. **论坛**：`/forum/threads?limit=50&page=N` 全量约 1.2 万帖、无服务端搜索（?query= 等参数全被忽略），抓全量 title 本地过滤；详情 /forum/threads/{id}（正文在 results[]，不是 posts）。

**⚠ `/videos` 系 count 全是假数**：?tags=、?user= 随 limit/page 变（5→11、50→101），裸列表≈limit+1；永远不当总数、不做规则搜索；?tags= 结果小而偏，仅兜底。
- 整站翻页零风控（2026-10 实测）：匿名+UA 翻到空页 ≈29.5–30 万条；32–64 并发持续跑零错误（详见 references/site-snapshot.md）。

## 遗漏挖掘（浓缩；细则见 references/playlist-workflow.md）

1. 拉全量+特征卡：tags 频次（≥15% 核心 / 5–15% 辅助）、标题词（中/日/英）、画面元素、≥2 部作者名单。别按列表名猜主题，读内容反推。
2. 同义词表：两列表现成表+作者系列索引见 collection-themes.md；新主题照模板扩（先抽词、再补各语言写法）。
3. 候选优先级：**要「尽可能全」→ 整站快照本地匹配（快速路径）**；常规路径：核心+同义 `{tags}` → 重点作者全量翻页（最易挖同系列不同版本）→ `{body_*}` 宽召回后按 tags 复核 → `site:iwara.tv` 引擎只当最后手段（几乎无收录）。
4. A>B>C>D：A 标题/标签硬命中；B 简介命中；C 同作者同系列/同视频不同版本；D 同动作+画面元素（标注、排最后）。每条写明命中依据。
5. 排除：`otokonoko`+男娘丢；动漫列表里 VAM 写实风丢；**幼态角色不排除**（loli/JS 照收）。
6. diff 去重（对 playlist 全量）→ 逐条 `/video/{id}` 核验 → 报告 `iwara-<主题>-<YYYY-MM-DD>.md`。

## Pitfalls

- 别用 `api.iwara.tv/videos?tags[]=x` / `?query=` 做规则搜索（count 假数、索引不全）；完整索引只有 /search 运算符。
- `{author: X}` 只匹配当前 username（改名作者先 resolve）；users 搜索是前缀模糊匹配（近名会混入），用返回的 username 精确核对。
- `/playlists?userId=…` / `?owner=…` 等参数名静默失效（返回全站约 78 万条且不报错），只有 `?user={uuid}` 是真过滤。
- 分页以空 results/短页终止，别按 count；批量翻页 sleep ~0.25s 防限流。
- `{title_en: 单词}` 常是某部作品专属（franchise 陷阱）；命中先核对是否真属该列表主题。
- videos 系 list 的 tags 偶发 null 数组；要 tags 用 /search 结果或 /video/{id}。
- 短中日词分词差 → 多换写法（中日英各试）；外部引擎 site:iwara.tv 基本不可用（DDG 异常验证、Bing 过滤成人）。
- **必须浏览器语境时（罕见）**：turnstile-bypass 的 `scripts/human_click.py`（Camoufox 引擎）2026-10-09 实测能过 iwara 墙——www auto-pass + cf_clearance、同会话 API 页直读 JSON；agent 自带 Chrome 则被卡在挑战页。
