# 核实「疑似某 X 漫画作者」：twicomi 列表 + fxtwitter 取原图

反搜/Lens/Onegai 指向某个 X 漫画账号时，用这条纯命令行链核实，不用开浏览器。

## 1. 拉作者全作品表（标题 + 日期 + 推文 ID）

`https://twicomi.com/author/<handle>/sort/date/page/<N>` 逐页 curl（带浏览器 UA，页间 sleep 0.4s）：

- 页面文本里每条漫画的结构是「台词行… → @handle → `YYYY年M月D日`」。
- 链接 `href="/manga/<handle>/<tweet_id>"` 里的数字就是推文 ID。
- 解析：以 `@<handle>` 这一行做锚点，向上收台词（跳过「タグなし」「展開」「Twitterで見る」和纯数字/日期行），向下正则 `^\d{4}年\d+月\d+日$` 取日期。实测一个东方漫画作者一次拿到 112 条、覆盖到 2026-07。
- 存成 `[(date, title), ...]` 的 JSON，按日期排序，后面靠它做关键词筛。

## 2. 先筛标题，再取图

把题材词（例：`トイレ` `おもらし` `がまん` `ゴミ` `外出` `外で` `尿`）grep 刚抓到的标题表：

- 命中 → 才值得进第 3 步取原图。
- 全表都不含题材词 → 该作者不是来源，停止挖掘（实测：某画风高度相似的东方作者 112 条标题里没有任何如厕/垃圾/外出题材，直接排除）。

## 3. 取原推与原图

```bash
curl -s -A "$UA" "https://api.fxtwitter.com/<handle>/status/<tweet_id>" \
  | python -c "import json,sys; t=(json.load(sys.stdin).get('tweet') or {}); print(t.get('created_at')); print(t.get('text')); [print(m.get('url')) for m in ((t.get('media') or {}).get('all') or [])]"
```

`media.all[].url` 换成 `?name=orig` 可直接 curl 下载（实测 `pbs.twimg.com/media/<code>.jpg?name=orig` → 900×1650 原图，免登录）。然后 vision 比对用户图与该推文图（同页/同格才算命中）。

## 4. 结论纪律

- 风格像、内容不对 → 只能说「同风格作者」，不能当成出处；不要把该作者写进候选表第一位。
- 只有当 vision 确认同一组分镜、或标题+日期与用户图的汉化 repost 日期对得上，才把作者写进结论。
