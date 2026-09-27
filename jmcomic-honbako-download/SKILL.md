---
name: jmcomic-honbako-download
description: "Use when 用户要下载禁漫天堂/JMComic 本子：插件工具搜+下，存 F 盘。"
---
# JMComic（禁漫天堂）本子下载

用户说「帮我下个 XX 本子」「JM 上有这本吗」时用本 skill。先在 JM 搜；**JM 没有的本子（商业连载/单行本，如 Bebe、融合社作品）直接走 Hitomi.la 章节，别在 k-manga 的 canvas 阅读器上耗时间。**

## 标准闭环：用户丢一页漫画图要「找这本并下载」
固定流水线（实测跑通两次）：
1. **先读图里的名字**：`vision_analyze` 逐字读出角色名牌/标题/水印。有作品名或作者名 → 直接拿它当关键词去 JM `jmcomics_search`（kind=site，日文原名+中文译名各试一次），命中就下。
2. **图里没有名字**（只有角色名牌这种）→ **反向搜图定名**：browser_exec 开 `https://soutubot.moe/`，CDP `DOM.setFileInputFiles` 喂 `#file-input`（自动提交跳结果页），等 ~10s 读结果页文本。命中格式「NN.NN% NHentai #车号 + 标题(含中文翻译版)」。**相似度 ≥90% 且元数据匹配即定名，不用再开 Lens/Yandex**。角色名牌（如「俵山愛莉」）搜不到作品时不要死磕 web_search。
3. **拿到名字/作者 → JM 下载**：`jmcomics_search {query:作者或标题, kind:'author'}` 挑最匹配车号 → `jmcomics_download {ids:[车号]}`。JM 条目名常是「[汉化组] [原作(作者)] 日文原名」，中文名在括号里。
4. **转 PDF**（用户要 PDF/发文件时）：PIL 逐张 `Image.open(webp).convert('RGB')` → `save(save_all=True, format='PDF', resolution=150)`。webp→pdf 前用 `os.listdir`+endswith 过滤，别用 glob（目录名带 `[...]` 方括号会被当字符类）。

## PDF 命名与验收
- **文件名必须带时间戳**：`伪装词-MMDD_HHMM.pdf`（如 `项目周报-0921_1731.pdf`），同一天多版本不互相覆盖。伪装词避开「本子/漫画/JM/hentai」等敏感字，用「产品需求文档」「项目周报」这类。
- **验收分辨率**：PIL 抽查每张图宽度（正文页应 ≥1000px），别只信下载成功或文件大小——内容简单的全尺寸页可能才几 KB。

## 基础设施（已装好，勿重装）
- Hermes 插件 `jmcomics`：位于 `<HERMES_HOME>/plugins/jmcomics/`（plugin.yaml + __init__.py + option.yml），已在 `<HERMES_HOME>/config.yaml` 的 `plugins.enabled` 里启用。
- jmcomic 库装在 Hermes 主 venv（jmcomic 2.7.x，Python 3.11）。
- 凭据在插件目录 `option.yml`（login 插件自动登录；账号/密码只写在本机 option.yml，**不要提交进仓库**），下载根目录 `dir_rule.base_dir: <工作盘>/downloads/jmcomic/`。
- 参考源码：GitHub hect0x7/JMComic-Crawler-Python；独立 venv（含 jmcomic）可作备用解释器。

## 正常流程（插件工具可用时）
会话里直接调两个工具：
1. `jmcomics_search {query, kind}` — kind: site(默认关键词/车号) / author / tag / work / actor。返回 `[id] 标题 (tags)` 列表，**把 id 给用户确认或自行挑最匹配的一条**（搜索结果常有汉化组前缀、多版本）。
2. `jmcomics_download {ids}` — ids 用 `['<车号>']` 下整本；`['p<章节id>']` 只下单章。阻塞到全部图片下完，大本可能几分钟（terminal 超时要给足）。
3. 验证：`ls <WORK_DIR>/downloads/jmcomic/<书名>/` 有 webp 文件、数量与日志一致；报给用户保存路径。QQ 端可挑封面/前几张图用 MEDIA: 发出去预览。

## 工具不可用时（新会话未加载插件 / 工具没出现）
直接用主 venv python 跑，等价于插件逻辑：
```bash
# <HERMES_HOME>/hermes-agent/venv 里的 python（Windows: .../Scripts/python.exe；Linux/macOS: bin/python3）
python - <<'PY'
import importlib.util, time
spec = importlib.util.spec_from_file_location('jm', r'<HERMES_HOME>\plugins\jmcomics\__init__.py')  # Linux/macOS 用正斜杠
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
print(m._handle_search({'query':'关键词','kind':'site'}))   # 搜索
# print(m._handle_download({'ids':['车号']}))                 # 下载整本
PY
```
首次调用会先登录（约3秒），之后 option/client 有缓存。

## Pitfalls（全部踩过）
- **不要用 `jmcomic.api.download_album/download_photo`**：它进 jm_task_context，退出时等 after_album 插件收尾，在只有 login 插件的 option 下会挂死（实测卡 >7 分钟）。用 `new_downloader(option)` 上下文管理器直接调 `dler.download_album(id)` / `dler.download_photo(pid)`（2 秒完成）。
- **锁要用 RLock**：`_handle_*` 持 `_lock` 时内部会再调 `_load_option()` 抢同一把锁，普通 Lock 死锁且无报错（faulthandler 定位过一次）。
- option.yml 用 `jmcomic.api.create_option(path)` 加载；JmOption 没有 from_dict。读 base_dir：`option.__dict__['dir_rule']['base_dir']`（不支持下标访问）。
- 搜索走 api 端（impl: api），域名自动更新（cdnhjk.net 等）；登录失败先看 option.yml 里 username/password 是否还是当前账号。
- 车号是纯数字 id；搜索结果里的 `147xxxx` 都是车号，可直接下。同名多版本时优先选带汉化组名、章节多的那条。
- 下载目录在 F 盘（遵守用户禁 C 盘规则）；webp 原图不解码，要 PDF/长图可在 option.yml plugins.after_album 加 zip/img2pdf 插件（需 `pip install jmcomic[plugins]` 到主 venv）。

## JM 没有的本子 → Hitomi.la（商业连载/单行本）
- 搜索端点：`https://hitomi.la/search.html?` + encodeURIComponent(关键词)（旧 `/advsearch/`、api.hitomi.la 都失效了）。结果页 `/manga/<slug>-<id>.html`，ID 就是 reader 用的数字 id。
- **全尺寸图必须从 reader 页取**：`https://hitomi.la/reader/<id>.html`，正文 img src 在 `w1/w2.gold-usergeneratedcontent.net`（~1012px 宽）。画廊页只有缩略段（webpsmalltn/webpbigtn，很多页仅 454px），拿它做 PDF 字会糊到不可读——踩过。
- 翻页：找 `options.length===总页数` 的 `<select>`，`s.value='N'; s.dispatchEvent(new Event('change',{bubbles:true}))`，等 ~2s 后收 img src（正则 `/w[12]\.gold-usergeneratedcontent\./`）。别用 `next_scene()`（会卡在第1页不动），别裸调 `twoPageChange()`（TypeError）。
- 部分页首次只给小文件（~4KB）：对该页重新跳转、等 8–12s 让 reader 换入高清图后再取 URL。**验收用 PIL 查尺寸（宽≥1000），别信文件大小**——内容简单的全尺寸页本来就小。
- 下载：curl + UA + `-e https://hitomi.la/`，并发 ≤5、404 退避重试即可；CDN 对 referer 宽松。
- PDF：PIL `Image.open(webp).convert('RGB')` → `save(save_all=True, format='PDF', resolution=150)`。全尺寸 163 页约 44MB，属正常。

## k-manga（まんが王国）canvas 阅读器——能避则避
竖读 reader 是 canvas + WebSocket 流式 base64：CDP Input 事件被主线程动画循环吞掉（wheel/touch/mouse 全超时但可能已投递）、合成事件被 isTrusted 过滤、`window.scrollTo` 不推进场景。硬要用时：`Page.addScriptToEvaluateOnNewDocument` 装持久钩子捕获 drawImage dataURL + `canvas.toDataURL()` 逐页导出，但只有预载的场景能抓到，翻页是难点。

## 输出格式
书名 + 车号、章节数、图片数、总大小、保存路径。需要时附前几张预览图（MEDIA:）。
