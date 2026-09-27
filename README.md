# Hermes ACG 资源搜索 Skills

给 [Hermes Agent](https://hermes-agent.nousresearch.com/) / Cursor Agent 用的 skill 合集：**有图或关键词 → 认出作品 →（仅三次元且用户明确要求时）给磁力候选**，外加下载、新番表、图片格式等周边工具。

本仓库只含流程模板（`SKILL.md`），**不含账号、Cookie、API Key、会话记录或真实番号**。凭据一律放在你本机，配置方法见下方。

## 免责声明

**本仓库仅供学习、研究与技术参考，不构成法律建议，也不对任何检索结果的合法性、准确性或可用性作保证。**

- 技能只描述助手如何检索与比对公开网页上的元数据/候选，**不自动下载、不批量打种、不传播盗版文件**。
- 第三方站点内容、磁力链接、在线播放页均由使用者自行访问；请遵守所在地法律法规、著作权与各站服务条款。
- **18+**。疑似未成年相关请求必须拒绝。
- 因使用、配置或滥用本仓库造成的任何后果，作者与贡献者不承担责任。完整条款见 [DISCLAIMER.md](DISCLAIMER.md)。

## 包含的 skill

### 核心搜索闭环（互相引用，请全部安装）

| 文件夹 | 何时用 |
|--------|--------|
| [`acg-resource-search-router`](acg-resource-search-router/SKILL.md) | **主入口**。先读用户文字再搜网页；一行职员条/太碎纯字图读字搜声优或台词；整屏片尾可文字+以图；二次元不搜磁 |
| [`acg-reverse-image-search`](acg-reverse-image-search/SKILL.md) | 无标题/番号时的反向搜图。含 CF 墙应对（出口 IP → turnstile-bypass）与谷歌搜图 AI 模式；Lens 必须喂 `encoded_image` |
| [`jav-bangou-lookup-fc2`](jav-bangou-lookup-fc2/SKILL.md) | 查 JAV/FC2 番号、女优，核对 JavDB 或 FC2 官网；社交评论区路线（Threads/X 回复帖找番号） |
| [`acg-magnet-torrent-search`](acg-magnet-torrent-search/SKILL.md) | 搜磁力/种子/BT。四源仍空则三次元可走在线视频兜底；官方预览型跳过搜磁，只做预览核对 |

### 扩展 skill（按需安装）

| 文件夹 | 何时用 |
|--------|--------|
| [`jav-person-profile`](jav-person-profile/SKILL.md) | 查日本 ACG/JAV 人物档案（女优/声优/写真）：JavDB actor 优先，NotFound 降级萌娘/bangumi |
| [`sougouwiki-series-number-table`](sougouwiki-series-number-table/SKILL.md) | 要整系列番号清单或怀疑前缀不对时，从 sougouwiki 抓全表整理号→演员名（含 references/） |
| [`jav-number-decode`](jav-number-decode/SKILL.md) | 用户发来含隐藏番号的叙事文本：解码提取所有 JAV 番号并输出分组列表 |
| [`acg-release-schedule`](acg-release-schedule/SKILL.md) | 某月/下月的里番新番表或发售日历、要求附图时用：Hanime1 预告抓取 + 封面拼图（含 scripts/contact_sheet.py） |
| [`magnet-hash-aggregator-lookup`](magnet-hash-aggregator-lookup/SKILL.md) | 非 JAV 系列 / 死站资源找磁力、BT、网盘下载来源 |
| [`jmcomic-honbako-download`](jmcomic-honbako-download/SKILL.md) | 下载禁漫天堂/JMComic 本子：插件工具搜+下；JM 没有的走 Hitomi.la |
| [`pixiv-image-download`](pixiv-image-download/SKILL.md) | 抓 Pixiv 原图 / 动转 GIF / 按画师归档（依赖本机 pixiv-cli，见下方外部依赖） |
| [`iwara-search`](iwara-search/SKILL.md) | 在 iwara 搜/收集视频图片、给收藏找新候选；走 api.iwara.tv，不硬刚 CF 网页 |
| [`patreon-free-content-sites`](patreon-free-content-sites/SKILL.md) | Patreon 白嫖 / Kemono 不全时的替代源：Free Tier → 镜像 → Pawchive → Coomer |
| [`image-format-conversion`](image-format-conversion/SKILL.md) | webp/jpg/png 本地互转，再喂 vision 模型（反搜图 skill 引用） |

日常丢图搜资源时优先启用 **ACG resource search router**；其余按场景加载。

三次元资料/磁力还会调用本机 `javdb` 命令。CLI 本身不在本仓库，见 [javdb-cli 配置](#1-javdb-cli三次元强烈建议)。

## 流水线

```
抽出文字线索 + 判定二次元 / 三次元 + 太碎 / 纯字 / 是否整屏片尾

有标题 / 番号 / 卖家 / 站点 / 分集？
  是 → 网页检索（HTTP 优先）
         命中 → 二次元结束（无磁链）
                三次元 → 资料/官网核对 → 用户要磁力才搜磁
         未命中且有图 → 看是否太碎/纯字；否则反向搜图
否，一行职员条 / 太碎纯字图（不是整屏片尾）？
  是 → 读字 → 网页搜声优或台词（不要开 Lens/SauceNAO）
否，整屏 720p+ 片尾？
  是 → 文字定锤，可以顺便以图碰运气
否，仅有图且有可搜视觉 → 反向搜图

三次元且用户要磁力：javdb-cli → sukebei → OneJAV → JAVHouse
  四源仍空 → 在线视频兜底（时长 + 预览图 + 完整/预览标注；可附同作品旧号）
  官方预览型（FC2/DMM/Moodyz 等付费页，流站最终跳官方 embed）→ 跳过磁力与在线搜，只做预览核对
```

浏览器：**整个任务只允许 1 次 `new_tab`**，之后用 `goto_url`；读完就走；同时最多 3 个标签。禁止循环开新标签。

Google Lens：必须喂 `input[name=encoded_image]`。第一个 `input[type=file]` 是首页搜索框，喂进去只会显示「已添加 N 张图片」，不要点首页「搜索」。成功标志是 URL 出现 `vsrid=`。

---

## 安装

把需要的文件夹整目录复制到 skills 根下，保持「一 skill 一文件夹 + `SKILL.md`」。核心闭环 4 个必装；扩展 skill 按需。

### Hermes

官方默认目录是 `~/.hermes/skills/`。若你改过 `HERMES_HOME`（例如 Windows 上的 `F:\Hermes`），则复制到 `$HERMES_HOME/skills/`。下文 `<HERMES_HOME>`、`<WORK_DIR>` 均指你本机的对应目录（如 `F:\Hermes-work`）。

```bash
git clone https://github.com/843630162/hermes-acg-skills.git
```

```text
# 核心闭环（必装）
<HERMES_HOME>/skills/acg-resource-search-router/SKILL.md
<HERMES_HOME>/skills/acg-reverse-image-search/SKILL.md
<HERMES_HOME>/skills/jav-bangou-lookup-fc2/SKILL.md
<HERMES_HOME>/skills/acg-magnet-torrent-search/SKILL.md
# 扩展（按需，含子目录的整目录复制）
<HERMES_HOME>/skills/sougouwiki-series-number-table/   # 含 references/
<HERMES_HOME>/skills/acg-release-schedule/             # 含 scripts/
```

也可以按文件安装（社区源可能被安全扫描拦截，预览后再加 `--force`）。核心四个：

```bash
hermes skills inspect https://raw.githubusercontent.com/843630162/hermes-acg-skills/main/acg-resource-search-router/SKILL.md
hermes skills install https://raw.githubusercontent.com/843630162/hermes-acg-skills/main/acg-resource-search-router/SKILL.md
hermes skills install https://raw.githubusercontent.com/843630162/hermes-acg-skills/main/acg-reverse-image-search/SKILL.md
hermes skills install https://raw.githubusercontent.com/843630162/hermes-acg-skills/main/jav-bangou-lookup-fc2/SKILL.md
hermes skills install https://raw.githubusercontent.com/843630162/hermes-acg-skills/main/acg-magnet-torrent-search/SKILL.md
```

含子目录的扩展 skill（sougouwiki-series-number-table、acg-release-schedule）建议整目录复制；其余单文件 skill 可套用上面的 `hermes skills install <raw URL>` 模式。

或加为 tap 后按路径安装：

```bash
hermes skills tap add 843630162/hermes-acg-skills
hermes skills install 843630162/hermes-acg-skills/acg-resource-search-router
```

安装后新开一轮会话，或执行 `/reload-skills`。

### Cursor

项目级（推荐）复制到 `.cursor/skills/`，或用户全局 `~/.cursor/skills/`。结构同上。新开对话后用 `/` 或 `@` 调用。

---

## 本仓库已脱敏的内容

上传前去掉了只属于原作者环境、不应公开的信息：

| 已去掉 | 原形态（概要） | 请在本机自行配置 |
|--------|----------------|------------------|
| 会话 ID | 某次 FC2 检索的内部会话名 | 不需要；不要把 Hermes session 名写进 skill |
| 真实作品号 | 输出示例里的具体 `FC2-PPV-…`、以及某次检索用的新旧号 | 用 `{id}` / `{旧id}` / `{新id}`；真实番号只出现在你自己的对话里 |
| 「已经登录过」 | JAVHouse 等站点的本机登录状态 | 见下方浏览器登录 |
| 搜索后端细节 | 某次环境里的 Exa keyless 失败写法 | 按你的 Hermes `web.backend` / API Key 配置 |
| 实测职员条上的角色/声优名 | 某次用户截图里的具体字 | skill 里改成 `{角色名}` / `{声优名}` 占位；你自己搜时用 OCR 读到的原文 |
| 本机路径、Cookie、token | 未收录 | **永远不要**写进 `SKILL.md` 或提交到 git；skill 里出现时用 `<HERMES_HOME>` / `<WORK_DIR>` 占位 |

公开 skill 里保留的是站点域名、检索顺序和操作规则（例如分集 `…15` 与 `15,5` 不是同一部）。这些是流程，不是账号。

---

## 本地配置

### 1. javdb-cli（三次元强烈建议）

四个 skill 在三次元路径会调用 `javdb search` / `javdb detail` / `javdb magnets`。二进制和对应 Hermes skill **不在本仓库**。

1. 从稳定 Release 安装 CLI（不要直接用 `main`）：  
   [FlanChanXwO/javdb-cli/releases](https://github.com/FlanChanXwO/javdb-cli/releases)  
   Windows 把 `javdb.exe` 放到已在 `PATH` 的目录。装完执行 `javdb --version`。
2. **搜资料和磁力默认可以匿名。** 只有要用「我的列表 / 想看 / 已看」等账号功能时，在**你自己的终端**登录：

   ```bash
   javdb auth login
   ```

   凭据写入 `~/.javdb-cli/auth.json`（Windows：`%USERPROFILE%\.javdb-cli\auth.json`）。该文件含用户名、密码与 JWT，权限应尽量收紧。
3. **不要**把 `auth.json` 复制进本仓库、不要贴到聊天、不要让 agent 打开该文件「帮忙排错」。
4. 可选：把官方 javdb-cli skill 一并装进 Hermes（以 Release tag 为准，版本号自行替换）：

   ```bash
   hermes skills install https://raw.githubusercontent.com/FlanChanXwO/javdb-cli/v0.7.3/skills/javdb-cli/SKILL.md
   ```

5. 网络不通时，用 CLI 自己的代理，而不是把代理密码写进 skill：

   ```bash
   javdb --help
   javdb config --help
   # 一次性：javdb search SSIS-589 --proxy http://127.0.0.1:7890
   ```

CLI 不可用时，skill 会降级打开 JavDB 网页，并应在输出里写明原因。

### 2. 需要登录的网页（JAVHouse 等）

`javhouse.org` 必须登录才能搜。本仓库**不会**保存 Cookie。

在 Hermes `config.yaml` 使用持久化真实浏览器配置，例如：

```yaml
browser:
  use_real_profile: true
```

然后用**同一套**浏览器配置，由你本人打开站点并登录。不要把 Cookie 头、`document.cookie` 或账号密码写进 `SKILL.md`。未登录时 agent 应跳过该站并注明。

Cursor / 其他助手同理：用你平时已经登录过的浏览器配置，而不是每次临时空白 profile。

### 3. 网页搜索（`web_search`）

skill 在「有标题找番号」时会先网页检索。后端由 **Hermes 自己的配置**决定，本仓库不绑定某一家。

任选其一（按你现有环境）：

| 方式 | 怎么配 |
|------|--------|
| 自建 SearXNG | `config.yaml` 里 `web.backend` / `web.search_backend: searxng`，并配好实例地址 |
| Exa | 在 Hermes 环境变量中设置 `EXA_API_KEY`（不要提交 `.env`） |
| Firecrawl 抽取 | 设置 `FIRECRAWL_API_KEY`，或改用本地/其他 extract 后端 |
| 什么都不配 | skill 要求：`web_search` 失败立刻改 `curl` 或 DuckDuckGo HTML，禁止为此狂开标签 |

**不要把 Key 写进本仓库。** Hermes 常见位置是 `$HERMES_HOME/.env` 或进程环境变量。

### 4. 反向搜图引擎

二次元主链（onegai.moe、soutubot.moe、SauceNAO、trace.moe、ascii2d）和三次元主链（Google Lens、Yandex、iqdb、avscan.cc）都走公开网页，**默认不需要 API Key**。

可选加强：

- **SauceNAO**：在 [saucenao.com](https://saucenao.com/) 注册后可提高限额。若你要让脚本走 API，把 key 放环境变量（例如 `SAUCENAO_API_KEY`），不要写进 skill。当前 `SKILL.md` 按网页使用，无 key 也能搜。
- **Google Lens**：必须喂 `input[name=encoded_image]`，不要打第一个 `input[type=file]`（那是首页搜索框，「已添加 N 张图片」= 传错了）。成功标志是 URL 出现 `vsrid=`。若出现「图片未与账号关联」，在持久化浏览器里登录 Google 后再试；不要去操作页内 Gemini。失败就记一笔，进入下一引擎。
- 部分引擎在国内可能需要系统代理；代理账号同样只放系统或 Hermes 环境，不放 skill。

### 5. FC2 官网核对

FC2 商品页主机固定为 `https://adult.contents.fc2.com/article/{id}/`。用 `curl` 直链即可，`/search/?q=` 可能跳登录。

官网返回「商品見つかりません」只说明**当前会话/地区看不到**，不能单独否决番号。对照方法写在 `jav-bangou-lookup-fc2` 里：再 curl 一个已知在售的近邻 ID，区分「下架」与「地区限制」。

不需要 FC2 账号也能做资料对比；有账号也不要把 Cookie 提交到 git。

### 6. 外部依赖（引用其他仓库 / 本机工具）

部分 skill 引用了不在本仓库的外部组件，按需安装：

| 依赖 | 来源 | 被哪些 skill 引用 |
|------|------|------------------|
| `javdb` CLI + javdb-cli skill | [FlanChanXwO/javdb-cli](https://github.com/FlanChanXwO/javdb-cli)（Release 安装，见上方第 1 节） | acg-magnet-torrent-search、jav-bangou-lookup-fc2、acg-resource-search-router、sougouwiki-series-number-table、jav-person-profile |
| `turnstile-bypass`（CF 墙过墙：human_click.py / cf_clearance cookie） | [Sophomoresty/turnstile-bypass](https://github.com/Sophomoresty/turnstile-bypass)（clone + `python3 scripts/install.py`，自带 .venv） | acg-reverse-image-search、iwara-search 的 CF 墙应对节 |
| `pixiv-cli`（单文件 CLI + venv，含 gppt 登录脚本） | 本机自建：`<HERMES_HOME>/tools/pixiv-cli/`（基于 [upbit/pixivpy](https://github.com/upbit/pixivpy) + [eggplants/get-pixivpy-token](https://github.com/eggplants/get-pixivpy-token)，不随仓库分发） | pixiv-image-download |
| `jmcomics` Hermes 插件（JMComic 下载，凭据在插件 option.yml） | 本机自建：`<HERMES_HOME>/plugins/jmcomics/`；参考 [hect0x7/JMComic-Crawler-Python](https://github.com/hect0x7/JMComic-Crawler-Python) | jmcomic-honbako-download |
| libwebp / ffmpeg 便携二进制 | `<HERMES_HOME>/tools/`（Google 官方预编译，BSD-3-Clause；不随仓库分发） | image-format-conversion |

skill 内的相对链接（如 `../web/turnstile-bypass/SKILL.md`）指向 Hermes 本机 skills 目录布局；外部组件未安装时对应路径自动降级（skill 里已写明降级动作）。

### 7. 不要提交的文件

`.gitignore` 已覆盖常见机密文件。额外确认：

- `~/.javdb-cli/auth.json`
- Hermes `auth.json`、`.env`、`config.yaml` 里的 Key 与本地模型地址
- 浏览器 Cookie / `cookies.txt`
- 含真实番号、会话 dump、用户截图的对话日志

---

## 使用提示

1. 丢图或关键词搜资源：先开 **ACG resource search router**。
2. 已经确定只要番号/官网对比：用 **JAV bangou lookup FC2**。
3. 已经确定只要磁力：用 **ACG magnet torrent search**（二次元须用户明确说要磁力）。
4. 不要伪造 magnet hash；不要在用户未确认时调用下载器。

## 许可证

[MIT](LICENSE)。使用前请阅读 [免责声明](DISCLAIMER.md)。
