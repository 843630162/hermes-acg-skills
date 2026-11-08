# 日本同人動画（Getchu / としあき系）来源溯源 —— 无番号、通常无磁力

适用：用户丢来的是**拼接长图**（多张封面竖排堆叠、带红色圆形徽章 +「収録時間 N分」+「画像N枚」+ 系列 masthead），实为日本同人サークル的 cosplay ハメ撮り動画/画像集宣传封面，无 JAV 番号。

## 关键判定
- 这类长图**不是**论坛自制图：每一格 = 官方 DVD ジャケット展开图（Getchu `top.jpg`，560×376）里**右半的正面封面**（裁出来正好 ≈236×374 竖幅）被裁切后竖拼。认出这一点就不必把整张长图丢去反搜（整图反搜只会出噪音）。
- **逐格裁开再反搜**：`panel_N.jpg` 用 LANCZOS 放大 4×（原图常只有 200–300px 宽），再 `soutu_http_probe.py yandex --image panel_N.jpg --proxy http://127.0.0.1:10808` → 直接命中 `dl.getchu.com/i/item<7位>`。（实测 1 次命中，整图 5 条全是噪音。）
- 面板上的「59 / 63 / 72」是**収録分数**，不是卷号；`VOLUME 59` 这类读法多为 vision 误读。核对方式：把每格时长与 Getchu 商品页的「動画N分 / 画像N枚」逐一对齐，全中即钉死。
- masthead 的罗马字常与官方标题不同（例：图上像 `KAMIKAGURA`，官方实为 `神 KAMI-UTA 歌`）；以 Getchu 标题为准，别照抄 vision 转写。

## 一次拿到サークル全部作品（比逐格反搜快）
1. 商品页里取 `dojin_circle_detail.php?id=<サークルid>`（例 としあき = 4062）。
2. 抓 `https://dl.getchu.com/search/dojin_circle_detail.php?id=<id>&pageID=1..6`（带 `Referer: https://dl.getchu.com/` + 浏览器 UA；**不带 pageID 时各页返回同一份**）。
3. 编码：`shift_jis` → 失败再 `euc_jp`（`file` 会报 ISO-8859，别据此判断）。正则 `/i/item(\d{7})"[^>]*>([^<]{5,200})` 取 id+标题，按人名/系列词过滤。
4. 商品页取元数据：`<title>`、配信日、`[0-9,]+\s*円`、`動画\s*\d+\s*分`、`画像\s*\d+\s*枚`。

## 预览图（免费、无需登录，可直接交付）
- 封面展开图：`https://dl.getchu.com/data/item_img/<id前5位>/<id>/<id>top.jpg`（560×376）
- 官方样张：同目录 `<id>_<4位序号>.jpg`（1000–1500px，序号从商品页 HTML 里 grep，通常 3 张）
- 交付前按用户固定要求做编号网格（PIL，每格左上黄字 `#<id>`，quality≈87），封面一张 sheet、样张另开 sheet。
- 注意 pansell/付费墙在这边不存在：Getchu 预览全公开，「先给预览再决定买不买」在这类资源上总是做得到。

## 磁力：先用带对照词的管道查 sukebei，再谈「没有」
- 「NO UPLOAD / NO P2P」是サークル的声明，**不等于公开侧没档**：2026-11-06 实测 としあき／藤木紗英 7 部里 5 部在 sukebei 有磁力（サンダーロード 9.8G `d2a07970…`、追憶のマーメイド 12.8G `1e753f25…` / 12.6G `a2a96fa6…`、KAMI-UTA 9.1G `a87943ca…` / 5.2G `2d80524d…`），只是做种接近 0。
- 下「无磁力」结论前必须查一次 sukebei，且必须用对照词验证管道：`python <HERMES_HOME>/skills/acg-magnet-torrent-search/scripts/sukebei_search.py "<日文标题/人名/番号>" --proxy http://127.0.0.1:10808`（内置 MIDE-599 对照 + 搜索框回显校验 + gzip 解压；管道坏时退出码 2）。
- 历史教训（2026-11-06 误判）：`?rss=1&q=` 返回 200 / 0 items 曾被写成「实测全空」，实际是参数被忽略（sukebei 只认 `?q=`）；据此得出的「同人動画一律无磁力」是错的，已撤销。
- 仍无磁力时再走：javdb（无番号时基本无效）、868888 hex、老王 `laowang search`；最后才写「官方预览型」。分发线索看 archiveofsins 求档帖 + 司机社 `xsijishe.net` 求出处帖（回复里常直接贴磁力）。
- 卖端只有官方付费渠道：Getchu（`dl.getchu.com/i/item…`）、FANTIA（`fantia.jp/products/…`，同一作常有「【DL用】」另一条）、XCREAM、駿河屋 DVD（`suruga-ya.jp/product/detail/…`）。

## 卫生
- Getchu 的 `/search/search_list.php?...` 直连 **403**（要 cookie/JS），但 `/i/item*` 与 `dojin_circle_detail.php` 用 curl 直取即可——别在搜索页上耗重试。
- `archiveofsins.com/t/search/text/...` 403；`/t/thread/<id>` 可直取（页面 1–2MB，用 Python 定位关键词 ±1200 字符窗口，别 grep 整页）。
