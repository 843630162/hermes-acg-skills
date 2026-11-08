---
name: JAV bangou lookup FC2
description: 用户查 JAV/FC2 番号、女优、要核对 javdb 或 FC2 官网时使用。JavDB 优先走 javdb-cli；有标题/分集/站点名时先网页检索和 HTTP 核对，不要先识图。官网「未找到」不能单独否决番号。
---
# 番号 / JAV 资料检索（含 FC2 官网对比）

用户给出 **番号、女优名、FC2 作品号、标题+分集、截图要识番号**，或要对比资料站 vs 官网时使用。默认做 **元数据与官网核对**，不是一键找盗版。

有 **标题 / 卖家 / 站点名 / 分集后缀** 时：网页检索优先于识图。对标有效做法：搜索出候选 → 镜像标题钉死 → TM 时长/分集排除混淆项 → 官网仅作参考。

## 安全

- 假定用户已成年；疑似未成年则拒绝。
- 区分：官方售卖页、资料库、第三方索引、磁力站。默认先资料+官网；用户明确要磁链再转磁力 skill。

## 免责声明

本 skill **仅供学习与技术参考**。默认做元数据与官网核对，不是一键找盗版。不提供、不保证任何资源的合法性或可用性；使用者须自行遵守所在地法律与站点条款。

## 浏览器卫生

- 优先 `curl` 拉 `article/{id}`、JavDB 条目、镜像 HTML。
- 必须浏览：1 次 `new_tab`，之后 `goto_url`。翻页不要 `new_tab`。读完关掉或跳走。同时最多 3 标签。

## 先抽出线索

1. 番号：
   - `ABC-123` / `ABCD-123`（统一大写+连字符）；`ABC123` → 试 `ABC-123`
   - FC2：`FC2-PPV-1234567` / `fc2 ppv 1234567` / 6–7 位数字 → `FC2-PPV-{数字}`
   - `HEYZO`、`1pondo`、`Caribbean` 等保留前缀
2. 标题、分集：`…15` 与 `15,5` / `15.5` **不是同一部**。
3. 站点（TokyoMotion 等）、卖家。
4. **只有图、没有任何标题/番号** → 才交识图（avscan.cc / whos.tv / xslist）。有标题时识图最多当旁证。

## 有标题时怎么找番号（先于识图）

1. 网页搜索标题变体：`{标题} FC2-PPV`、卖家、`{标题} {分集}`。`web_search` 失败就 curl 搜索页 HTML。
2. 对每个候选 ID HTTP GET：`https://adult.contents.fc2.com/article/{id}/`。
   - 「商品見つかりません」= 官网不可见，**不是**「这个号不存在」。
   - `/search/?q=` 可能跳登录，优先直链。
3. 镜像/资料页若同一行写着 `FC2 PPV {id} {完整标题含分集}` → 标题字符串钉死。
4. 用户给了 TokyoMotion：站内搜同系列；用独立页和时长区分 `15` vs `15,5`。
5. 图搜（whos.tv 等）乱出别的号 → **丢弃**，以标题+分集为准。

## 社交评论区路线（Threads / X / 社区串帖）

用户给播放器截图、社区帖子链接，或说「有人在 Threads/X 求番号」时，先走这条便宜路径再开重型搜图：

1. **找原串**：`web_search` 图里的特征字符串（平台名+目录 ID、OCR 得到的文字，如 `"Sonka" "11826045"`）。转发帖会链回原贴；原贴评论多、质量高。
2. **Threads 每条回复都是独立帖子 URL**（`threads.com/@user/post/<id>`）：串页被登录墙挡住时，对单条回复 URL `web_extract` 仍能拿到完整文本（串页只露前几条）。高赞回复大概率是番号答案；收集所有候选号逐个用 JavDB 核对。
3. **X/Twitter**：回复同样有独立 URL；不登录可用 fxtwitter/vxtwitter（`api.fxtwitter.com/<user>/status/<id>`）拿回复内容。
4. **X 引流号（MyFans / CandFans 分销帖）定源**：日本引流号常配虚构/AI 合成的「某网红/啦啦队/YouTuber 下海」对比图，并在自评里发 `調べたらマジでデビューしてた👇` + 推广短链（如 `mfco.link/r/...`）。不要拿伪造的左图去反向搜图：
   - 用 `twitter user-posts @<handle> --json` 或 `twitter tweet <url> --json` 取推主自评里的短链；
   - `curl -sIL` 跟 302 跳转（如 `https://myfans.jp/posts/<uuid>?aff=...`）直接拿到真实作品 UUID；
   - GET 该 MyFans 帖子 HTML 解析 `<script id="__NEXT_DATA__">`（`props.pageProps.metadata` 的 `og_title`、`og_description`、`og_image_url`），或检索汇总站 `fanfind.jp/myfans-<creator>-<uuid>/`，一次锁定真实创作者、出镜女主 MyFans 主页（`myfans.jp/<handle>`）、完整时长与定价。
5. 评论区答案是隐藏/编码形式（叙事文本、房间号/路线数据）→ 先调一次 `skills_list`，用 [jav-number-decode](jav-number-decode) 解码提取评论里的所有番号再核对。
6. 评论区得到的番号必须经 JavDB/资料站交叉验证后才能定锤——点赞多不等于对（实测有 AI 片被多人误认成 FC2）。

## 文件输出纪律（Windows）

- curl / 下载临时文件一律放非系统盘：`<HERMES_HOME>/cache/scratch` 最佳；不要写 C: 或 `%TEMP%`。

下架判定：article 显示未找到时，再 curl 一个已知在售的近邻 ID。近邻能开、目标不能 → 目标下架；两个都不能 → 地区/会话限制，不要写「已下架」。

## 资料站

能并行则并行：

1. **JavDB（优先 javdb-cli）** — 二进制可用时不要开网页条目页，直接：
   - `javdb search <标题/番号> --json` 拿候选（含 series/actor/maker 维度）；
   - `javdb detail <规范化番号> --json` 取元数据（标题、演员、时长、厂牌、发行日、系列 ID）；
   - 执行前按 [javdb-cli](javdb-cli) skill 用 `javdb <command> --help` 核对参数。
   CLI 缺失/失败才降级打开网页 `https://javdb.com/`，并在输出注明。标题常被打码，要用分集后缀对齐。
2. 其它 jav 库；女优脸 `https://xslist.org/zh`
3. 仅无标题时的识图：avscan.cc → whos.tv

## FC2 官网对比（FC2 必做）

1. 官网主机仅 `https://adult.contents.fc2.com/`
2. 商品页：`https://adult.contents.fc2.com/article/{id}/`
3. 摘：标题、卖家、价格、状态、时长、是否下架
4. 与 JavDB 对比：标题（含机翻）、时长、封面是否同一作品、是否错号
5. 输出一节 **官网 vs 资料站**：一致 / 冲突 / 官网下架资料站仍挂 / 仅一方有。冲突以官网为准（若官网可见）。
6. 核对最终搜索结果时可用这些站点做预览/图片对比——FC2 官方 embed（`adult.contents.fc2.com/embed/<纯数字>`）、moodyz.com、`https://video.dmm.co.jp/av/`（官方付费，DMM 有年龄确认门槛）——用于身份核验（番号/标题是否一致）；但不要把它们当在线视频或磁力来源：官方预览型作品无需在这些站搜索。

非 FC2：用户要官网对比再查 DMM/FANZA 等。

## 预览图 / 封面（用户要「预览图」时的标准做法）

**先走官方图源，不要直接把 JavDB 的图 URL 丢给用户或 PIL。**

1. **DMM 官方图床（首选，未加密、分辨率最高）**：<code> = 番号前缀小写 + 数字补零到 **5 位**（`SNOS-424` → `snos00424`）。
   - 封面：`https://pics.dmm.co.jp/digital/video/<code>/<code>pl.jpg`
   - 剧照：`https://pics.dmm.co.jp/digital/video/<code>/<code>jp-1.jpg`、`jp-2.jpg` …
   - 只接受补零 5 位形式；`snos424` / `1snos00424` 会返回 **405**，别据此判定「没有图」。
   - 官方封面是**整幅 DVD 封套（正面+背面展开）**，放拼图第一格信息量最大。
2. **`tp.spfcas.com`（JavDB CDN）的图是加密的**：文件首字节是 **XOR 密钥**，其余字节全部与之异或。直接 `Image.open` 会抛 `UnidentifiedImageError`，而返回的是 200 + 正常 JPEG 体积，**看起来像成功下载**。解码：
   ```python
   data = open(p,'rb').read()
   if data[:2] != b'\xff\xd8':      # 不是 JPEG 头
       k = data[0]
       open(p,'wb').write(bytes(b ^ k for b in data[1:]))
   ```
   校验办法：同一张官方封面从 DMM 直取比 JavDB 版**正好小 1 字节**（就是那个密钥字节）。此规则适用于 `cover_url`、`thumb_url`、`preview_images[].large_url` 全部字段。
3. **剧照张数不要照抄 `preview_images` 长度**：DMM 样张常少于 JavDB 列出的数量，末尾可能返回一张灰白 **「NOW PRINTING」占位图**（200 + 真图）。逐张判：`mean > 200 且 std < 25` → 占位图，丢弃。
4. **拼图交付格式**：默认 **4 列**，深色底（如 `#16161a`），每格按行高**垂直居中**（横竖画幅混杂时否则错位）。16:9 剧照用 2 列会拼成极端竖长条，在 QQ/Telegram 里被压成缩略细条没法看。
5. **发之前必须 `vision_analyze` 过一遍成品拼图**：同时查两件事 ——（a）有无占位图/破图/空白格；（b）顺序与身份是否对得上（封面、同片连续剧照）。这一步实测抓到过占位图，也确认了剧情顺序，比肉眼信任脚本可靠。
6. 现成脚本：`scripts/preview_grid.py <番号> --out <交付目录>`，自动走 DMM → 失败降级 JavDB（含 XOR 解码）→ 出拼图。

## FC2 批量「磁力 + 预览图」（2026-11 实测，10 号一批）

- **JavDB 覆盖不全**：部分 FC2 号 `javdb search` 直接返回 `{"movies":[]}`、`javdb detail` 无数据 → 不能据此判定番号不存在。这批里 2/10 只有第三方源有。
- **FC2 官网 article 会 410/404**（限定販売结束就整页消失，连卖家页也空）→ 官网不可见 ≠ 号不存在，也拿不到官方预览图。
- **磁力兜底 = sukebei 网页直查**（`https://sukebei.nyaa.si/?q=FC2-PPV-<id>`），它把这 10 号全部命中（含 JavDB 完全没有的 2 号），一条 = 原盘 MP4（2–11 GiB）+ 若干 `[H265 1080p]` 压制版（400 MiB–1.2 GiB）。用 `scripts/sukebei_search.py <id...>`，它输出 size/seeds/leechers/downloads + 完整 magnet URI；选型规则：seeds>0 优先，其次 downloads 最大，并同时给「原盘」与「H265 小容量」两条。
- **sukebei 抓取两个假阴性坑**（踩过）：① 不要发 `Accept-Encoding: gzip` —— urllib 不解压，body 是 gzip 字节，所有正则零命中，看起来像「站里没货」；② 行 markup 现在是 `<tr class="default">`，旧 `<tr class='torrentrow'>` 零命中。单元格**按内容识别**（日期正则 / `[\d.]+ (MiB|GiB)` / 剩余整数 = seeds,leechers,downloads），列序会因多出的标记列偏移，按位置取会张冠李戴。
- **FC2 无 JavDB 条目时的预览图降级链**：`jav.sb/ja/jav/fc2-ppv-<id>-1-1.html` 里的 `img.18av.mov/img/<n>/1..7.jpg` 是**真剧照**（带 SUPJAV/OUTDOORcom 水印，可用），配该页 og:image 的镜像封面 `pics.pornfhd.com/storage*/file/<3位>/<fileid>/...png`（200 可直取，无防盗链）。
- **别用的源**：`fc2tube.com/wp-content/uploads/...`（og:image 里的图会被清掉 → 404，直连和走代理都 404）；`onejav.com`、`supjav.com` 对 curl 恒 403（带本地 10808 代理也 403）；`eporner` 的 `imggen.eporner.com/<id>/640/360/<n>.jpg` 返回 200 但 body 0 字节；`shirouto-kantei.com/works/fc2-<id>/`、`18av.mov/search.php` 分别 404 / 连不上。最新号（发售 <3 月）常常**只有封面没有任何剧照**，直接交付单张封面并说明原因，不要硬凑。

## 番号不存在的判定与假阳性（2026-11 实测，MIDE-999）

- **`javdb detail <不存在的番号>` 会静默模糊回退**：`MIDE-999` 返回的是 `MIDD-999`（字段 `number` 变了）。**必须核对返回 JSON 的 `number` 是否与输入一致**；不一致 = 该号没有收录，不能拿回退结果当命中。批量探测 MIDE-995~999 全是 MIDD-995~999 的回退。
- **厂牌番号线会整段终止**：MOODYZ 的 `MIDE` 到 **MIDE-994（2021-11-02，991~994 同日一批）结束**，之后改走 `MIDV`。用户给「MIDE-9xx」而 9xx>994 时，先按「同数字的 MIDV/MIDD」和「该线最后一号」两个方向给候选，别硬找。
- **AI 洗稿资讯站会编造番号**（buz.wpx.jp、japhub 等）：它们写的「MIDE-999 ＝ 葵いぶきと中出し温泉旅行 / 50人ごっくん」这类条目，用 `javdb search <标题>` 搜不到对应作品 → 番号是生成的假号。web_search 命中这类站不能证明番号存在，必须有 DB 精确命中或磁力/官网命中。
- 交叉验证的最低成本组合：`javdb detail`（看 number 是否回退）+ `sukebei_search.py <番号>`（**先过对照词再判零**；对照通过后的 0 行才是「无该号资源」）+ `av-wiki.net/<去连字符号>`（404）。带对照/回显校验的新版见 `acg-magnet-torrent-search/scripts/sukebei_search.py`。

## 与磁力

- 只要「这是什么片」→ 元数据 + 官网对比，**不附磁链**。
- 明确要磁力 → **第一步 javdb-cli**：`javdb magnets <番号>`（无需登录）或 `javdb search <番号> --magnets N`；用户只要一条最优加 `--best`，指定中字/HD 加 `--cnsub`/`--hd`。JavDB 拿到结果即可交付，但用户要中字或破解版时按 [ACG magnet torrent search](acg-magnet-torrent-search) 的「变体覆盖」再补查一次 sukebei——JavDB 常只给同源 rip，中字版往往只在 sukebei。
- JavDB 磁力不足或 CLI 不可用 → 兜底 [ACG magnet torrent search](acg-magnet-torrent-search)（sukebei → OneJAV → JAVHouse），输出注明已降级及原因。
- JavDB/第三方磁链一律标「非官方源」。

## 执行步骤

1. 抽出文字线索；有标题走「有标题时怎么找番号」。
2. 规范化番号。
3. JavDB 元数据：优先 javdb-cli（`search`/`detail --json`），不可用再开网页并注明。
4. FC2 → 必查 article 直链并对比。
5. 冲突标注，不要悄悄覆盖。
6. 用户没提磁力就不要展开。

## 输出格式

1. **规范化番号**
2. **元数据**：标题、演员、时长、厂牌/卖家、发行日
3. **对齐证据**：镜像标题行、TM 分集/时长（若有）
4. **链接**：JavDB；FC2 article URL
5. **官网对比表**
6. **状态**：在售 / 下架 / 仅资料站 / 不确定

## 不要做的事

- 不要有 TM 标题还先开一串识图标签页。
- javdb-cli 可用时不要绕开它直接翻 JavDB 网页；降级到网页须注明原因。
- 不要把第三方镜当 FC2 官网。
- 不要编造 article id。
- 不要把 `…15` 当成 `15,5`。
- 不要用低置信图搜号覆盖标题钉死的号。
- 不要在只要资料时刷盗版在线站。
- 不要在有社交串帖线索（平台名+ID、原串链接）时跳过评论区直接开搜图——评论区常有现成番号答案，成本最低。
