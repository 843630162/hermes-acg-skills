#!/usr/bin/env python
"""歌单缺口审计（2026-10-11 实测定稿）—— 解释 playlist 标称条数 > 实际可列出条数的缺口。

结论模型（Iwara 实测，通用思路同样适用于"计数器含不可见项"的站点）：
  numVideos = 可列出 + 私密(403) + 已删(404)
  登录（含作者本人 token）**不解锁**额外条目；缺口逐条定性：
  对"标称有、列表没有"的可疑 ID 逐条 GET /video/{id}（带作者 accessToken）：
    403 = 私密（作者未对列表开放，可补进目录供日后回查）
    404 = 已删（只记数量，ID 可能来自旧缓存）

用法（turnstile-bypass skill 的 venv python 跑）：
  python playlist_gap_audit.py --site iwara \
      --playlist 03ba44da-caf0-4060-a2ce-e361d33b9d43 \
      --user <iwara-user> --password-file <creds.json> \
      --suspect-ids suspect_ids.json --out result.json

  --password-file: {"password": "***"} 或 {"pw": "***"}（键名兼容）
  --suspect-ids:   文本/JSON 文件，每行一个 videoId（来自旧缓存/旧报告的"应有但没列出"的 ID）
  --variants:      逗号分隔的 API 参数变体，默认 "plain,limit=1000,unlisted=1,mine=1,private=1"
  端点按 Iwara 约定写死（user/login、user/token、playlist/{id}、video/{id}、www SPA 页）；
  其他站点照 page-session.md 配方改 ENDPOINTS 即可。

产出 result.json: {login, tokEx, variants:{k:{s,n,numVideos,ids}}, v403:[...],
  spa:{...}, gap:{declared, listed, private, deleted, unexplained}}
"""
import argparse, asyncio, json, sys, time, re

VARIANTS_DEFAULT = ["plain", "limit=1000", "unlisted=1", "mine=1", "private=1"]

JS_AUDIT = r"""
(async () => {
  const t0 = performance.now();
  const j = async (u, o = {}) => {
    const r = await fetch(u, o);
    let b; try { b = await r.json(); } catch (e) { b = {}; }
    return { s: r.status, b };
  };
  const out = { variants: {}, v403: [], spa: null };
  const acc = localStorage.getItem("token") || "";
  const H = { "Authorization": "Bearer " + acc };
  const authed = h => ({ credentials: "include", headers: h ? h : {} });
  // 1) 变体探针：owner token 下逐个参数组合拉列表
  for (const key of window.__VARIANTS) {
    const q = key === "plain" ? "" : "?" + key;
    const r = await j("https://api.iwara.tv/playlist/" + window.__PID + q,
      Object.assign(authed(key === "plain" ? {} : H), {}));
    const res = r.b.results || [];
    out.variants[key] = { s: r.status, n: res.length,
      numVideos: r.b.numVideos !== undefined ? r.b.numVideos : (r.b.playlist && r.b.playlist.numVideos),
      ids: res.map(x => x.id) };
  }
  // 2) 可疑 ID 逐条定性（403=私密 / 404=已删）
  for (const id of window.__SUSPECT) {
    const r = await j("https://api.iwara.tv/video/" + id, Object.assign({}, authed(H)));
    out.v403.push({ id, s: r.s, title: r.b.title || (r.b.video && r.b.video.title) || "",
      user: r.b.user && r.b.user.username, created: r.b.createdAt });
  }
  // 3) SPA 歌单页由 Python 用第二个 page 执行 JS_SPA（同浏览器共享 localStorage token），此处不重复
  return out;
})()
"""

# SPA 滚动单独用第二 page 跑（歌单网页），JS 如上 SPA_JS 内层
JS_SPA = r"""
(async () => {
  const t0 = performance.now();
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const scrollers = () => {
    const els = [];
    document.querySelectorAll("div, section, main").forEach(e => {
      if (e.scrollHeight > e.clientHeight + 200 && e.clientHeight > 200 &&
          ["auto", "scroll"].includes(getComputedStyle(e).overflowY)) els.push(e);
    });
    els.push(window);
    return els;
  };
  const hits = { pl: 0, sample: [] };
  const of = window.fetch;
  window.fetch = function (...a) {
    const u = (typeof a[0] === "string" ? a[0] : (a[0] && a[0].url)) || "";
    const p = of.apply(this, a);
    if (u.indexOf("/playlist/") >= 0) {
      hits.pl++;
      p.then(r => { if (hits.sample.length < 5) hits.sample.push({ u: u.slice(0, 160), s: r.status }); }).catch(() => {});
    }
    return p;
  };
  let prev = 0, stuck = 0;
  for (let i = 0; i < 120 && stuck < 6; i++) {
    const els = scrollers();
    els.forEach(e => { if (e === window) window.scrollTo(0, document.body.scrollHeight); else e.scrollTop = e.scrollHeight; });
    const btn = [...document.querySelectorAll("button, a, [class*=load], [class*=more], [class*=next], [class*=Load], [class*=More]")]
      .find(b => /load\s*more|更多|more|next|load/i.test(((b.innerText || "") + " " + (b.className || ""))) && b.offsetParent);
    if (btn) { try { btn.click(); } catch (e) {} }
    const n = document.querySelectorAll("a[href*='/video/']").length;
    if (n === prev) stuck++; else { stuck = 0; prev = n; }
    await sleep(700);
  }
  return { ms: Math.round(performance.now() - t0), htmlVids: document.querySelectorAll("a[href*='/video/']").length,
    plRequests: hits.pl, plSample: hits.sample, title: document.title };
})()
"""

JS_LOGIN = r"""
(async () => {
  const j = async (u, o = {}) => { const r = await fetch(u, o); let b; try { b = await r.json(); } catch (e) { b = {}; } return { s: r.status, b }; };
  const login = await j("https://api.iwara.tv/user/login",
    { method: "POST", credentials: "include", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: window.__USER, password: window.__PW }) });
  if (login.s !== 200) return { login: login.s, tokEx: -1, accLen: 0, errMsg: JSON.stringify(login.b).slice(0, 200) };
  const tok = await j("https://api.iwara.tv/user/token",
    { method: "POST", credentials: "include",
      headers: { "Content-Type": "application/json", "Authorization": "Bearer " + login.b.token }, body: "{}" });
  if (tok.s === 200 && tok.b.accessToken) localStorage.setItem("token", tok.b.accessToken);
  return { login: login.s, tokEx: tok.s, accLen: (tok.b.accessToken || "").length };
})()
"""


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--playlist", required=True)
    ap.add_argument("--user", required=True)
    ap.add_argument("--password-file", required=True)
    ap.add_argument("--suspect-ids", default="")
    ap.add_argument("--variants", default=",".join(VARIANTS_DEFAULT))
    ap.add_argument("--out", default="playlist_gap_result.json")
    ap.add_argument("--no-spa", action="store_true")
    a = ap.parse_args()

    d = json.load(open(a.password_file, encoding="utf-8"))
    pw = (d.get("password") or d.get("pw") or list(d.values())[0]) if isinstance(d, dict) else str(d)
    suspects = []
    if a.suspect_ids:
        raw = open(a.suspect_ids, encoding="utf-8").read()
        try:
            arr = json.loads(raw)
            suspects = [x if isinstance(x, str) else str(x.get("id")) for x in arr]
        except Exception:
            suspects = [ln.strip() for ln in raw.splitlines() if re.fullmatch(r"[A-Za-z0-9]{6,32}", ln.strip())]
    variants = [v.strip() for v in a.variants.split(",") if v.strip()]

    from camoufox.async_api import AsyncCamoufox
    log = lambda m: print(m, flush=True)
    async with AsyncCamoufox(headless=False, humanize=True, os="windows", i_know_what_im_doing=True) as cw:
        page = await cw.browser.new_page()
        await page.goto("https://www.iwara.tv/", wait_until="domcontentloaded", timeout=90000)
        for _ in range(30):
            t = (await page.evaluate("document.title")) or ""
            if "moment" not in t.lower() and "just a" not in t.lower():
                break
            await asyncio.sleep(1)
        log("CF: " + (await page.evaluate("document.title")))
        # 注入参数（evaluate 无法传闭包，用 window 属性）
        await page.evaluate("window.__USER = %s; window.__PW = %s; window.__PID = %s; window.__VARIANTS = %s; window.__SUSPECT = %s;"
            % (json.dumps(a.user), json.dumps(pw), json.dumps(a.playlist), json.dumps(variants), json.dumps(suspects)))
        login = json.loads(await asyncio.wait_for(page.evaluate(JS_LOGIN), timeout=90))
        log("login: %s tokEx: %s accLen: %s" % (login.get("login"), login.get("tokEx"), login.get("accLen")))
        audit = json.loads(await asyncio.wait_for(page.evaluate(JS_AUDIT), timeout=240))
        for k, v in audit["variants"].items():
            log("%s %s n=%s numVideos=%s" % (k, v.get("s"), v.get("n"), v.get("numVideos")))
        for v in audit["v403"]:
            log("vid %s -> %s %s" % (v["id"], v["s"], (v.get("title") or "")[:40]))
        # 全量翻页拿 listed 集合（plain 变体只给首页；用 API 逐页翻完）
        # SPA 验证（第二 page 同浏览器，共享 localStorage token）
        spa = None
        if not a.no_spa:
            page2 = await cw.browser.new_page()
            await page2.goto("https://www.iwara.tv/playlist/%s" % a.playlist,
                             wait_until="domcontentloaded", timeout=90000)
            log("pl title: " + (await page2.evaluate("document.title")))
            log("scrolling SPA (max ~5min)...")
            spa = json.loads(await asyncio.wait_for(page2.evaluate(JS_SPA), timeout=360))
            log("scroll: %s" % json.dumps(spa, ensure_ascii=False))

    # 缺口拆解：以 plain 变体的全量 id 为 listed（plain n 只是首页，故再用 API 匿名逐页补全）
    import urllib.request
    UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
    listed, declared = set(), None
    p = 0
    while True:
        req = urllib.request.Request("https://api.iwara.tv/playlist/%s?page=%d&limit=50" % (a.playlist, p),
                                     headers={"User-Agent": UA})
        b = json.loads(urllib.request.urlopen(req, timeout=30).read())
        declared = b.get("numVideos")
        res = b.get("results") or []
        listed |= {x["id"] for x in res}
        if len(res) < 50:
            break
        p += 1
        await asyncio.sleep(0.25)
    priv = [v for v in audit["v403"] if v["s"] == 403]
    dead = [v for v in audit["v403"] if v["s"] == 404]
    gap = {
        "declared": declared,
        "listed": len(listed),
        "private_403": len(priv),
        "deleted_404": len(dead),
        "unexplained": (declared or 0) - len(listed) - len(priv) - len(dead),
        "listed_not_in_suspect": sorted(listed - {s for s in suspects}),
        "suspect_in_listed": sorted({s for s in suspects} & listed),
    }
    res = {"playlist": a.playlist, "login": login, "variants": audit["variants"],
           "v403": audit["v403"], "spa": spa, "gap": gap}
    json.dump(res, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    log("SAVED %s" % a.out)
    log("GAP: declared=%s listed=%s private=%s deleted=%s unexplained=%s"
        % (gap["declared"], gap["listed"], gap["private_403"], gap["deleted_404"], gap["unexplained"]))
    log("conclusion: 登录不解锁 → 缺口=私密+已删，非 unlisted（见 playlist-write.md「歌单缺口」节）")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(130)
