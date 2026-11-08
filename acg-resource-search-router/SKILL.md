---
name: ACG resource search router
description: 用户要 Hermes 式资源闭环（有图/关键词搜资源）时使用：先读用户文字再搜网页；一行职员条/太碎纯字图读字搜声优或台词，不要先反向搜图；整屏片尾可文字+以图；有标题/番号也不要先搜图；二次元不搜磁力。用户丢网盘签名链接（116pan/windfiles 等）问是啥/还有效吗时走 ①″（验链+搜 dlname 定身份+预览核实）。只给人名要套图/写真集时走套图路径（meitu.knit.bid 站内搜索→?page=N 分页下载，references/gravure-set-download.md）。
---
# ACG 资源搜索流水线（Router）

给 Hermes / 任意助手用的 **固定闭环**。默认假设用户丢的是 **图或截图相关资源需求**（也可带补充关键词）。

**先读用户已经给的文字，再决定动图。** 标题、番号、站点名、分集后缀、卖家只要有一项能用，就先网页检索；反向搜图是补漏，不是默认第一步。

**一行职员条 / 太碎纯字图：读字 → 当关键词网页搜（职员条搜声优表）。** 不要开 Lens/onegai。整屏 1080p 片尾可以文字定锤、以图碰运气。

第 0 步判定 **二次元 / 三次元**。**只有三次元才跑磁力和 FC2 官网对比。** 二次元认出作品后结束，不搜磁。

## 免责声明

本 skill **仅供学习与技术参考**，不是法律建议，也不提供、不保证任何资源的合法性或可用性。检索结果来自第三方站点；使用者须自行遵守所在地法律与各站条款。疑似未成年内容必须拒绝。不自动开下、不批量打种。

## 否定结论闸门（任何「没有 / 全空 / 查不到」之前，强制）

搜不到不是结论，是待验证的状态。写「没有」之前三条必须同时成立，缺一条只能写「没查成（管道故障）」：

1. **对照**：同一条管道先跑一个已知存在的样本（番号类用 `MIDE-599`，健康时出 19 行 / ~45KB），对照为空 = 管道坏了，不是资源没有。
2. **状态与体量**：记下 HTTP 状态 + 响应字节数。`200` 但 0 字节、或明显小于正常结果页的模板页（十几 KB 的首页壳），一律算失败，不能当「空结果」。
3. **解析自证**：解析器要回读页面里的查询回显（搜索框 `value`、URL 参数、`<title>`）。回显与查询词不一致 = 参数被站点静默忽略，此时解析出的 0 行毫无意义。

同一「没有」结论要至少两个独立源各自过闸（例：官方下架 + 磁力站在对照通过后零命中）。输出里逐源写「状态 / 体量 / 命中数」，让用户看得出哪一条是真空、哪一条是没查成。

**规则来源也是证据**：如果结论是照着 skill 里的一句话下的（「这类默认没有磁力」「X 站一律零命中」），先把那句话拿出来复核——被上一轮写错的规则会稳定复现同一个错误，改 skill 比换模型、调温度有用。

## 总流程（必须按序）

```
第 0 步  抽出文字线索 + 画面类型（二次元 / 三次元 / 不确定）
         + 太碎 / 纯字 / 是否整屏片尾

有可用文字（标题 / 番号 / 卖家 / 站点名 / 分集如 …15）？
  是 → ①′ 网页检索（HTTP 优先，见下方）
         命中番号或作品名 → 跳过反向搜图
           二次元 → ④（无磁链）
           三次元 → 资料核对 →（用户要磁力才）③ → ④
         未命中且有图 → 看「太小/几乎只有字」；否则 ②
否，太碎或删掉字以后没辨识度（一行职员条/字幕横条）？
  是，且不是整屏片尾 → 读字 → ①′ 网页搜（职员条搜声优，台词搜原句；不要搜图）
         命中 → 跳过 ②
         未命中且画面仍有可搜角色/场景 → ②
         无独特字也无可搜视觉 → ④ 说明无法定位，不要空跑 Lens
否，整屏片尾/职员表（720p+） → ①′ 读字网页搜 + 可以 ② 以图碰运气
否，仅有图且有可搜视觉 → ② 反向搜图

② 反向搜图仍空：
  二次元 → AI 鉴定 → ④
  三次元 → ②b FC2 关键词（非「很可能 AI」时）→ 有则资料/磁力，无则鉴定 → ④
```

「不确定」：文字线索仍优先。无文字时先 2D 搜图前两个引擎，空再 3D。两条都空才做 AI 鉴定。

子 skill：

- ①′＋资料 / FC2：[JAV bangou lookup FC2](jav-bangou-lookup-fc2)（三次元标题/番号）
- ② [ACG reverse image search](acg-reverse-image-search)
- ③ 磁力（仅三次元且用户明确要磁力 / 种子 / BT）：第一步 [javdb-cli](javdb-cli)，不足时兜底 [ACG magnet torrent search](acg-magnet-torrent-search)
- 老王论坛无磁力兜底 / 网盘分流检索（四源无可用磁链，或所搜资源含二次元/同人/H游/套图等无磁力链时）：[laowang-cli](laowang-cli)（`laowang search "<关键词>"`、`laowang thread <tid>` 在 `laowang.vip` 检索百度/夸克/PikPak/123pan 网盘链接、种子附件或 `remote_play` 免费在线视频/种子）
- 套图 / 写真集（只给人名要某人的套图，无图无番号）：`references/gravure-set-download.md`（meitu.knit.bid 站内搜索列全套 → `?page=N` 分页下载 → 预览交付）
- 印尼 bokep 文件夹站（用户丢 tribunvideo.com/f/ 等链接问是啥 / 要核实内容）：`bokep-indo-folder-sites`（本机私有 skill，未随仓库发布）（文件夹页 web_extract 列清单 → jwplyr 三跳链拿真实视频 → 抽帧拼编号总图核年龄）
- 社交帖→来源/店铺溯源（X/Bluesky 截图预告新模型/新资源，查 VGen/BOOTH 上架状态；以及 X 视频切片求出处——myfans/裏垢系素人流出：读回复串拿源链接 → 跳转页取真链接 → SPA 的 `__NEXT_DATA__` 取标题 → fans-log 核对时长价格；这类无番号、通常无磁力）：`references/social-post-source-tracing.md`（§5 = 视频切片配方）
- 特定图搜寻（**无图**，用户要版本特典/官方宣传图/角色外观图等一组可交付图）：[web-image-hunt](web-image-hunt)
- 封面拼接长图 / 日本同人動画サークル（Getchu `dojin_circle_detail`、FANTIA、駿河屋 DVD；无番号，サークル常写 NO P2P，但 2026-11-06 实测 としあき/藤木紗英 7 部里 **5 部 sukebei 有磁力**）：`references/getchu-doujin-cosplay-lookup.md`（逐格裁开放大反搜 → item id → サークル一页列全作 → 官方 top.jpg/样张免费预览 → 磁力行必须用带对照词的 sukebei 检索后再定论，**不得直接判无**）；作者允许上传时再查「网盘档/云盘档」——`references/cloud-drive-copy-sweep.md`（先读商品页 NO UPLOAD/NO P2P 判作者态度，再决定是「确认不存在」还是真检索）

## 浏览器与抓取卫生（全程强制）

会话 `fc2-20260912` 在 Edge 上循环 `new_tab` 翻页、从不关掉，导致标签无限堆积、任务走不完。禁止再这样。

1. **静态页优先 HTTP**：`curl` / `web_extract` 拉 HTML。JavDB、FC2 article、镜像标题页、TM 搜索页能 curl 就不要开浏览器。**搜图同理**：先跑 [ACG reverse image search](acg-reverse-image-search) 的 `scripts/soutu_http_probe.py`（Yandex / soutubot / SauceNAO / ascii2d / Safebooru 全部免浏览器），403 撞墙再走 turnstile-bypass + 浏览器。
2. **必须浏览器时**：整个任务 **只允许 1 次** `new_tab(url)`；之后一律 `goto_url(url)`。翻页、换查询、换站点都用 `goto_url`，**禁止 `for` 循环里 `new_tab`**。
3. **读完就走**：摘完标题/番号/时长后立刻 `goto_url` 下一地址，或 `cdp("Target.closeTarget", targetId=...)` 关掉当前页。同时打开的标签不超过 **3**；超出先关已摘完的。
4. **不要操作 Lens / Gemini 页内输入框**（MCP 填不进去会空转）。Lens 只看视觉匹配；上传必须喂 `input[name=encoded_image]`，不要打第一个 `input[type=file]`。做不到就跳过并写明。
5. **web_search 失败**（如 Exa keyless）→ 立刻改 curl/DuckDuckGo HTML，不要为了「搜一下」连开几十个标签。
6. **agent Chrome 实例全机最多 3 个**（主代理 + 所有子代理合计；识别特征：命令行带 `--user-data-dir=<HERMES_HOME>/chrome-profile`）。派并行子代理各开浏览器前，先数现有 agent 实例（`Get-CimInstance Win32_Process -Filter "name='chrome.exe'" | ? CommandLine -like '*chrome-profile*'`），超了先协调/停掉再开。锁住或卡死时**先用父进程链查占用方**是主代理还是哪个子代理，多沟通确认归属再处理；**绝不杀用户日常 Chrome**（不带 `--user-data-dir` 参数的那个）。
7. **CF 墙先于引擎**：搜图链上 onegai / soutubot / SauceNAO / trace.moe / ascii2d / avscan.cc 全在 Cloudflare 边缘，撞「Just a moment」/403+cloudflare 时按 [ACG reverse image search](acg-reverse-image-search) 的「CF 墙应对」走：先查出口 IP（v2rayN/singbox TUN、数据中心 vs 住宅），仍撞再调 turnstile-bypass 的 human_click.py；多引擎同撞 = 出口问题，换节点重跑整链。

## 并行子代理分工（编号/水印线索 + 画面特征同时可用时）

有 IPPA/EPPA 号等厂牌级水印、且画面有明确可搜特征（制服类型、场景、发型等）时，**派两个子代理并行分工**：

- **子代理 A（编号+特征路径）**：IPPA 号 → ippa-member.info 查厂牌组/年代窗口 → `javdb search <画面主题词>` 在目录里命中具体作品；必要时多镜像文字佐证。
- **子代理 B（反搜图路径）**：按 [ACG reverse image search](acg-reverse-image-search) 跑 avscan / Lens / Yandex，只输出候选列表 + 缩略图证据，不拉磁力。

两个都完成后合并交叉验证：同指一部 → 高置信直接定锤；冲突时以编号+特征佐证优先（厂牌级注册号是硬证据），再视觉核验一次后定锤。派并行子代理前按「浏览器与抓取卫生」第 6 条先数现有 agent Chrome 实例（全机最多 3 个）。

## 第 0 步：先用用户文字

从用户消息、文件名、水印 OCR 抽出（有则记下，没有就空着）：

- 番号（`ABC-123` / `FC2-PPV-#######`）
- 作品标题（含日文）
- 分集后缀：`…15` 与 `15,5` / `15.5` **不是同一部**
- 来源站（如 TokyoMotion）、卖家/UP 主
- 网盘签名链接：`dlname=<文件名>` 就是最强文字线索（116pan/windfiles/123pan 系）；URL 日期段 = 上传日期，`expires` 是毫秒 epoch

用户说了「在 TM 上叫 xxx」「应该是 FC2」→ 这就是可用线索，**不要假装没看见去跑 iqdb/Lens 主链**。

图本身也要先看一眼（已附带的视觉描述即可，不必为了分流再开一遍浏览器）。像素是启发式，不是硬阈值：

- **太碎**：最短边 < ~100px，或高度只有几十～一百多的细横条（例：342×83 一行职员条）。读字，不要搜图。
- **纯字图**：删掉字以后没辨识度（没脸/立绘/道具，弱纹理底 + 字）。读字走 ①′。
- **职员条**：「女奴隷　土屋李央」这种 → 搜声优/角色表，不要 SauceNAO。
- **整屏 1080p 片尾**：文字定锤 + 可以顺便以图碰运气。
- 压过的整帧、角色清楚 → 即使文件很小也仍可搜图。
- 细则见 [ACG reverse image search](acg-reverse-image-search) 的「第 0 步前」。

## ①′ 网页检索（有文字时，先于搜图）

三次元标题/FC2（对标已验证能找到番号的做法）：

1. 并行搜标题变体：`{标题} FC2-PPV`、卖家名、`{标题} {分集后缀}`。
2. 摘要里抽出候选 ID 后，**HTTP GET** 官网 `https://adult.contents.fc2.com/article/{id}/`。返回「商品見つかりません」只说明官网不可见，**不能因此否决该号**。
3. 打开把 **标题和番号写在同一行** 的镜像/资料页，用完整标题字符串钉死（含 `…15` 这种后缀）。
4. 用户提到 TokyoMotion：用标题在 TM 交叉；独立页 + 时长区分 `15` 与 `15,5`。
5. 反向搜图若给出别的号，**不得覆盖**「标题字符串 + 分集」已钉死的结论。

二次元有番名/作者名：先网页/Bangumi/VNDB，不要先 SauceNAO。

社交帖截图（X/Twitter/Bluesky，发帖人预告新模型/新作品/新资源）：

- **先答快路径**：帖子的内容 + 原帖链接 + 发帖人身份；然后再追「去哪领 / 怎么领」（店铺上架状态、发布时间窗口）。不要在内容问题还没答完前就默默钻店铺 API 深水区。
- 定原帖：web_search 并行「发帖人 handle（带引号）」+「handle + 主题关键词」两条；X 原帖 `curl https://api.fxtwitter.com/{user}/status/{id}` 免登录直接拿（全文 + 作者 profile 的 website 店铺链接 + 媒体直链，配方细节见 `references/social-post-source-tracing.md`）。
- Bluesky 公共 API（public.api.bsky.app/xrpc 的 getProfile / resolveHandle）对普通 handle 会报 Invalid AT identifier / MethodNotImplemented——别再试 handle 变体，改走 X 侧（fxtwitter）；同帖文案与 X 跨帖一致，直接拿截图文字搜。

命中后：二次元 → ④；三次元 → 按番号 skill 做官网/资料核对；**默认不搜磁**，除非用户明确要磁力。

**IPPA / EPPA 编号水印（画面带 `IPPA No.XXXXXX` / `EPPA No.XXXXXX`）**：

1. IPPA 号是 **厂牌级**注册号，不是作品级——只能定位 **厂牌组 + 年代窗口**，不能直接定到具体哪一部。
2. web_search `IPPA No.<编号> ippa-member` → 打开 `https://ippa-member.info/?p=NNN` 对应页，取厂牌清单（例：ヒロスンエンタテインメント系 = SUN / DANDY / COSMOS PICTURES / ひよこ）+ 注册窗口（例：2022.03–2023.03）。
3. 结合画面特征关键词，用 `javdb search <主题词>` 在该厂牌组对应年代的目录里直接命中具体作品（实测「駅員」一次命中 SUN-080）；也可 `javdb code <前缀>` / `javdb maker <厂牌>` 拉目录后按年代+题材过滤。
4. xsz-av / avjb 等站的搜索页是关键词匹配，拿 IPPA 号搜基本返回噪音（标题含 "No" 的随机视频），不要依赖。
5. 定位到具体番号后 → 交 [JAV bangou lookup FC2](jav-bangou-lookup-fc2) 核对；用户要磁力再走 ③，否则 ④。

## ② 反向搜图（仅无可用文字，或 ①′ 未命中）

按 [ACG reverse image search](acg-reverse-image-search)。不要为了「技能写了要跑前两个引擎」在已经用标题或字幕台词锁定作品之后还开 Lens。图太小/几乎只有字时本步直接跳过。

## ②b FC2 关键词（仅三次元，搜图仍空）

二次元**永不**走。非「很可能 AI 生成」时，用残留关键词搜 `https://adult.contents.fc2.com/`（能直链 article 就不要依赖会跳登录的 `/search/?q=`）。

## ③ 磁力（仅三次元 + 用户明确要）

查询词：`规范化番号` > 日文标题 > 中文译名。最多 5 条。二次元默认跳过。

固定顺序 **javdb-cli → acg-magnet-torrent-search**，不要打乱：

1. **第一步 javdb-cli**（二进制可用时）：
   - 番号已确认：`javdb search <规范化番号> --magnets N` 一次完成搜索、筛选、排序与磁力获取；`--cnsub` / `--hd` 在排序前筛选，N=0 返回全部。
   - 或直接 `javdb magnets <番号>`（无需登录）；用户只要一条最优时加 `--best`，指定中字/HD 加对应 flag。
   - 结果足够 → 直接进 ④，输出注明来源为 JavDB 及所用过滤条件。执行前按 javdb-cli skill 用 `javdb <command> --help` 核对参数。
2. **兜底 [ACG magnet torrent search](acg-magnet-torrent-search)**：javdb-cli 不可用（二进制缺失/执行失败）或 JavDB 磁力不足时，按其三次元索引顺序 sukebei → OneJAV → JAVHouse 继续；输出注明已降级及原因。
3. **四源都无可用磁链**（JavDB → sukebei → OneJAV → JAVHouse）：不要直接下『未找到』结论——按 [ACG magnet torrent search](acg-magnet-torrent-search) 的「无磁力 → 在线视频兜底」执行：用番号/扮演者名/作品名搜在线视频，返回时长 + 预览图 + 链接（标注完整/预览），并附同作品旧号结果（含其磁链）；同时或当所搜资源（含二次元/同人/H游/套图等）无磁力链时，可调用 [laowang-cli](laowang-cli)（命令：`laowang search "<关键词>"`、`laowang thread <tid>`）在老王论坛 (`laowang.vip`) 检索网盘链接（百度/夸克/PikPak/123pan）、种子附件或 `remote_play` 免费在线视频/种子（付费项默认 dry-run，未经用户明确同意严禁加 `--confirm` 扣软妹币）。
4. **官方预览型判定**：作品为 FC2 PPV 或 moodyz.com / video.dmm.co.jp/av/ 等官方付费源、在线渠道最终都跳 FC2 官方 embed（`adult.contents.fc2.com/embed/<纯数字>`，免费约60秒预览）时 → 跳过在线视频搜索与磁力链搜索；这些站点仅在**核对最终搜索结果时**做预览/图片对比（身份核验：番号、标题是否一致）。

## ①″ 网盘签名链接（用户丢链接问「这是啥 / 还有效吗 / 帮我下」）

用户丢网盘签名链接（116pan `pt-n2.116pan.xyz/<上传日期>/<hash>.rar?sig=…&expires=…&dlname=…`、windfiles、123pan 系）时**不走搜图链、不搜磁力**，文字线索优先：

1. **curl（带浏览器 UA）看响应体判别**：`text/plain` 纯文本 = 服务端判定（116pan：`Link expired.` = 链接过期、`Missing signature or expiry.` = 缺签名参数），文件通常还在盘上；HTML + "Just a moment" 才是真 Cloudflare 墙。看到 `Server: cloudflare` 响应头不等于 CF 挑战——应用只是跑在 CF 后面，不要直接上 turnstile-bypass。
2. **解码 `expires`**（毫秒 epoch → 北京时间）对比当前。116pan 签名链接有效期仅约 2 小时，用户丢来「已过期」的往往只是几小时前生成的——结论是「链接过期，需新签名链或回原帖」，不是「文件没了」。
3. **web_search 精确搜 `dlname` 字符串（带引号）** → 命中 Discuz 资源帖（4k2、随性ACG a41415 等），首帖含完整元数据：标题/作者/页数/分辨率/容量/解压密码/预览图，同帖通常还挂 windfiles 等备源。4k2 站内搜索只匹配标题且 10 秒限一次，直接 web_search 文件名更可靠。
4. **预览核实**：论坛图床（imagetwist/imagehaha/s*.域）直 GET 返回 HTML 查看器壳而非图片 → 从 HTML 里 grep `<img src=…>` 拿真实图 URL，下载后 vision_analyze 核实内容与标题一致。
5. 汇报：是啥（标题/作者/规格/密码）+ 链接状态（有效/过期/过期时间点）+ 怎么拿（新签名链 / 原帖 / 备源）。
6. **链接过期但用户要拿回文件**：文件通常还在盘上，只是要新签名。找 `/f/` 分享码（游客可见转载源，或用用户的论坛账号看原帖）→ 分享页 API 生成新签名链，完整机制见 `references/pan-share-link-recovery.md`。不要说「资源死了」。

## ④ 输出

1. **线索**：用了哪些用户文字  
2. **网页检索**（若执行）：候选、镜像标题对齐、TM 时长/分集  
3. **搜图**（若执行）：引擎与证据；跳过 Lens AI。若走了读字幕/网页搜台词，写在这里并注明未搜图  
4. **AI 鉴定**（仅全空时）  
5. **FC2 / 资料**（三次元有番号时）  
6. **磁力**（仅执行了 ③）；否则写 `未搜磁力` 或 `二次元：跳过磁力`  
7. **总状态**一行，例如 `标题命中 FC2-PPV-4363423 → 官网下架仅资料站 → 未搜磁力`；官方预览型时如 `官方预览型（FC2 PPV）→ 跳过磁力/在线视频，仅核对时做预览对比`
8. **PDF 交付**：用户说「预览图转成 PDF」（或预览图量大，如女优作品海报网格 + 磁力清单）时：PIL 多页 A4 PDF（CJK 字体 `C:/Windows/Fonts/malgun.ttf` / `malgunbd.ttf`，配方见 acg-magnet-torrent-search 的「韩国 AV（K-av）捷径」），单个 PDF 走 MEDIA 发送，不逐张发图。

## 分支速查

| 情况 | 动作 |
|------|------|
| 有标题/番号（无论有没有图） | ①′ → 命中则跳过搜图 |
| 水印带 IPPA/EPPA 编号 | ①′ IPPA 法（ippa-member.info → 厂牌组/年代 → javdb 主题词）；有画面特征时走并行子代理分工 |
| 一行职员条 / 太碎纯字图 | 读字 → ①′ 搜声优或台词；不要 ② |
| 整屏 1080p 片尾 | ①′ 文字定锤，可加 ② 碰运气 |
| 仅有图（有可搜视觉） | ② |
| 二次元命中 | ④，无磁链 |
| 三次元命中，用户要磁力 | 资料 → ③ → ④ |
| 三次元命中，用户只要番号/来源 | 资料 → ④，不搜磁 |
| 全程未中 | 鉴定 + 明确无番号 |
| 用户丢网盘签名链接（116pan/windfiles/123pan） | ①″ 验链状态 → web_search 精确 dlname 定身份 → 预览核实；不搜图、不搜磁 |
| 只给人名要套图 / 写真集（无图无番号） | 套图路径：meitu.knit.bid 站内搜索列全套 → `?page=N` 分页下载 → 首图核实人物 → 预览交付（references/gravure-set-download.md） |
| 用户丢印尼 bokep 文件夹站链接（tribunvideo.com/f/ 等，含 X 帖内链）问是啥 / 核实内容 | bokep-indo-folder-sites：web_extract 文件夹页列清单 → jwplyr/Vidoy 三跳链拿真实视频 → 抽帧核年龄；不搜图不搜磁 |
| 社交帖截图（X/Bluesky 预告新模型/新资源，如免费 Live2D 模型） | ①′ 快路径：先答「说的啥 + 原帖 + 发帖人」→ fxtwitter 拿原帖（author.website 常直指店铺）→ VGen/BOOTH 查上架状态（references/social-post-source-tracing.md） |
| X 视频切片求出处（搬运号发的几秒预览，myfans/裏垢系素人） | 读该帖回复串取源链接（「ふる↓」+ 发帖人回 👍 = 确认）→ 跳转页 grep `window.location` → 帖子页 `__NEXT_DATA__` 取完整标题/日期 → fans-log / myxeromovie 核对时长与价格 → 抽帧与模糊封面并排核场景特征。无 JAV 番号（只有作者内部 `Page.NN`），磁力按 ③ 各源查一轮即定论（references/social-post-source-tracing.md §5） |
| 无图，用户要特定图（版本特典/宣传图/角色外观等） | 不走搜图链：web-image-hunt（文字定项 → 源优先级抓图 → md5+vision 核验 → 裁图交付） |
| 四源无磁链，或所搜资源（含二次元/同人/H游/套图等）无磁力链 | 调用 [laowang-cli](laowang-cli) 在老王论坛 `laowang.vip` 搜索（`laowang search "<关键词>"` → `laowang thread <tid>`），提取百度/夸克/PikPak/123pan 网盘链、种子附件或 `remote_play` 免费 `m3u8`/`.torrent`（付费项默认 dry-run，未经用户明确同意严禁 `--confirm`） |

## 不要做的事

- 不要有文字线索还先跑反向搜图主链。
- 不要把一行职员条/太碎纯字图丢给 Lens 或 SauceNAO；先读字搜声优表或台词。整屏片尾除外。
- 不要循环 `new_tab` 翻页；不要开完标签不关。
- 不要把 Lens 页内 Google AI 当成必做步骤。
- 不要把 `…15` 认成 `15,5`。
- 不要用图搜低置信号覆盖标题钉死的番号。
- 不伪造 magnet；不把镜相当 FC2 官网（主机仅 `adult.contents.fc2.com`）。
- 三次元搜磁力不要跳过 javdb-cli 直接上 sukebei/网页源；只有 CLI 不可用或 JavDB 结果不足才降级，且须在输出注明。
- 拿 IPPA/EPPA 号依赖 xsz-av / avjb 关键词搜索页定位（噪音大）；厂牌级注册号走 ippa-member.info + javdb 主题词路径。
- 网盘签名链接「过期」不等于文件没了：先解码 `expires` 看过期了多久，再引导新签名链/原帖，不要直接说资源死了。
- 不要替用户注册新账号：论坛检索优先用用户已有账号（老王论坛 laowang.vip（优先直接用已登录的 laowang CLI，见 laowang-cli skill，无需开浏览器重复登录；付费项默认 dry-run，未经用户明确同意严禁加 --confirm 扣软妹币）、sjs96 sjs96.com，用户有账密——发过来代填或让其在可见浏览器里自己登录），再用游客源（转载帖正文 / TG 频道）；用户明确同意才注册。
