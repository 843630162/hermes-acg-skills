# 整站快照：拉取 + 本地匹配 + 核验（命令手册）

**用途**：要「尽可能全」时，把 iwara 公开列表整站拉到本地，用多语言词表做本地匹配——补站内搜索对短中日词的短板（站内「隐奸」只出 2 条那种）。与 `/search` 运算符的分工：

- `/search` 运算符 = 精确结构过滤（tags/author/title/body），秒级——快速定位、种子作者；
- 整站快照 = 全量文本召回（标题/简介/标签/作者），本地、可复算、跨主题复用——「找遗漏」正路。

## 0. 事实速查（2026-10 实测）

- 规模：约 29.5–30 万条、5,900–6,000 页（page 5900 满、6000 空）；列表自带 title/tags/body/时长/播放/点赞，够本地匹配。
- 并发与耗时（实测，深度翻页全程 0 错误）：

| 并发 | 吞吐 | 全量预计 | 单请求延迟 |
|---|---|---|---|
| 1 | 0.4 个/秒 | ~4 小时 | 2.4s |
| 16 | 5.7 个/秒 | ~17 分钟 | 2.7s |
| 32（默认） | 8.0 个/秒 | ~12 分钟 | ~4s |
| 64（上限） | 11.0 个/秒 | ~9 分钟 | 5.3s |

- `/videos` 的 count 字段是假数（裸列表≈limit+1）——只按「空页」判终止。
- 数据：JSONL 一行一条（裁剪字段），约 0.2–0.4GB；默认目录 `<HERMES_HOME>/iwara-snapshot`（首次 update 自动创建；`--dir` 或环境变量 `IWARA_SNAPSHOT_DIR` 可改）。放 F: 盘，别放 skills/ 或任务中间产物目录。
- 脚本纯标准库，本机 `python` 直接跑，无依赖。

## 1. 命令（复制即用）

脚本：`<HERMES_HOME>/skills/iwara-search/scripts/iwara_snapshot.py`

```
# ① 建立/增量更新快照（首次约 12 分钟；可反复跑，断点续拉）
python <HERMES_HOME>/skills/iwara-search/scripts/iwara_snapshot.py update

# ② 本地匹配（多词 OR；标题/简介/标签/作者；--out 落 md+jsonl）
python <HERMES_HOME>/skills/iwara-search/scripts/iwara_snapshot.py search silhouette シルエット 影姦 隠姦 カーテン --out <WORK_DIR>/cand.md --exclude-ids <WORK_DIR>/playlist.json

# ③ 核验候选（逐条 /video/{id} → active / 拿不到 两张清单）
python <HERMES_HOME>/skills/iwara-search/scripts/iwara_snapshot.py verify --in <WORK_DIR>/cand.jsonl --out <WORK_DIR>/cand-verified.md

# ④ 拉 playlist 全量（JSON；可直接喂给 ② 的 --exclude-ids 去重「已收藏」）
python <HERMES_HOME>/skills/iwara-search/scripts/iwara_snapshot.py playlist https://www.iwara.tv/playlist/<uuid> --out <WORK_DIR>/playlist.json

# ⑤ 查看快照状态（条数/日期范围/断点）
python <HERMES_HOME>/skills/iwara-search/scripts/iwara_snapshot.py info
```

所有子命令都支持 `--dir`（默认 `<HERMES_HOME>/iwara-snapshot`）。

## 2. update 行为

- 从 `page 0` 开翻（新视频在最前），空页终止；两段式：先扫顶部收新（连续 2 页无新即停）→ 未完成的历史从 `state.json` 断点续（回退 20 页重叠，防插队漏）。长跑时每约 15 秒打印一行进度（页数/新增/速率）。
- 容错：429/5xx/网络错误指数退避重试；失败页留痕、最多补扫 3 轮，绝不静默跳过；Ctrl-C 随时安全，重跑同一条命令即续。
- 参数：`--workers 32`（实测干净上限 64，不建议再高）、`--rewind 20`、`--reset`（从头重扫）、`--max-pages N`（调试用，本次最多取 N 页）。
- 覆盖：匿名可见公开列表（general/ecchi；r18 需登录看不到）；**unlisted/私密不在**——补 unlisted 用作者全量（`/profile/{username}` → `/videos?user={uuid}`，见 playlist-workflow）。

## 3. search 行为

- 匹配：词对 title/body/tags/作者名做不分大小写子串匹配；NFKC + 片假名↔平假名折叠（シルエット≡しるえっと）；简繁不自动——词表里简繁两种写法都写。
- OR 语义；命中记录「匹配词」→ 报告里的「匹配理由」（再按 A/B/C/D 复核）。
- `--exclude-ids` 排「已收藏」（playlist.json / ids.txt / 含链接的 md 都行）；`--not 词` 误命中排除（可多个：先粗跑、看高频误命中、补进排除表重跑）；`--terms-file` 词表文件（一行一词）；`--sort views|date`；`--limit` 终端预览条数。
- 输出：终端 = 摘要 + 前 N 行；`--out 名` = `名.md`（表格，人看）+ `名.jsonl`（机器用，含 file_id / 匹配词）。

## 4. verify 行为

读 `--in`（jsonl/txt/含链接 md），并发 8 逐条拉 `/video/{id}`：active 进正表、404/403/非 active 进「拿不到」；输出 md + 终端摘要。报告「逐条核验」环节用。

## 5. 缩略图（可选视觉复核）

`<file_id>`（在 search 的 `.jsonl` 里）→ `https://i.iwara.tv/image/thumbnail/<file_id>/thumbnail-01.jpg`（实测：01/15 是不同的真实帧；不存在的序号回固定占位图）。对「待确认」档抽看封面用。

## 6. 小模型 / agent 操作卡（照抄即行）

1. 用户要「找遗漏/找全」→ 先 `info`；快照不存在或太旧 → `update`（等它跑完）。
2. `search <词表> --exclude-ids <playlist.json> --out <名字>.md` → 读 `.md` 表格继续处理（**别把 .jsonl 全量读进上下文**）。
3. 存疑候选 → `verify --in <名字>.jsonl --out <名字>-verified.md`。
4. 看最后一行判断结果：`OK`=成功；`[ERR]`=网络问题，重跑即续；`[!]`=被中断，重跑即续。
5. 不要手工改 `videos.jsonl` / `state.json`；要重扫用 `update --reset`。

## 7. 边界与维护

- 报告写明「数据来源：整站快照（日期）+ 运算符流」；快照口径（≈30 万）与 `/search` 计数口径（general+ecchi≈32.4 万）不一致，别混用总数。
- 快照是可复用资产：换主题只跑 `search`，不用重拉；丢了重跑 `update`（约 12 分钟）。
- 更新节奏：平时一条 `update` 很快完成（只扫顶部 + 补断点）；全量首跑或断了再续才需要十几分钟。
