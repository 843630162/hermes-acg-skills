# 司机社 (xsijishe) — CN 资源/图包论坛，游客绕行

司机社是老王同类 Discuz 站：国内域名 `xsijishe.com`（搜索走 btwaf，curl 直接 403），海外镜像 `xsijishe.net`；裸域 `sijishe.net` 是停放域名（无站）——用户说「sijishe.net」即指司机社，按 xsijishe 系域名走。板块：国产视频 fid=48、求出处、3D动漫 fid=44；货币为「车票」（软妹币同类）。付费帖标题带「（磁力）」或「[售价N 车票]」。

## 游客能力边界
- 搜索要登录：GET `search.php?mod=forum&searchsubmit=yes&terms=<词>` 游客返回「提示信息」空页；`xsijishe.com` 上同请求 403（btwaf）。
- 帖正文对游客多数隐藏（「本内容被作者隐藏」/阅读权限1，或整页变「提示信息」）；`forum.php?mod=viewthread&tid=<tid>&mobile=no` 常只剩版头+表情图。
- 板块列表页对游客不可读：`forum.php?mod=forumdisplay&fid=<fid>` 只返回版头、「New」跳转链和主题分类下拉，没有 threadlist 行——不要指望游客能翻板块列表。
- **求出处板块的旧帖是例外**：`mod=viewthread` 给游客完整标题、发帖时间和回帖正文（含「ai的」「名字找不到」这类结论），OP 的附图也常挂在 `urlimage.cc/attachments/...`，带 `Referer: https://xsijishe.net/` 就能直下。问「这段视频/这张图出处」时先 Google Lens 完全匹配 + `site:xsijishe.net 求出处 <关键词>`，那里往往已经有人问过同一条。
- 已知板块：国产视频 fid=48、3D动漫 fid=44、AI合成视频 fid=37（主题分类是「AI短剧 / 明星名 / 其他、合集」）。
- 结论：要正文/预览必须注册登录；没有账号时不要硬试搜索接口，改走上面的 Google 路径。

## 游客发现路径（实测有效）
1. `web_search "site:xsijishe.net <CN名或别名> <角色/关键词>"`（以及 xsijishe.com）——谷歌有全站索引，标题+日期+摘要足够定位候选 tid。
2. 相关帖子侧栏也会带出同 CN 的其他帖；求出处板块（标题含「求出处」）常有对同一资源的多手讨论，顺藤可找到已解答帖。
3. 汇总站补充：584520.xyz / wantuzhi.com / yuanqxz.com 的合集文常列 CN 名+别名+微博 URL，用来把「一个人名」展开成别名集再回搜。

## 与老王对照
- 老王 pansell 卡锁正文+预览；司机社登录墙同理，游客拿不到预览——预览替代一律走漏站相册（cosplayboobs 按角色名列全 coser 专辑，见 acg-reverse-image-search/references/coser-identity-attribution.md）。
- 同一图包通常两边都有帖：老王 `laowang search "<别名>"` 快于司机社注册；先老王拿链接+价格，司机社仅作为出处讨论/补充源。

## 登录后脚本化抓取（curl_cffi，实测可行）

司机社边缘是 Cloudflare 托管挑战：`curl`/`requests`/urllib 一律 403（返回 `<title></title>` + `window.location.href` 挑战页），**加 UA/Referer 也没用**。可用路径：

1. 真实浏览器登录 `xsijishe.net`（账号与密码只在本机密码库：vault 条目 `<vault-id>`，用 `browser_vault action=list` 查；登录页 `member.php?mod=logging&action=login`，勾 `cookietime` 拿 30 天 cookie）。
2. 用 CDP `Network.getAllCookies` 把 `*xsijishe*` 域的 cookie 导出成 JSON（含 `SgL6_2132_auth` / `_saltkey` / `cf_clearance`）。
3. 脚本用 **curl_cffi**（`impersonate="chrome"`，UA 抄真实 Chrome 版本）+ 这套 cookie 直连，状态 200 且已是登录态；纯 stdlib/requests 不行。
4. 搜索：`GET /search.php?mod=forum&searchsubmit=yes&srchtxt=<词>&srhfid=0&srhlocality=forum::index`，会 302 到 `searchid=` 结果页。翻页用 `&page=N`（`orderby=dateline&ascdesc=desc` 时最新在前）。
5. 当前模板（nex 系列）结果行结构：`li.nexwateritems` → `h3>a`（标题，含 `<strong><font>` 高亮）、`.nex_conbtms span`（作者）、`.nex_conbtms_view` / `.nex_conbtms_reply`、`.nex_update_time`、`.nex_showpics img`（封面）。没有 `li.pbw`，别套默认 Discuz 选择器。
6. 关键词覆盖：`カノジョドリ` 与 `kanojodori` 各搜一次再按 tid 去重（后者能命中「カノ ジョ ドリ」空格写法，命中数明显更多）。两次搜索间隔 ≥8s（flood 控制）。

现成实现：`<HERMES_HOME>/scripts/kanojodori-watch/watch.py`（配合 `<WORK_DIR>/kanojodori-watch/sjs_cookies.json` 与同目录 venv）。cookie 过期后只需重新登录并重导。

**坑**：正常页面也会内联 `window.__CF$cv$params`（CF beacon），拿它判「被挑战」会误判——真挑战页是 `<title></title>` + 不足 8KB + `window.location.href` 跳转脚本。
