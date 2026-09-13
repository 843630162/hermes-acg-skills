# Hermes ACG 资源搜索 Skills

给 [Hermes Agent](https://hermes-agent.nousresearch.com/) / Cursor Agent 用的四件套：**有图或关键词 → 认出作品 →（仅三次元且用户明确要求时）给磁力候选**。

本仓库只含流程模板（`SKILL.md`），**不含账号、Cookie、API Key、会话记录或真实番号**。凭据一律放在你本机，配置方法见下方。

> 18+ 向。疑似未成年内容必须拒绝。技能只检索与比对，不自动开下、不批量打种。请自行遵守所在地法律与站点条款。

## 包含的 skill

| 文件夹 | 何时用 |
|--------|--------|
| [`acg-resource-search-router`](acg-resource-search-router/SKILL.md) | **主入口**。先读用户文字再搜网页；有标题/番号不要先反向搜图；二次元不搜磁；三次元才做 FC2/磁力 |
| [`acg-reverse-image-search`](acg-reverse-image-search/SKILL.md) | 用户丢图且没有可用标题/番号时。二次元：onegai.moe → soutubot.moe → Lens → Yandex → SauceNAO → trace.moe → ascii2d |
| [`jav-bangou-lookup-fc2`](jav-bangou-lookup-fc2/SKILL.md) | 查 JAV/FC2 番号、女优、核对 JavDB 或 FC2 官网 |
| [`acg-magnet-torrent-search`](acg-magnet-torrent-search/SKILL.md) | 搜磁力/种子/BT。Router 默认只给三次元自动走；二次元搜图闭环不要调用，除非用户事后明确要磁力 |

四个 skill 互相引用，请**全部安装**。日常丢图搜资源时优先启用 **ACG resource search router**。

三次元资料/磁力还会调用本机 `javdb` 命令。CLI 本身不在本仓库，见 [javdb-cli 配置](#1-javdb-cli三次元强烈建议)。

## 流水线

```
抽出文字线索 + 判定二次元 / 三次元

有标题 / 番号 / 卖家 / 站点 / 分集？
  是 → 网页检索（HTTP 优先）
         命中 → 二次元结束（无磁链）
                三次元 → 资料/官网核对 → 用户要磁力才搜磁
         未命中且有图 → 反向搜图
  否，仅有图 → 反向搜图
```

浏览器：**整个任务只允许 1 次 `new_tab`**，之后用 `goto_url`；读完就走；同时最多 3 个标签。禁止循环开新标签。

---

## 安装

把四个文件夹整目录复制到 skills 根下，保持「一 skill 一文件夹 + `SKILL.md`」。

### Hermes

官方默认目录是 `~/.hermes/skills/`。若你改过 `HERMES_HOME`（例如 Windows 上的 `F:\Hermes`），则复制到 `$HERMES_HOME/skills/`。

```bash
git clone https://github.com/843630162/hermes-acg-skills.git
```

```text
# 最终应类似
<HERMES_HOME>/skills/acg-resource-search-router/SKILL.md
<HERMES_HOME>/skills/acg-reverse-image-search/SKILL.md
<HERMES_HOME>/skills/jav-bangou-lookup-fc2/SKILL.md
<HERMES_HOME>/skills/acg-magnet-torrent-search/SKILL.md
```

也可以按文件安装（社区源可能被安全扫描拦截，预览后再加 `--force`）：

```bash
hermes skills inspect https://raw.githubusercontent.com/843630162/hermes-acg-skills/main/acg-resource-search-router/SKILL.md
hermes skills install https://raw.githubusercontent.com/843630162/hermes-acg-skills/main/acg-resource-search-router/SKILL.md
hermes skills install https://raw.githubusercontent.com/843630162/hermes-acg-skills/main/acg-reverse-image-search/SKILL.md
hermes skills install https://raw.githubusercontent.com/843630162/hermes-acg-skills/main/jav-bangou-lookup-fc2/SKILL.md
hermes skills install https://raw.githubusercontent.com/843630162/hermes-acg-skills/main/acg-magnet-torrent-search/SKILL.md
```

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
| 真实作品号 | 输出示例里的具体 `FC2-PPV-…` | 用占位符 `{id}`；真实番号只出现在你自己的对话里 |
| 「已经登录过」 | JAVHouse 等站点的本机登录状态 | 见下方浏览器登录 |
| 搜索后端细节 | 某次环境里的 Exa keyless 失败写法 | 按你的 Hermes `web.backend` / API Key 配置 |
| 本机路径、Cookie、token | 未收录 | **永远不要**写进 `SKILL.md` 或提交到 git |

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
- **Google Lens**：若出现「图片未与账号关联」，在持久化浏览器里登录 Google 后再试；不要去操作页内 Gemini /「询问这张图片」。失败就记一笔，进入下一引擎。
- 部分引擎在国内可能需要系统代理；代理账号同样只放系统或 Hermes 环境，不放 skill。

### 5. FC2 官网核对

FC2 商品页主机固定为 `https://adult.contents.fc2.com/article/{id}/`。用 `curl` 直链即可，`/search/?q=` 可能跳登录。

官网返回「商品見つかりません」只说明**当前会话/地区看不到**，不能单独否决番号。对照方法写在 `jav-bangou-lookup-fc2` 里：再 curl 一个已知在售的近邻 ID，区分「下架」与「地区限制」。

不需要 FC2 账号也能做资料对比；有账号也不要把 Cookie 提交到 git。

### 6. 不要提交的文件

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

[MIT](LICENSE)
