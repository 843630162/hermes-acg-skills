---
name: ACG release schedule
description: "Use when 用户要某月/下月的里番新番表或发售日历、要求附图时用：Hanime1 预告抓取+封面拼图。"
tags: []
related_skills: [acg-resource-search-router]
---
# ACG 月度新番表（里番 / 成人动画）

任务类：用户问「这个月/下个月的里番有哪些」，常要求附图。**不走** acg-resource-search-router 的搜图闭环——这是排期查询，不是资源定位。

## 抓取（HTTP 优先）

1. Hanime1 新番預告页是服务端渲染，curl 即可：
   ```bash
   curl -sL "https://hanime1.me/search?genre=%E6%96%B0%E7%95%AA%E9%A0%90%E5%91%8A" \
     -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36'
   ```
   一页覆盖未来多个月，日期是无年份的 `M月D日` —— 按月份自己分组。
2. **不要用旧路由 `/previews/YYYYMM`**：近期月份返回 500 Server Error（站点已把导航入口注释掉改用 genre 搜索）。若搜索页拿不到结果网格（纯 JS / 空列表），改 drive_preview 浏览器读页面，不要循环开标签。

## 解析配方

- 封面：`re.finditer(r'image/cover/(\d+)\.jpg\?secure=([^\s"]+)', html)`，按 id 去重。
- 每张卡片后续 ~1600 字符内的文本节点：日期出现**两次**（同一 `M月D日`），标题是第二个日期之后第一个非日期中文文本节点。先剥标签取 `>([^<>]+)<` 再 unescape。
- 封面 CDN：`https://vdownload.hembed.com/image/cover/{id}.jpg?secure={token}`，必须带浏览器 UA + `Referer: https://hanime1.me/`，否则拒图。
- 交叉校验：去重后封面数 == 卡片数；对不上就重新拉页（SSR 页面可能拿到旧缓存）。

## 附图交付（用户要求「附图」时默认走这条）

- 做带标签 contact sheet PNG 网格（每格封面 + 日期 + 标题），**发前用 vision_analyze 验一遍**：无破图/空白格、文字不重叠不溢出，再 `MEDIA:` 交付。直接甩一堆散装 jpg 不如一张总览图。
- Pillow 不在系统 `py` 里；用 Hermes venv 解释器 `<HERMES_HOME>/hermes-agent/venv/Scripts/python.exe`（自带 PIL）。拼图脚本见本 skill `scripts/contact_sheet.py`：
  ```bash
  "<HERMES_HOME>/hermes-agent/venv/Scripts/python.exe" <skill_dir>/scripts/contact_sheet.py items.json --title "2026年9月 里番新番" --out F:\\Hermes-work\\rihan_2026-09.png
  ```
  `items.json`：`[{"id":"...","date":"9月4日","title":"...","image":"cov_xxx.jpg"}, ...]`（本地路径或 http url）。
- 交付物存 <WORK_DIR>；任务结束删掉临时目录（封面、html dump），只留总结/拼图。

## 输出格式

1. 按月分表：日期 + 作品名，标注是**新作还是老番续集/新话数**（预告页里混大量续作，别笼统说「新作」）。
2. 注明数据源与预定发售日可能微调。
3. 二次元不搜磁力（router 规则），除非用户明确要。
