# 网盘签名链接过期后重新拿文件（116pan 系）

适用：用户的 116pan 签名链接（`pt-n2.116pan.xyz/<上传日期>/<hash>.<ext>?sig=…&expires=…&dlname=…`）403 `Link expired.`，文件还在盘上，要重新拿到下载链接或文件本体。用户不想注册账号时全程走游客视角。

核心：116pan `/f/<12位分享码>` 分享页对游客公开；「普通下载」是走 API 用验证码换一条新签名链（约 2 小时有效）。**任务 = 找到该文件的 /f/ 分享码。**

## 116pan 机制（实测）

1. 分享页 `https://www.116pan.xyz/f/<code>` 游客可见；文件名/大小/上传者/权限在 HTML 的 Inertia `data-page` JSON 里。curl 会被 CF 挡，用浏览器开（Inertia 数据直接读 DOM）。
2. 下载 API：`POST https://www.116pan.xyz/f/<code>/generate-download`，JSON body `{"type":"normal","captcha":"<验证码文字>"}` → `{success, download_url, is_repeated}`。`download_url` 即 pt-n2 新签名链（约 2 小时有效）。
3. 验证码图：`GET /captcha/18?<ts>`；用本机 ninfer vision 或 vision_analyze 读字。
4. 游客「普通下载」：每天限次（页面标 10 次）+ 限速约 10KB/s；「无限速」要 VIP/登录。大文件（数百 MB）游客限速下要十几小时——**交付新签名链给用户自下**，或让用户登 VIP，不要自己慢慢拉。
5. 没有公开搜索 API：`/api/search`、`/api/files`、`/search` 等全 404；公开文件列表页也没有（`/files`、`/share/list`、`/sitemap.xml` 均 404，robots `Disallow: /`）。首页「BT搜索」只是外链 maghub.org。
6. 前端下载逻辑在文件页懒加载 chunk（`Show-*.js`）里，`app-*.js` 只有 locale API——找 API 时拉文件页实际加载的 chunk，别只 grep app.js。

## 去哪里找 /f/ 分享码（各源实测状态）

- **4k2 游客搜索**：只匹配标题；时间窗参数 `srchfrom=<秒>`（6 月=15552000）；高级搜索页对游客会重定向；旧帖可能不在索引里。
- **杏吧（sex8.cc 及镜像）**：游客看得到正文，但载点常在**附件**里，游客下附件要登录。
- **weizhongchou.cn**：站内搜索 `/s.html?q=` 可用，但下载区 VIP 付费。
- **tgstat**：频道 post 页公开（正文 + ttttt.me「Open in Telegram」链接），但**评论区不公开**；全站 post 搜索要登录。资源常被放评论区 → 游客视角基本拿不到。
- **t.me**：`t.me/s/<channel>` 公开预览经常被关（重定向到 `t.me/<channel>`，点「Preview channel」不跳转 = 关）；ttttt.me 只是 `tg://` 跳转器；web.telegram.org 要登录。游客基本只能看预览开关开着的频道。
- **windfiles.com（WF 盘）**：`/search/all?sch=` 搜索要登录（页面 10 秒后自动跳 `/user/login`）；有直链的话文件页公开。
- **feixueacg**：`feixueacg.com` 301 → `feixueacg.org`（www 子域 404）；游客搜索 = 「游客)无法进行此操作」，只能手工翻板块页。
- **avlang.com**：www 只能走 **http**（https 超时）；游客搜索同样被禁，板块浏览可以。
- **maghub.org**（磁力聚合，偏 AI 短剧/二次元）：首页输入框 → 点「搜尋」按钮（XHR POST `/search` → 跳转 `/search?t=<加密token>`）；直接开 `/search?q=` 显示「搜尋連結已過期」无效。AI 漫画常没收录。
- **老王论坛（`laowang.vip`）**：本机已登录并安装专用 CLI（见 [laowang-cli](laowang-cli) skill），可直接用 `laowang search "<关键词>"` 与 `laowang thread <tid>` 免扣币检索同资源帖、提取网盘链/提取码及自动执行 `jnpar_pansell:check` 验活（付费项默认 dry-run，未经用户明确同意严禁加 `--confirm`）。

全空 → 优先用 `laowang` CLI 查老王论坛（`laowang.vip`），或用用户的其他论坛账号看原帖（账号规则见 SKILL.md「不要做的事」），或让用户自己登录。

## 交付

- 新签名链（约 2 小时有效）发给用户自下；或按限速/额度自己下。
- RAR/7z 解压密码通常写在原帖**明文**区（不需要解锁隐藏内容）——摘密码不需要账号。
- 同帖常挂备源（windfiles 等），一并给出。
