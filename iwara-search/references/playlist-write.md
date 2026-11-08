# Iwara 歌单写入（登录态 API，2026-10-11 实测）

搜索/挖掘任务保持只读；仅当用户明确要求建单/加片/移除时用本流程。

## 认证（两步）

- 第1步 登录：POST `https://api.iwara.tv/user/login`，Content-Type: application/json，body `{"email": "<用户名或邮箱>", "password": "<vault 里的密码>"}` → 200 返回 `{"token": "<JWT，约236字符>"}`
- 第2步 换 accessToken：POST `https://api.iwara.tv/user/token`，Header `Authorization: Bearer <第1步返回的 token>`，body `{}` → 200 返回 `{"accessToken": "<约 279 字符>"}`
- 之后所有写操作用 Header `Authorization: Bearer <accessToken>`；把第1步的 token 直接写接口会 400 `{"message":"errors.invalidToken"}`。

## 端点（全部实测）

- 建歌单：POST `https://api.iwara.tv/playlists`，body `{"title": "..."}` → 201（注意复数 playlists；/playlist 单数建单 404）
- 加片：POST `https://api.iwara.tv/playlist/{playlistId}/{videoId}` → 204（无 body）
- 移除片：DELETE 同路径 → 204
- 删歌单：DELETE `https://api.iwara.tv/playlist/{playlistId}` → 204
- 读歌单：GET `https://api.iwara.tv/playlist/{playlistId}?page=N&limit=32` → 200（playlist.numVideos + results[]，results 项的 id 就是 videoId）
- 查视频在哪些歌单：GET `https://api.iwara.tv/light/playlists?id={videoId}`
- videoId = 视频页 URL 里的短 ID（形如 mJTf3zDkyRBuHx），不是 UUID。

## 执行环境（绕 CF）

- 写接口需要登录态且必须浏览器语境过 CF；agent 自带 Chrome 会卡在 CF 挑战页，勿用。
- 标准做法：Camoufox（turnstile-bypass skill 的 venv：`<HERMES_HOME>\skills\web\turnstile-bypass\.venv\Scripts\python.exe`），`Camoufox(headless=False, humanize=True, os="windows", i_know_what_im_doing=True)`；先打开 https://www.iwara.tv/ 让 CF auto-pass（等约6秒），再在 page.evaluate 里 fetch：
  ```js
  fetch('https://api.iwara.tv/playlist/'+pl+'/'+vid, {method:'POST', credentials:'include', headers:{'Authorization':'Bearer '+acc}})
  ```
- 一个页面会话可连续跑 N 个 fetch；批量时在 evaluate 里用 async worker 队列（给定批次数组+并发数，返回逐条 {vid,status} 结果）。
- 全新 Camoufox 会话 localStorage 里没有 token，直接走上面两步 API 登录即可，不必浏览器 UI 登录。

## 批量与限流（实测教训）

- 6 并发 + 每条约120ms 间隔 → 约150条后开始大面积 HTTP 500，继续则 NetworkError（整页断流）。
- 稳妥配速（863条全程无阻断）：并发2、每条间隔约550ms；每批20条；批内失败过半冷却约20s；失败集再单独慢速重试一轮（并发1、约900ms）。
- 结果校验：结束后逐页 GET `/playlist/{playlistId}?page=0..` 拉全量，与目标 ID 集合 diff；不要只信 numVideos（以逐页结果为准）。2026-10-11 实测 863/863、0缺失0多余。

## 歌单缺口：numVideos 与可列出条数不一致（2026-10-11 实测）

- 歌单 `playlist.numVideos` 是**计数器**，会把私密(403)/已删(404)的视频也算进去；列表端点只返回可列出的条。标称 N、实际只能列出 M（N>M）时，缺口 = 私密 + 已删，**不是「不登录才看得到」**。
- 实测：用**作者本人 accessToken** 调 `playlist/{id}`，试遍 `unlisted=1`/`mine=1`/`private=1`/`limit=1000`，返回与匿名完全相同；登录态 SPA 歌单页（localStorage token）5 分钟激进滚动也只发 1 次 playlist 请求、不触发翻页。结论：**登录不解锁额外条目**。
- 定位缺口里的私密条：对可疑 ID 逐条 `GET /video/{id}`（Bearer 作者 accessToken），仍 403 = 私密；404 = 已删。
- 报告写法：把这类条目单列「私密/受限(403)」表（含 ID，供作者日后公开时回查），不要标成「unlisted/不登录看不到」。
- 现成脚本：`../scripts/playlist_gap_audit.py`（turnstile-bypass venv 跑；参数化 playlist/user/password-file/suspect-ids，页内变体探针 + 可疑 ID 逐条 403/404 定性 + 登录态 SPA 滚动交叉验证 + 匿名逐页补全 listed 集合，输出缺口拆解）。通用配方（其他站点改端点即用）见 turnstile-bypass skill 的 `references/page-session.md`。

## UI 备用

- 视频页有 "Add to" 按钮（成人弹层 .adultWarning 先点 "I am over 18"）；下拉勾选=POST、取消=DELETE，与 API 一致。批量仍建议 API。

## 凭证与账号

- vault 内有两条 iwara 登录（主号 + 备用）。账号名、邮箱与 vault id 只写在本机密码库，不进仓库。
- 取用：hermes venv python 跑 `agent.vault_store.VaultStore().resolve_secret('<vault-id>')`；临时凭证文件用完即删，文档中不写密码。

## 端点发现方法（找别的写接口时）

- 下载 `https://www.iwara.tv/main.<hash>.js`，grep 函数名（addToPlaylist / removeFromPlaylist / fetchPlaylist 等）看 URL 拼法与 method，如 `A(e,"playlist/".concat(t,"/").concat(n),{method:"POST"})`。
