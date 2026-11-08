---
name: web-image-hunt
description: "Use when 用户要网页找特定图（版本特典/宣传图/角色外观）：文字定项、按源抓图、核验裁切交付。"
version: 1.0.0
author: local
license: MIT
platforms: [windows]
metadata:
  hermes:
    tags: [web, images, artwork, media-download, verification]
    related_skills: [acg-resource-search-router, reverse-image-search, twitter-x-toolkit]
---

# 网页特定图搜寻（图找内容，非内容找源）

## When to Use

用户说「帮我找 X 的 Y 图」（游戏版本特典、官方宣传图、角色外观、key art 等），交付目标是一组**可用的图**，不是溯源。判别：用户**给了图**问出处 → reverse-image-search / acg-reverse-image-search；用户**只给文字描述**要图 → 本 skill。

## 流程（按序）

1. **先定内容，再找图**：web_search 中英各一轮（`<标题> <版本/特典词> 特典/奖励/pre-order bonus/deluxe edition`）→ 官方文案（官网、wiki、官方社媒）核对**确切项目清单与官方命名**（中英文名、归属版本、是否独占、效果）。项目名定错，图全白找。
2. **按源优先级抓图**（高=清度高、水印少）：
   - **官网 assets**（首选）：官网 JS 渲染/curl 返 0 字节时 → browser_exec `new_tab(官网)` → `js("document.documentElement.outerHTML")` → regex 出资源路径（常见 `/assets/<dir>/<name>-01-zh-CN.png` 式命名）→ curl 逐个探测变体（序号 `-02/-03`、语言后缀可能 404）：`curl -s -o f -w '%{http_code}' -A "Mozilla/5.0" <url>`，只留 200。
   - **X 帖原图**：`curl https://api.fxtwitter.com/<user>/status/<id>` 免登录，media[].url（pbs.twimg.com，带 `?name=orig`）= 原图（可达 4096px 级）。官方号或高赞第三方帖的特典展示图通常比媒体站干净。
   - **媒体文章图**（备选）：curl 文章 HTML + grep `<img>` 的 src（只取页面真实存在的 URL）。媒体站（gamersky/17173/QQ 新闻等）普遍 550–1024px，且常带水印（频道台标、字幕、站标）。
   - **wiki**（fextralife 等）：缩略图 ≤1000px，只用于核对内容，不交付。
3. **核验（必做，交付前）**：
   - 先 `md5sum` 全部下载件：多文件同尺寸同 md5 = 占位图（CDN 对不存在路径常返同一默认图），整批剔除。
   - vision_analyze 逐张（可并行）核：内容是不是目标项目、有无第三方水印；见到台标/字幕/解说文字即降源，该图不交付或降为参考。
4. **交付**：
   - 落 `<WORK_DIR>/<任务名>/`，中文文件名（内容+归属，如 `豪华版_外观_机械魔躯.jpg`）。
   - 多外观总览图（多角色并排+文字标签）：PIL 按宽度裁出每个外观的独立图（顶部留余量、裁掉标签区），裁完再 vision 复核一遍。
   - 一次性 MEDIA: 编号发出，每张一行说明内容；附特典文字清单（官方名+效果）。
5. **收尾**：删任务 scratch 目录；`process_manage list` 查后台进程并 kill。

## 陷阱

- 官方 assets 目录的图常只是某版本 **key visual**，不是每个外观都有独立官图——具体外观独立图可能只存在于总览裁切或社媒帖；交付时注明每张对应哪个项目，别把 key visual 当全套。
- 游戏内道具类特典（饰品/挂件）通常只有总览图里的**图标**，没有独立立绘：别硬裁图标冒充立绘，文字注明即可。
- 同一天时间戳的媒体图 URL 可能全是同一占位图（gamersky 无前缀 URL 即此症状）；「URL 看着对」≠「图是对的」，md5+vision 双验。
- 媒体转载图多为视频截图（17173/QQ 新闻常见 bilibili 台标+字幕）：vision 发现台标字幕就换源，不交付给用户。
- 裁切总览图时角色可能延伸到原图底边（原图本身脚部出画）：裁切无法补回出画部分，核验时按「头顶完整、无严重偏移」标准接受即可。
