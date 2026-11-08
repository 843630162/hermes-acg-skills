# 套图 / 写真集下载（人名 → 套图 → 下载 → 预览）

适用：用户只给**人名**（如「找 X 的套图」），要写真/gravure 套图，不是 JAV 作品（番号类）也不是二次元。来源偏好（imouto.tv / 幼女系未成年优先等）以用户档案为准。

## 固定流程

1. **列套图**：web_search 对日本写真系人名召回常为 0 或噪音，别重试 → 直接上镜像聚合站的站内搜索：
   `curl -sL --compressed -A 'Mozilla/5.0' 'https://meitu.knit.bid/search/<urllib.parse.quote(人名)>'`
   - 必须核对结果页 `<title>` 含**逐字正确**的关键词：编码错一个字节 = 「暂无结果」（例：れい 末字节 %84 错成 %86 = れう，空结果但不报错）。
   - 搜索结果直接给出该人全部套图的 `/beauty/<slug>` 链接；`/model/<slug>` 模特页也能列全。
   - meitu.knit.bid 是死站镜像聚合（minisuka.tv / imouto.tv / Girlz-High / Digi-Gra / 秀人等）：图带原站水印（如 minisuka.tv、俊美图），1200px webp，通常就是能拿到的最高清，交付时注明水印。
   - JavDB actor 对 JK/写真系模特常 NotFound——正常（人物库偏 AV 女优），别当「查无此人」，也不要在本路径里绕 javdb。
2. **枚举页**：`/beauty/<slug>` 第一页是静态完整 HTML，含全部分页。
   - 第 N 页 URL = `?page=N`（`/N`、`/page/N` 均 404）。
   - 总页数 = 分页 nav 里出现的**最大页码**（gotoPage(N) 与数字页项都算）；末页「下页」指向第 2 页不是 disabled，别用它判断。
   - 每页固定 3 张主图。
3. **提取图**：主图在 `<div class="details_item ...">` 容器内，懒加载（`src=loading.gif` + `data-src` 真实路径）。页底「猜你喜欢」推荐区也有 `data-src`（缩略图均带 `thumb_0_425_` 前缀）——只取容器内或排除 thumb，否则张数虚高。
4. **下载**：`https://meitu.knit.bid` + data-src 路径，8 线程并发即可。校验：文件数 = 页数 × 3；RIFF/WEBP magic（`RIFF`@0、`WEBP`@8，注意 WEBP 四字节在 offset 8 不是 4）；webp 解析宽高（VP8/VP8L/VP8X 三分支）。
5. **核实内容**：vision_analyze（挂时改 ninfer qwen :9000）每套首图确认是目标人物；混入同名不同人整套剔除。
6. **存放**：`<WORK_DIR>\downloads\<人名>\<NN_主题>_<来源站>\<NNN>.webp`（NNN 三位零填充，按页序）。
7. **交付**：用户当条消息已明说「下载下来」→ 直接下全套，回消息附 4–6 张预览（webp 直接走 `MEDIA:`，QQ 原生可读）；未明说 → 先列清单（编号 + 套图名 + 张数 + 缩略图），等确认再下（用户既定偏好）。
8. **收尾**：删本次全部中间产物（HTML/JSON dump、probe 脚本），只留交付目录；process list 确认无残留后台进程。

## 坑

- 文件大小不能当质量判据：30–180KB 的 webp 就是 1200px 原图，先解析头部宽高再说话。
- 镜像站的「套图」可能只是原站的部分镜像（如 minisuka.tv 原站已死），找不到原图高清版属正常，注明即可。
- 搜索结果「暂无结果」先自查关键词编码（见第 1 步），再考虑换写法/换站。
