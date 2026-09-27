---
name: jav-person-profile
description: 查日本ACG/JAV人物档案（女优/声优/写真）：javdb actor优先，NotFound降级萌娘/bangumi。
---
# 日本 ACG/JAV 人物资料检索

用户问「X是什么人 / 整理一下 TA 的资料」：女优、声优、写真系艺人。本 skill 只做**人物档案**，番号/作品核对走 [jav-bangou-lookup-fc2](../jav-bangou-lookup-fc2/SKILL.md)，磁力走 acg-magnet-torrent-search。

## 步骤

1. **名字变体**：简体 / 日文汉字 / romaji 各准备一份（丰田萌绘 = 豊田萌絵 = Toyota Moe），逐一试，不要只用用户给的写法查到底。
2. **JavDB 优先**（javdb-cli 可用时，参数以 javdb-cli skill 为准）：
   - `javdb actor "名字" --json` — 命中即直接拿作品列表；
   - `javdb search "名字" --type actor --json`。
   - **NotFound ≠ 圈外**：JavDB 人物库偏 AV 女优，声优系/写真系艺人常无条目。NotFound 就降级第 3 步，不要写「查无此人」。
3. **网页兜底源集**（web_search + web_extract 并行）：
   - `zh.moegirl.org.cn` — 基本信息 + 完整电视动画作品表（声优系最权威）；
   - `bangumi.tv/person/<id>` — 别名、出身地、事务所、官方博客；
   - Weblio 辞典 `weblio.jp/content/<URL编码名>` — 著作/写真集书目（含 ISBN）；
   - `xslist.org/zh` — AV 作品列表（仅当确认有作品时再查，别默认人人都有号）。
4. **同名核对**：合并或拆分人物前，先交叉生日 + 事务所。声优与写真/AV 常是同一人跨领域活动；只有生日冲突才拆成两个人。身高体重等身体数据各源不一致（如声优资料 vs 写真企划宣传值）时分别标注来源，不要取平均。
5. **输出格式**：基本信息 / 代表作（配音）/ 写真与著作活动 / 备注，末尾列来源站点。

## 陷阱

- CJK 百分号编码 URL：「未找到术语 X」页先核对码点再下结论——豊是 %E8%B1%90，错一个字节变豚（%E8%B1%9A）会得到假阴性；重查字符后再说没有条目。
- 搜索命中里提到目标人物的 snippet 常是**相关人物**的文章（标题/描述夹带目标名），只当旁证，不当成 TA 自己的作品或活动证据。
