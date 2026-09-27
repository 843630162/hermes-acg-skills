---
name: magnet-hash-aggregator-lookup
description: 非JAV系列/死站资源找磁力、BT、网盘下载来源时用。
---

# Magnet / Hash-Aggregator Source Hunt (non-JAV series)

For a **named series or collection** (studio series like LS/laurasolo-type packs, collector "收集整理" bundles, resources from dead forums) where the user asks "where can I download this", and it is NOT a JAV bangou lookup (that goes to acg-magnet-torrent-search / javdb-cli).

Deliverable: a **source list** — magnet links with hashes, aggregator pages, cloud-drive mirrors — each annotated with liveness evidence (last-activity date, file count/size), plus which candidate sites are currently reachable.

## Procedure

### 1. Web-hunt name variants in parallel
Run web_search on several spellings at once: original-language name, Chinese transliteration/localized name, "磁力" / "magnet" / "btih" combos, collector pack names (「收集整理」「collection by <author>」). Expect aggregator hash pages to surface even when the origin site is dead.

### 2. Extract candidate hashes + aggregators
From results pull: `magnet:?xt=urn:btih:<40-hex>` links and bare 40-hex strings (both are btih), plus cloud-drive mirrors (PikPak/Quark/Baidu share links). Record the aggregator domain per hash.

### 3. Verify liveness on the hash-aggregator detail page
Fetch the aggregator's per-hash page with curl and read: **last-active timestamp, file count, total size, seed heat**. A last-activity within days = still alive; also grab the embedded file list to confirm it is the right series (filenames like `lsm-*` / `lsd-*`).
- Same collection often exists under **multiple hashes** (re-seeds with different trackers): identical content metadata across two hash pages means duplicates — report both, mark them as same pack.

### 4. Probe reachability of dead/parked candidates via DoH
Local resolvers can be flaky (timeouts on domains that actually exist). Before declaring a site unreachable:
```bash
curl -s --max-time 10 "https://223.5.5.5/resolve?name=<host>&type=A"   # AliDNS DoH; Google: https://dns.google/resolve
```
- `Status:0` + A record → domain exists; curl it with `--resolve <host>:443:<ip>` (and port 80 variant) to bypass local DNS.
- `Status:3` (NXDOMAIN) → truly dead; check Wayback CDX for archives instead.
- A-record present but connect fails (curl exit 52/35, browser ERR_CONNECTION_CLOSED) → site is up-ish but flaky/WAF; log as "unreachable today", do not conclude content is gone.

### 5. Dead origin forums: Wayback CDX + GBK
For forum-based origins (Discuz etc.), enumerate `thread-*` URLs via CDX and pull snapshots through `web.archive.org/web/<ts>/<url>`:
- **Pages are often GBK**: `curl ... | iconv -f GBK -t UTF-8` before parsing; regex for thread titles/links on the converted text.
- **CDX rate limit: keep concurrency ≤ 2–4** (parallel >4 → "Remote end closed"); on a failed timestamp, retry with an earlier capture from the same URL's CDX list. A transient "Temporarily Offline" HTML response = back off ~15s and re-query.
- Forum section pages (`forumdisplay.php?fid=N`) captured while logged-out usually show 您無權進入 (login wall) — the real content is in `thread-<tid>-1-1.html` snapshots; distinguish "page archived but login-walled" from "no capture exists".
- **But thread-* snapshots are ALSO commonly walled** (Discuz returns HTTP 200 with a 您無權進入 body — status 200 does NOT mean content). When the bulk of thread-* captures are walled, check for `archiver/fid-*.html` board-index pages: they bypass the login wall and list every thread's title + tid per section. Those titles (series name + issue numbers) become your search keywords for live aggregators even though no body links survive.

### 5b. 冷门资源：838888 系磁力搜索引擎（2026-09 实测）

死站/小众系列（LS/laurasolo 类）关键词搜索首选 **838888 引擎族**，冷门收录比 chihuhub/btbtt 好：

| 站点 | 状态（2026-09 实测） | 用法 |
|------|------|------|
| `www.868888.net` / `www.838888.net` | ✅ curl 直连可用，无需验证页 | 搜索 URL = `/search/<hex(utf8关键词)>-<页码>-id-s.html`（**不是** `/search?keyword=`，后者 404）。例：Ls-magazine → `https://www.868888.net/search/4c732d6d6167617a696e65-1-id-s.html`（hex 是关键词的 UTF-8 字节十六进制，Python: `kw.encode('utf-8').hex()`）。结果页每条指向 `/hash/<40位hash>.html` 详情页（与 3d47.com 同结构） |
| **磁力狗 ciligou.net** | ⚠️ A=104.224.157.58，curl 只返回 JS 验证脚本；需浏览器点「点击访问」按钮过验证页（`a.challenge-c`），过后跳到 `clg1x.vip` 镜像（如 clg10.vip/clg105.vip） | **必须经导航站取当前入口**，不要硬记域名：bs5.org `/site/10001`=磁力狗（列 ciligou.net + clg.im）、jinyu.org、cldq.cc（→ cldq.xyz/cilidaquan SPA）。镜像域：clg.im / ciligou.net / cilibao 系；验证页同引擎族，过验证后搜索 URL 与 838888 相同格式 |

- `ydx.cilimao.im`（磁力狗内部 watch 主机）只返回 1x1 GIF，是统计/挑战后端，不是搜索入口。
- ciligou 各域 DoH：clg.im / ciligou.net / cilibao.app/.top/.in A=104.224.157.58；`www.*` 多无记录——直连一律用裸域 + `--resolve host:443:104.224.157.58`。
- 导航站卡片会换目标域（bs5.org 的 /site/N 卡里列当前有效域名），**每次以导航页现取的 URL 为准**，别把旧镜像写死进流程。

### 6. Deliverable shape
Per source: name/series | magnet or URL | size/file count | last-active date | aggregator domain | status (live / flaky / dead→archive). Close with a one-line reachability summary of every candidate site probed, and which sub-series have evidence vs none.

## Pitfalls
- **Do not trust local DNS/`nslookup` for liveness.** A timeout or "Non-existent domain" from the host resolver can be a flaky resolver, not a dead zone. WHY: cost a wrong "site is dead" conclusion; DoH gave the answer in 10s.
- **Aggregator search endpoints rot faster than per-hash pages.** Sites like 838888.net lose their `/search?keyword=` path (404) while known hashes stay reachable on mirror domains (e.g. 3d47.com's `/hash/<hex>.html`). When a keyword search 404s, don't conclude the site is dead — probe a known hash page directly and check for mirror domains of the aggregator.
- **838888 族搜索是 hex URL，不是 query string。** `/search?keyword=X` 全 404；正确形式 `/search/<hex>-1-id-s.html`（mysubmit() JS 把关键词 UTF-8 转 hex 后拼路径）。curl 即可，无需浏览器。
- **磁力狗 (ciligou/clg.im) curl 只拿到 base64 JS 验证壳**：解码后是 `location.href='https://clg1x.vip/search/…'`。无头流程用 browser_exec 打开镜像域、点 `.challenge-c`「点击访问」按钮过验证页再读结果；或直接把导航站列出的 clg*.vip 域 curl（带同路径 hex URL）。注意其跳转可能开新标签，about:blank 卡住时 `Target.getTargets` 找真实 page target。
- **When delegating bulk CDX enumeration to a subagent, demand findings written to disk incrementally.** A long fan-out can die on context overflow with only its saved files (CDX dumps, parsed JSON) surviving; the final report file is often left empty. Verify every claimed output file exists and is non-empty before building on it.
- **Verify every magnet on its aggregator detail page before delivering** (last-active + file list). A hash found via search may be stale or a different pack with a similar name.
- **browser_exec `js()` async loops over many URLs exceed the daemon's evaluate window and time out.** Do one in-page fetch per call, or navigate (`new_tab`/`goto_url`) and read DOM; batch multi-site probes into a few small chunks instead of one giant loop. (Single `fetch` inside `js()` is safe.)
- **GBK-encoded legacy forum pages must be iconv'd before any regex** — searching the raw bytes for thread titles silently fails.
- **Wayback CDX concurrency >4 gets throttled** (Remote end closed); 2–4 parallel + earlier-timestamp retry is the working pattern. A "Temporarily Offline" HTML page from web.archive.org = transient, back off and re-query.
- Do not fabricate hashes or last-active dates; every number in the deliverable comes from a fetch you ran (same rule as dead-site-resource-recovery).

## Relation to other skills
- JAV bangou / FC2 driven → [acg-magnet-torrent-search](acg-magnet-torrent-search) + javdb-cli first.
- Entry point is a **dead site domain** and the goal is recovering its content/files → [dead-site-resource-recovery](dead-site-resource-recovery); this skill covers the *magnet/source-hunt* side of such tasks (its aggregator step overlaps: chihuhub/btbtt/磁力狗 for seed status).
