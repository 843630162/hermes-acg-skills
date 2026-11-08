---
name: laowang-cli
description: "Use when 在老王论坛(laowang.vip)搜资源/提取帖子磁力m3u8种子/预览购买/维护CLI。"
version: 0.2.1
author: local, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [laowang, discuz, resource-search, magnet, cloud-drive, cli]
    related_skills: [acg-resource-search-router, acg-magnet-torrent-search, magnet-hash-aggregator-lookup, discuz-forum-reverse]
---

# 老王论坛 CLI (`laowang-cli`)

基于 Python 标准库的 `laowang.vip`（老王论坛，Discuz! X3.4）命令行工具，供 Hermes 检索帖子、在常规磁力源无结果时做论坛兜底搜索、免扣币提取公开/内嵌资源（网盘链、磁力、在线视频 `m3u8` 与 `.torrent`），以及在用户明确授权下预览/购买付费附件或资源卡。

## When to Use

- 用户明确提到老王论坛、`laowang.vip`、`laowang` CLI，或给出老王论坛帖子 `tid` / URL。
- 搜资源（三次元番号/同人/国产/欧美、二次元里番/3D/本子、H 游、套图写真、小说/ASMR、AI 视频/套图）在常规磁力源（JavDB、sukebei、OneJAV、JAVHouse、868888 等）**找不到磁力链或做种死绝**时，用 `laowang search` 搜论坛内的百度盘/夸克/PikPak/123pan 网盘档、种子附件或在线视频源。
- 不要用于：未尝试番号规范化与 JavDB/sukebei 主链就直接跳过主链（三次元番号仍以 `javdb-cli` → `sukebei` 为先，老王论坛作为无磁力/缺中字/缺网盘时的补充与兜底）。

## Prerequisites

- **全局命令**：`laowang`（已安装于 `<HERMES_HOME>\bin\laowang` 与 `<HERMES_HOME>\bin\laowang.cmd`，底层指向 `<HERMES_HOME>\tools\laowang-cli\laowang.py`；skill 备份位于 `<HERMES_HOME>\skills\laowang-cli\scripts\laowang.py`）。
- **状态与凭据目录**：默认 `<HERMES_HOME>\.laowang`（可通过 `LAOWANG_HOME` 或 `--home` 覆盖；首次运行自动从 `%USERPROFILE%\.laowang` 只读迁移 `state.json` / `config.json`，全程不写 C 盘）。
  - `state.json`：持久化登录 Cookie（`X9wU_2132_auth`、`saltkey`）与浏览器指纹。
  - `config.json` 或环境变量 `LAOWANG_USERNAME` / `LAOWANG_PASSWORD`：账号密码（站点要求密码仅限 ASCII，登录时本地自动解算 TNCode 滑块验证码）。**本机默认没有这份 config**——日常检索靠 `state.json` 里的长期登录会话跑；`laowang login --force` 报缺凭据时，先把账号密码写进 `<HERMES_HOME>\.laowang\config.json` 再登录。凭据只写在本机 `config.json`，**不要提交进仓库**，文档与回复里不写密码明文。

## 修改 CLI（维护）

- `<HERMES_HOME>\bin\laowang` / `.cmd` 入口是薄 bash 封装，exec 的是 `<HERMES_HOME>\tools\laowang-cli\laowang.py`；skill 备份 `scripts/laowang.py` 是**另一份拷贝**，两份会漂移（换行/空行差异常见）。改前先 `head -5 <HERMES_HOME>/bin/laowang` 确认真实执行路径。
- 改动一律**两份同步打同一处补丁**，并 `python -m py_compile` 两份文件；只改备份时全局命令仍跑旧逻辑。改完用一个挂 pansell 卡的帖子跑 `laowang thread <tid>` 验证新字段/行为（已购帖可复验 `pv_card` 解析）。

## Quick Reference

通过 `terminal` 工具直接调用 `laowang`（所有命令默认在 stdout 输出 UTF-8 JSON）：

```bash
laowang whoami                                      # 查看当前登录账号、UID、软妹币余额
laowang balance                                     # 仅查看积分与软妹币余额
laowang login [--force]                             # 使用已配凭据自动过滑块登录并保存会话
laowang forums                                      # 列出全站分区与板块 fid
laowang search "关键词" --page 1                     # 按标题搜索帖子（默认 --field subject）
laowang search "关键词" --forum 40 --page 1          # 限定板块 fid 搜索
laowang search "作者名" --field author --page 1      # 按作者搜索
laowang thread 3040606                              # 读取帖子正文、附件、remote_play、付费状态、网盘检测、资源卡磁力映射(pv_card)
laowang buy 3193402                                 # 预览购买（默认 dry-run，绝不扣币）
laowang buy 168943 --list-only                      # 仅列出帖内未购付费附件
laowang buy 3193402 --max-price 10                  # 带价格上限的 dry-run 校验
laowang buy 3193402 --max-price 10 --confirm        # 实际扣币购买（必须获用户当次明确授权！）
laowang collect 3040606 3193402 --out <WORK_DIR>/lw.md   # 批量抓取帖子导出 .md/.jsonl/.json
```

## 常用板块 `fid` 速查

| 类别 | 常用板块 (`--forum <fid>`) |
|------|---------------------------|
| **三次元视频下载** | `40` 亚洲无码下载、`41` 亚洲有码下载、`43` 国产自拍下载、`45` 欧美视频下载、`46` 直播视频下载、`60` TP视频下载、`61` 三级/18R影视、`229` VR资源区 |
| **二次元专区** | `44` 二次元视频、`517` 二次元本子、`1052` 在线漫画 |
| **套图 / 写真** | `47` 亚洲套图下载、`51` 欧洲套图下载 |
| **H 游 / 软件** | `65` 游戏下载区、`58` 软件下载区 |
| **AI 专区** | `650` AI套图、`957` AI视频、`1004` AI资源工具 |
| **小说 / ASMR** | `48` 文本小说下载、`49` 有声小说&ASMR下载区 |
| **综合 / 网盘** | `727` 其他网盘资源、`53` 特别福利（合集/稀有）、`74` 重口味资源、`54` 互助加速 |
| **在线视频区** | `906` 原创视频、`907` 搬运视频、`437` 91精选、`995` 麻豆传媒、`864` 综合分类大区、`253` 综合存档、`261` 中文字幕、`458` 无码专区 |

## Procedure

1. **搜索候选帖**：
   - 运行 `laowang search "<关键词>" [--forum <fid>]`。
   - 番号检索建议同时尝试连字符版（`SSIS-840`）与无连字符/空格版（`SSIS 840`、`SSIS840`），因为老王论坛发帖标题格式不一。
   - 番号（各变体）0 命中时，关键词按序升维：系列前缀（如 `DEAA`）、作品标题、**女优本名**。本名检索是找合集帖最有效的方式——同一女优的多作合集帖常含目标作品；艺名（如 `×ちゃん`）过于宽泛，多命中无关作品。命中合集帖时先核对发帖日期与目标作品配信日——帖早于配信日即该合集不含目标作品，别误报命中。
  - **外文（韩语等）人名检索**：标题检索 `--field subject` 不索引非 CJK 字符（韩语全 0 命中），必须改用 `--field _all` 正文全文检索（正文可命中）。她在论坛的发帖名常是**中文音译**（韩文名直搜会漏掉大部分帖）：先读命中帖正文，从出演列表里挖出全部中文音译别名，再逐个用 `--field _all` 补搜——单个别名会漏合集帖。
   - 检查输出 `results[]` 中的 `tid`、`title`、`forum`、`date`、`snippet`，过滤掉标题含 `[已失效]` 的旧帖。
2. **读取帖子详情并自动提取免费资源**：
   - 运行 `laowang thread <tid>`。该命令不扣任何软妹币，自动完成四类解析：
     - **直链与提取码**：`links[]`（magnet、ed2k、百度盘、夸克、阿里、123pan、PikPak、蓝奏、城通、Mega、Google Drive）与 `codes[]`（提取码/解压密码）。
     - **在线视频 `remote_play` 免扣币直提**：若帖内嵌有 `<iframe src="/remote_play/video/play/{id}.html">`，自动请求子应用接口提取免费 `m3u8_url`（HLS 流）与百分号编码后的 `.torrent` 种子直链，填入 `remote_play[]` 并追加到 `links[]`。
     - **多作品资源卡（`.pv-card`）结构化映射**：`pv_card` 字段（`status: unlocked/locked`、`price`、`purchased`、`files[]`）。`files[]` 每项含 `title`（所属作品标题）、`size`、`url`（反转义后的干净磁力/网盘链，单个 `&`）、`code`（提取码，如有）——已解锁卡按 `title` 直接配哪条磁力属于哪部作品；锁定卡 `files[]` 为空（文件隐藏在购买墙后）。`links[]` 仍是平铺裸串（可能带 `&amp;amp;` 实体残留），配对一律以 `pv_card.files` 为准。
     - **付费门禁与网盘死链预检**：`paid` 字段汇总四类门禁：
       - `needs_pansell_pay` + `pansell_price`：老王最常见的 `.pv-card` 资源购买卡（`jnpar_pansell` 插件）。若带网盘检测按钮（`.pv-file`），`laowang thread` 会自动调用 `jnpar_pansell:check` 写入 `paid.pansell_checks[]`（`valid: true/false`）；若网盘已失效且服务端在隐藏 `<p style="display:none">` 泄露原链接，自动提取到 `leaked_url` 和 `links[]`。
       - `needs_attach_pay` + `unpaid_attachments[]`：付费附件（`.torrent` 或压缩包），含 `aid`、`filename`、`price`。
       - `needs_thread_pay` + `thread_price`：Discuz 原生主题付费。
       - `needs_reply_to_view` / `hidden_locked`：回复可见锁（`[hide]`）。
3. **处理付费资源（Dry-run 优先，严禁擅自购买）**：
   - 若目标资源在 `unpaid_attachments`、`needs_pansell_pay` 或 `needs_thread_pay` 后面：
     1. 先运行 `laowang buy <tid> [--aid <aid>]`（不带 `--confirm`）做 dry-run。
     2. 若 `pansell_checks` 全部为 `valid: false`，CLI 会以退出码 `2` 拒绝购买（防止花冤枉钱买死链），此时直接向用户报告网盘已失效（及是否有 `leaked_url`），再去搜同资源的其他帖子。
     3. 若链接有效或为磁力/种子附件，向用户汇报：**帖子标题、`tid`/`aid`、售价（软妹币）、当前余额（`balance_ruimeibi`）、购买后余额（`balance_after`）**，询问用户是否确认购买。**目标是合集帖时，先列出帖内含作品（正文标题块或 `pv_card.files`）并核对是否包含用户目标作品**——本名/系列命中合集帖不等于含目标片，购买决策前要让用户看到清单。
     4. **仅在用户当次明确同意购买该 `tid`/`aid` 及价格后**，运行 `laowang buy <tid> [--aid <aid>] --max-price <N> --confirm`，随后再跑一次 `laowang thread <tid>` 提取解锁后的链接或附件下载地址。
4. **多作品资源卡（pansell）磁力配对**：含多部作品的 pansell 卡购买后，重跑 `laowang thread <tid>` 读 `pv_card.files[]`——每项已带 `title`（作品名）+ `size` + `url`（干净磁力，单 `&`），按 `title` 分组直接汇报，无需再手工解析。仅当 `pv_card` 为 null 而 `links[]` 有裸磁力（旧版 CLI）时降级：读 `<HERMES_HOME>\.laowang\state.json` 的 `cookies[]` 列表拼 `Cookie:` 头（cookie 值禁止打印），带 Referer=帖子 URL 用 curl 拉帖子页 HTML，在「已解锁」卡块（`<div class="pv-card">` 内 `pv-file` 序列）中每部作品为一段标题块 + 后续若干 `[大小]magnet:...` 行，按文档顺序配对，输出前 HTML 反转义两次（卡体内容双重转义，`&amp;amp;`→`&`）。页面里找不到「已解锁」块说明会话过期——先 `laowang login --force` 再重试。

## Pitfalls

- **绝对禁止未经授权加 `--confirm`**：任何消耗软妹币的操作都必须先 dry-run 并获得用户对具体 `tid`/`aid` 和价格的明确指令。
- **`--confirm` 成功后要复核余额再报成功**：CLI 返回 `ok:true` 不等于已扣款；再跑一次 `laowang balance`，确认软妹币差额与购买价一致才向用户报告。
- **帖内预览图常是 WebP 冒充 `.jpg`**：老王帖内嵌预览图 URL 虽以 `.jpg` 结尾，实际常为 WebP（file magic `RIFF/WEBP`）。下载带帖子页 Referer + 浏览器 UA；交付 MEDIA 前先 `file` 核查，WebP 时用 `ffmpeg -i in.jpg -q:v 3 out.jpg` 转真 JPEG（本机 ffmpeg 在 `<HERMES_HOME>\ffmpeg\bin\ffmpeg`）。
- **凭据默认不外泄，但用户索要就直接给**：不要主动在回复、日志或注释里打印 `<HERMES_HOME>\.laowang\state.json` / `config.json` 的密码与 `auth` Cookie 原文（会话 Cookie 尤其不要贴出来）。但用户明确要「我的账号密码」时，那是他自己的凭据——从权威位置取出、直接给出用户名+密码，别只回「存在密码管理器里读不出来」。
- **表观 `price: 0` 不代表免费**：老王论坛大量帖子主题 `price` 为 0，但实际挂了 `attachpay`（付费附件）或 `jnpar_pansell`（`.pv-card` 资源购买卡）。`laowang.py` 已在 `parse_thread` 的 HTML 扫描阶段把这两类价格与状态合入 `paid` 字段，务必看 `paid.needs_pansell_pay` 和 `paid.needs_attach_pay`。
- **`.torrent` 附件是磁力载体，正文 `links[]` 常为空**：标题带「磁力链接」的帖，磁力不在正文里，在 .torrent 文件内部。用会话 Cookie（state.json `cookies[]` 拼 `Cookie:` 头）+ 浏览器 UA + `Referer: https://laowang.vip/forum.php?mod=viewthread&tid=<tid>` 下载附件（URL = `https://laowang.vip` + `attachments[].url` + `attachments[].attachment`，即 `/remote/data/attachment/forum/202403/31/xxxx.attach` 这类**存盘路径**；不是 `filename` 显示名，用 filename 拼必然 404），免费附件（`price: 0`）直接下，付费附件先走 buy 流程；再用 `scripts/torrent_magnet.py` 解析出 `magnet:?xt=urn:btih:<info hash>`（SHA1 of info dict）。种子自带 tracker 常已死，别据此单独判「种死了」，磁力交给用户客户端验证。
- **免费/付费按 `attachments[]` 逐项看 `price`，别只看 `paid.needs_attach_pay`**：同一帖里图片附件 `price: 0`、种子附件 `price: 10` 很常见（`needs_attach_pay` 只汇总「有不免费的附件」，具体哪一个是免费的要看每项的 `price` / `payed`）。标题写「磁力链接」而 `links[]` 为空时，先翻 `attachments[]` 里 `.torrent` 的那一项。
- **请求限速与防 Flood**：CLI 内置每次 HTTP 请求间隔 ≥1.5 秒。不要用多进程并发狂刷 `laowang search`；若返回 `code: "flood"` 或 `"captcha"`，立即停止连发并等待退避。
- **Flood 实测退避时长**：连发多次搜索后 flood 会持续很久（30~115 秒静默仍失败）。实测**静默约 180 秒**后单次搜索即恢复；恢复成功后按**每次搜索间隔 ≥45 秒**节奏连发（每次只发 1~2 个关键词）可稳定跑完多轮检索。规划多关键词检索时：先静默 3 分钟，再按 45 秒/次的节奏跑，别把关键词堆在一起发。
- **搜索是标题 AND**：`--field subject`（默认）只在标题里做关键词 AND，多词查询命中数会骤降；找某类资源时应先用**单个领域词**（如 `厕拍`、`漫展 厕拍`）打开题材面，再用 `--forum <fid>` 收窄。命中帖的正文若挂在 pansell 付费卡后，`laowang thread` 的 `posts[].message` 会是空串（正文在付费墙内），此时只能靠 `paid.pansell_price` 与标题判断，别误判成空帖。
- **pansell 卡连预览图一起锁**：挂了 `jnpar_pansell` 的帖，正文、预览图、链接全部在墙后——带登录 Cookie 拉帖子页 HTML 也 0 张帖内 `<img>`。别反复抓 HTML 找免费预览；直接告知用户预览需购卡，并从漏站/聚合站取同图包的公开预览替代交付（见 acg-reverse-image-search 的 references/coser-identity-attribution.md 的预览抓取配方）。
- **福利姬/Coser 有多个 CN 别名**：同一人常以 3-5 个名字发帖（如 Yiko湿润兔=咬一口兔娘=黏黏团子兔=咬人小小兔）。单个别名搜 0 命中不能断定无帖；换别名再搜，再用「别名+角色名」两词 AND 精确定位（命中极准，噪声极小）。
- **买前交付预览网格**（用户固定要求）：搜到候选帖后先不扣币，把该图包的公开预览全量下载，用 PIL 做 5×6 编号网格 JPEG（每格左上 `#N` 黄字，quality≈82，每 sheet 一 MEDIA），全部发出并列出各帖 tid/卡价/余额，等用户确认再 `--confirm`。
- **有些板块连预览都锁**：视频类板块（AI视频 fid=957、视频综合）的 pansell 卡 `needs_pansell_pay:true` 时，正文与预览图一起锁定，`laowang thread <tid>` 拿不到任何 img —— 此时「先给预览再决定买不买」做不到，要直接说明并列出卡价（常 1–7 币），别猜内容。老帖（标题带年份、无 pansell）常有 `paid:false` + `remote_play:[{m3u8_url, pic_url}]`：`pic_url` 是免费海报图，m3u8 是 AES-128 加密流（key URI 相对 m3u8）——用会话 Cookie + UA + `Referer: https://laowang.vip/` 取 index.m3u8/vod.jpg，再 `ffmpeg -headers "User-Agent: ...\r\nReferer: ...\r\n" -ss <t> -i <m3u8> -frames:v 1` 抽帧；这类直链常已失效（404），没有 Cookie 时也 404。
- **判断「这条资源里有没有我的片段」用帧哈希，不用标题**：抽候选帖的帧后跑 `reverse-image-search/scripts/compare_frames_dhash.py`，≥0.25 就是不同内容（同一帖标题写「裸舞」不代表含你的那段）。
- **只读原则**：本工具不提供发帖、回帖、评分、私信功能；遇到 `needs_reply_to_view: true` 的回复可见帖，优先换搜同资源的免回帖/直链帖或告知用户在浏览器处理，不要编写自动灌水回帖脚本。

## 从脚本 / cron 里调用（非交互）

- **`<HERMES_HOME>\bin\laowang` 是 bash 壳，Python `subprocess` 直接调 `laowang` 会 `WinError 2`**（Windows 无扩展名可执行找不到）。脚本里一律 `subprocess.run([sys.executable, r"<HERMES_HOME>/tools/laowang-cli/laowang.py", "search", ...], env=dict(os.environ, LAOWANG_HOME=r"<HERMES_HOME>/.laowang"), encoding="utf-8")`，解析 stdout 的 JSON。cron 会话里 PATH 与 shell 都不同，别指望 `laowang` 命令可用。
- 分页检索：`total` 字段给出命中总数，`count` 每页 20；循环 `--page 1..N` 直到 `page*len(results) >= total` 或结果不足 20 页大小。关键词「埋导演」与「埋 导演」命中集完全相同（Discuz 会分词），但简写别名（如「埋导」）是**另一批帖**，做监控时要把别名一起查。

## 姊妹站：司机社

用户说「司机社」时指 xsijishe.com（国内）/ xsijishe.net（海外镜像），同为 Discuz，游客搜索与正文均被登录墙挡住——搜法与绕行见 `references/sijishe-forum.md`。

## Verification

1. 运行 `laowang whoami` 确认 `"ok": true`、`"home": "<HERMES_HOME>\\.laowang"` 且返回有效 `uid` 与 `ruimeibi` 余额。
2. 运行 `laowang search "<关键词>" --page 1` 与 `laowang thread <tid>`，确认前后 `ruimeibi` 余额不变。
