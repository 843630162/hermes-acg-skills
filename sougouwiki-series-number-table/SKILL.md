---
name: sougouwiki-series-number-table
description: 用户要整系列番号清单或怀疑前缀不对时，从 sougouwiki 抓全表整理号→演员名。
category: research
metadata:
  hermes:
    editorial_name: sougouwiki 系列编号表
    editorial_description: 从素人系综合 wiki 抓取整厂牌/整系列的完整番号表，解析缓存全文并交付「号→演员名」CSV 与 HTML。
    requires_tools: [web_extract, execute_code]
---
# sougouwiki 系列编号表（号→演员名清单）

用户问整个系列、怀疑番号前缀不对、或要拿清单去批量搜磁力时使用。先抓全表整理成「号→演员名」清单作为检索输入，不要凭零星样本猜前缀。

## 抓取

1. `seesaawiki.jp/w/sougouwiki/d/{LABEL}` 找厂牌/系列页；长系列常拆多页（如 `{LABEL}(201～)`），全部抓齐再合并。相关子线（Regular / for MEMBERS / AMATEURGRAPH）通常各有独立页面。
2. **seesaawiki 对裸 requests/curl 返回 403** → 一律用 `web_extract` 拉；全文会落在 `<HERMES_HOME>/.cache/web\*.md`（按 mtime 找最新对应文件）。

## 解析

1. **解析缓存 .md，不要解析 web_extract 的返回值或 spillover**：head+tail 窗口会丢长表中间行（实测 dm001–200 只回 92 行）。用 Python 正则对全文文件抽全部行。
2. 表格 ID 格式可能中途变化（如 `_p` 后缀在某行后消失）→ 正则要兼容两种写法，抽完后**按 ID 连续性校验无缺口**，有缺口就回头补正则以抓漏行。
3. wiki 内部 ID 常与圈里番号不一致（如会员线 `dmNNN` ↔ 磁力站写作 `MDG-NNN`）→ 清单显式给两列映射，两种写法都拿去搜磁力。

## 交付

1. CSV（**UTF-8 BOM**，Excel 日文兼容）+ HTML 表；列 = wiki内部ID / 圈里番号 / 演员名 / 副标题。
2. 早期条目可能只有罗马字别名、没有正式艺人名 → 按副标题首词补入并标「别名」，不要留空。
3. 同系列多个子线合并时先 sanity-check：各线 ID 不重叠、总数与页面声明一致。

## 不要做的事

- 不要用 requests/curl 直接抓 seesaawiki（403）。
- 不要只解析 web_extract 返回内容就下「表完整」的结论——必须对缓存全文文件做连续性校验。
- 不要把 wiki 内部 ID 当成磁力站番号写法，两种都要给。
