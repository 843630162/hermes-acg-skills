---
name: pixiv-image-download
description: Use when 用户要抓/下 Pixiv 图片（原图、动转 GIF）。CLI 在 pixiv-cli 目录。
---

# Pixiv 抓图 CLI

用户要「下载 Pixiv 图片 / 抓原图 / 动图转 GIF / 按画师归档」时用这套。已有现成 CLI：`<HERMES_HOME>/tools/pixiv-cli/pixiv.py`（单文件，~670 行），venv 在同目录 `.venv/Scripts/python.exe`（Linux/macOS 为 `.venv/bin/python3`）。

## 方案选型结论（为什么不用现成库）
- **主库**：`upbit/pixivpy`（PyPI: `pixivpy3`，2.1k★，v3.7.x）。只封装 API 调用，不含下载/动图逻辑——所以自己包一层 CLI。
- **认证**：`eggplants/get-pixivpy-token`（PyPI: `gppt`）活跃维护。Pixiv 旧 iOS OAuth 端点 `accounts.pixiv.net/api/oauth/authorize` 已 404，新流程是 **android client + PKCE(S256)**：登录页 `https://app-api.pixiv.net/web/v1/login?code_challenge=<S256>&code_challenge_method=S256&client=pixiv-android`，client_id=`MOBrBDS8blbauoSck0ZfDbtuzpyT`。code 藏在登录后的一次性 `pixiv://` deep-link 里，手动抓很脆——**用 gppt 的 Playwright 可见窗口自动抓 code 换 token**（见下）。
- 没有维护良好的「一键批量下载 CLI」开源项目；包一层是最务实路径。

## 用法
```bash
cd <HERMES_HOME>/tools/pixiv-cli
PY=./.venv/Scripts/python.exe
$PY pixiv.py whoami                      # 验证 token
$PY pixiv.py ranking week -n 4 --download   # 榜单前 N + 下原图
$PY pixiv.py search "初音ミク" -n 3          # 标签搜索（列出 id）
$PY pixiv.py illust <id...> --download      # 指定作品下载
$PY pixiv.py user <uid> -n 10 --download    # 某画师最近 N 张
```
输出默认存 `<WORK_DIR>/pixiv-downloads`，按 `画师/标题_编号/{id}_{页}.jpg|page_N.gif` 归档；每目录附 `meta.json`（标签、作者、URL）。

## R-18 / 关注列表搜图（App API 没有 r18 参数）
`illust_ranking(mode)` 与 `search_illust()` 都**不接受 r18/content kwarg**（传了直接 TypeError），榜单默认全年龄。找 R-18：
1. **关注列表路线**（用户说"从我关注的里挑"时用）：`api.user_following(uid, restrict="public")`，响应字段名是 **`user_previews` 不是 `users`**；每个 preview 自带该用户近期作品（`.illusts`），条目带 **`x_restrict`**（True=R-18）+ tags + total_bookmarks——直接扫 feed 筛 R-18，不用逐张 detail。注意 `user_detail` 的 `following_users_count` 可能为 None，以 len(user_previews) 为准。
2. **关键词路线**：`search_illust(word="巨乳"/"下着", sort="popular_desc")`（无 r18 kwarg），detail 里看 tags/x_restrict 确认 R-18。
3. 「给我看看几张」时挑 total_bookmarks 高 + type!=ugoira（动图）+ 页数少的；多页本子/长条漫画不适合一次发。

## Token 刷新坑
- **别手搓 refresh**：只带 client_id POST `oauth.secure.pixiv.net/auth/token` 会 400 invalid_grant（"client credentials are invalid"，缺 client_secret）。直接跑 `pixiv.py whoami`，它走 load_tokens() 自动刷——可靠路径。
- **网络抖**：DNS 通但 TCP 间歇超时（WinError 10060），几分钟内自愈；别重新登录，等一会重试 whoami。user_* 端点偶发报 invalid_grant 而 ranking/detail 正常时，重刷 token 后恢复。

## 认证（token 过期时，access_token 仅 1h，refresh_token 自动续）
```bash
cd <HERMES_HOME>/tools/pixiv-cli && rm -f .tokens.json
./.venv/Scripts/python.exe _gppt_login.py   # 弹 Playwright Chromium 窗口
```
让用户在那个**新窗口**里登录，登到「此账号正在登录中 / 继续使用此账号」时点**「继续使用此账号」**。脚本自动抓 code、换 token、写 `.tokens.json`（含 user_id/name）。跑完可关窗。
- 注意：先别关那个 Playwright 窗口；Hermes 自带 Chrome 里登录的 session 不能直接复用（code 在 deep-link，浏览器 fetch 拿不到）。

## 关键坑（都已修进 pixiv.py，改代码时别踩回去）
1. **pximg CDN 要带 App UA + Referer**：`User-Agent: PixivIOSApp/7.13.3 (iOS 14.6; iPhone13,2)` + `Referer: https://www.pixiv.net/artworks/<id>`，否则原图 403。统一走 `_http_get(url, referer)`。
2. **字段是 snake_case**（`image_urls`/`meta_single_page`），但 pixivpy3 的 JsonDict `__getattr__` 永不抛异常 → 用 `_g(obj,*names)` 多拼写取值，别靠 hasattr/getattr。
3. **detail 返回结构**：`illust_detail(id)` 顶层是 `{illust, ...}`；单页原图在 `illust.meta_single_page.original_image_urls`(list) / `.original_image_url`(str)；多页在各 `meta_pages[i].image_urls.large`。原图 URL 规整见 `_norm_orig_url`（去 `/pixiv_zh/`、`square120x120_`，域名 `pi-cdn`→`img`）。
4. **动图(ugoira)判定**：`type=="ugoira"` 或 `meta_single_page.original_image_url` 含 `_ugoira`。**别**只看「有没有 original_image_url」（静态单页也有 → 会误判成动图去当 zip 下）。
5. **动图帧数据在 `api.ugoira_metadata(id)`**：返回 `ugoira_metadata.zip_urls`(如 `{medium: url}`，多页时 value 是 list) + `frames`(`[{file,delay}]`)。zip 下载后按 frames 合成 GIF（Pillow）。若 `original_image_url` 指向的是封面 jpg 而非 zip（前 2 字节非 `PK`），直接存图兜底。
6. **App API search/ranking/detail 都需 token**，无 token 返回 400。先确保 `.tokens.json` 存在。

## 验证下载是否真成功
下完用 Pillow 打开确认：静态原图应是 1200px 级大尺寸（非缩略），动图 `page_*.gif` 的 `im.n_frames>1`。只写了 meta.json、没有图片文件 = 失败。

## 拼图预览交付坑
- **遮挡**：按固定高度缩放各图 → 宽度溢出格子压到相邻格。每格独立画布 + contain-fit `s=min(cell_w/img.w, cell_h/img.h)` 居中。
- **CJK 字体**：PIL 默认字体渲染中日文全是星号/方框 → `ImageFont.truetype("C:/Windows/Fonts/msyh.ttc",26)`（fallback simhei.ttf）。纯 emoji 标题渲成豆腐块 → regex 剔掉非文字符号显示 `(untitled)`。
- **PIL 解释器**：系统 python 没有 PIL（ModuleNotFoundError）→ 用 `<HERMES_HOME>/hermes-agent/venv\Scripts\python.exe` 或 pixiv-cli 的 `.venv`。terminal heredoc 里引用 >1MiB 文件（如 msyh.ttc）会被 lifecycle guard 拦 → 先 write_file 写成脚本再跑。

## 收尾
任务做完删掉过程文件（probe/原始 dump/log、_mkgrid.py 这类拼图脚本），保留 `pixiv.py`、`.venv`、`.tokens.json`、下载目录与总结。工作目录在 <WORK_DIR>，易堆垃圾。
