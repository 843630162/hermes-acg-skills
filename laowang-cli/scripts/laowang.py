#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
laowang.vip (老王论坛 / Discuz! X3.4) CLI for humans and AI agents (Hermes).

stdlib only — runs on Windows / Linux / macOS.
Session + config: <HERMES_HOME>\\.laowang (or %USERPROFILE%\\.laowang; override with LAOWANG_HOME).
Credentials: LAOWANG_USERNAME / LAOWANG_PASSWORD env, or config.json in home.

JSON on stdout by default. Never buys without --confirm and --max-price.
"""
from __future__ import annotations

import argparse
import base64
import datetime
import html as htmlmod
import http.cookiejar
import json
import math
import os
import random
import re
import struct
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Force UTF-8 stdout/stderr (Windows consoles often default to GBK/cp1252)
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

BASE = "https://laowang.vip"
HOST = "laowang.vip"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36")
TN_SECRET = "GWDiugh398huiw0ioOYGd0934hew"
MOBILE = "/api/mobile/index.php?version=4"
MIN_INTERVAL = 1.5  # seconds between HTTP calls
TZ8 = datetime.timezone(datetime.timedelta(hours=8))

# magnet / pan / codes
LINK_RE = re.compile(
    r"(?:magnet:\?xt=urn:btih:[a-zA-Z0-9]+[^\s<\"']*"
    r"|https?://(?:pan\.baidu\.com|yun\.baidu\.com|www\.aliyundrive\.com|www\.alipan\.com|"
    r"www\.lanzou[a-z]*\.com|lanzou[a-z]*\.com|pan\.quark\.cn|drive\.uc\.cn|"
    r"www\.123pan\.com|www\.pikpak\.com|mypikpak\.com|ctfile\.com|url\d*\.ctfile\.com|"
    r"www\.mediafire\.com|drive\.google\.com)[^\s<\"']+"
    r"|ed2k://[^\s<\"']+)",
    re.I,
)
CODE_RE = re.compile(
    r"(?:提取码|密码|访问码|解锁码|提取密碼|pwd|password)\s*[:：=\s]\s*([A-Za-z0-9]{3,8})",
    re.I,
)


class Error(Exception):
    def __init__(self, message: str, code: str = "error"):
        super().__init__(message)
        self.code = code
        self.message = message


def home_dir() -> Path:
    env = os.environ.get("LAOWANG_HOME")
    if env:
        return Path(env).expanduser()
    # Prefer <HERMES_HOME>\.laowang on this host so runtime state writes stay off C:\
    hermes_root = Path("<HERMES_HOME>")
    legacy_home = Path.home() / ".laowang"
    if hermes_root.exists():
        hermes_home = hermes_root / ".laowang"
        if not hermes_home.exists() and legacy_home.exists():
            hermes_home.mkdir(parents=True, exist_ok=True)
            for fname in ("state.json", "config.json"):
                src = legacy_home / fname
                dst = hermes_home / fname
                if src.exists() and not dst.exists():
                    dst.write_bytes(src.read_bytes())
        return hermes_home
    return legacy_home


def ensure_home() -> Path:
    h = home_dir()
    h.mkdir(parents=True, exist_ok=True)
    return h


def state_path() -> Path:
    return ensure_home() / "state.json"


def config_path() -> Path:
    return ensure_home() / "config.json"


def emit(obj: Any, as_json: bool = True) -> None:
    if as_json:
        print(json.dumps(obj, ensure_ascii=False, indent=2))
    else:
        print(obj)


def now_iso() -> str:
    return datetime.datetime.now(TZ8).strftime("%Y-%m-%d %H:%M:%S %z")


# ---------------- PNG + TNCode (port of site captcha) ----------------
def decode_png(data: bytes):
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise Error("captcha is not PNG", "captcha")
    p, idat = 8, b""
    w = h = bd = ct = il = None
    while p < len(data):
        ln = struct.unpack(">I", data[p:p + 4])[0]
        typ = data[p + 4:p + 8]
        ch = data[p + 8:p + 8 + ln]
        p += 12 + ln
        if typ == b"IHDR":
            w, h, bd, ct, _, _, il = struct.unpack(">IIBBBBB", ch)
        elif typ == b"IDAT":
            idat += ch
        elif typ == b"IEND":
            break
    if None in (w, h) or bd != 8 or il != 0 or ct not in (2, 6):
        raise Error(f"unsupported PNG {w}x{h}", "captcha")
    bpp = 3 if ct == 2 else 4
    raw = zlib.decompress(idat)
    stride = w * bpp
    out, prev, i = [], bytearray(stride), 0
    for _ in range(h):
        f = raw[i]
        line = bytearray(raw[i + 1:i + 1 + stride])
        i += 1 + stride
        for x in range(stride):
            a = line[x - bpp] if x >= bpp else 0
            b = prev[x]
            c = prev[x - bpp] if x >= bpp else 0
            if f == 1:
                line[x] = (line[x] + a) & 255
            elif f == 2:
                line[x] = (line[x] + b) & 255
            elif f == 3:
                line[x] = (line[x] + ((a + b) >> 1)) & 255
            elif f == 4:
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                pr = a if pa <= pb and pa <= pc else (b if pb <= pc else c)
                line[x] = (line[x] + pr) & 255
        out.append([tuple(line[x * bpp:x * bpp + 3]) for x in range(w)])
        prev = line
    return w, h, out


def _band(px, n):
    return px[n * 150:(n + 1) * 150]


def _piece_mask(mid):
    M = [[sum(mid[y][x]) > 0 for x in range(50)] for y in range(150)]
    ys = [y for y in range(150) if any(M[y])]
    xs = [x for x in range(50) if any(M[y][x] for y in range(150))]
    if not ys:
        raise Error("empty captcha piece", "captcha")
    y0, y1, x0, x1 = ys[0], ys[-1], xs[0], xs[-1]
    for x in range(50):
        M[y0][x] = M[y1][x] = False
    for y in range(150):
        M[y][x0] = M[y][x1] = False
    return M


def _erode(M, n=4):
    for _ in range(n):
        N = [[False] * 50 for _ in range(150)]
        for y in range(1, 149):
            for x in range(1, 49):
                if M[y][x] and M[y - 1][x] and M[y + 1][x] and M[y][x - 1] and M[y][x + 1]:
                    N[y][x] = True
        M = N
    return M


def find_offset(px) -> int:
    mid, bot = _band(px, 1), _band(px, 2)
    M = _piece_mask(mid)
    E = _erode(M, 4)
    pts = [(x, y) for y in range(150) for x in range(50) if E[y][x]]
    if len(pts) < 40:
        E = _erode(M, 2)
        pts = [(x, y) for y in range(150) for x in range(50) if E[y][x]]
    if not pts:
        raise Error("captcha piece too small", "captcha")
    best, best_s = 0, 1e18
    for off in range(0, 191):
        s = 0
        for x, y in pts:
            a, b = mid[y][x], bot[y][off + x]
            s += abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2])
        if s < best_s:
            best_s, best = s, off
    return best


def gen_track(offset: float, duration_ms: Optional[int] = None):
    max_off = 190.0
    target = max(0.0, min(float(offset), max_off))
    duration = duration_ms or random.randint(700, 1400)
    n = random.randint(28, 48)
    start_x = random.uniform(40, 90)
    start_y = random.uniform(420, 520)
    pts = []
    for i in range(n):
        t = i / (n - 1)
        ease = 1 - (1 - t) ** 3
        if t > 0.85:
            ease = min(1.0, ease + random.uniform(-0.01, 0.015))
        x = start_x + target * ease + random.uniform(-0.6, 0.6)
        y = start_y + random.uniform(-1.2, 1.2) + 0.4 * math.sin(t * 6)
        ms = int(duration * (t + random.uniform(-0.004, 0.004)))
        if i == 0:
            ms, x, y = 0, start_x, start_y
        if i == n - 1:
            ms, x = duration, start_x + target
        pts.append({"x": round(x, 2), "y": round(y, 2), "t": max(0, ms)})
    return pts


def generate_secure_payload(track_data, mark_offset, secret=TN_SECRET) -> str:
    track_info: Dict[str, Any] = {"valid": False}
    if len(track_data) >= 2:
        speeds, directions = [], []
        total_dist = 0.0
        for i in range(1, len(track_data)):
            dx = track_data[i]["x"] - track_data[i - 1]["x"]
            dy = track_data[i]["y"] - track_data[i - 1]["y"]
            dt = track_data[i]["t"] - track_data[i - 1]["t"]
            if dt > 0:
                dist = math.sqrt(dx * dx + dy * dy)
                total_dist += dist
                speeds.append(dist / dt)
                directions.append(math.atan2(dy, dx))
        avg = sum(speeds) / len(speeds) if speeds else 0.0
        var = sum((s - avg) ** 2 for s in speeds) / len(speeds) if speeds else 0.0
        dch = sum(1 for i in range(1, len(directions))
                  if abs(directions[i] - directions[i - 1]) > math.pi / 4)
        track_info = {
            "valid": True, "points": len(track_data),
            "totalTime": track_data[-1]["t"], "totalDist": total_dist,
            "avgSpeed": avg, "maxSpeed": max(speeds) if speeds else 0.0,
            "minSpeed": min(speeds) if speeds else 0.0, "speedVar": var,
            "dirChanges": dch,
            "finalX": track_data[-1]["x"] - track_data[0]["x"],
        }
    track_str = json.dumps(track_info, separators=(",", ":"), ensure_ascii=False)
    normalized = f"{float(mark_offset):.2f}"
    ts = int(time.time() * 1000)
    xor = "".join(chr(ord(track_str[i]) ^ ord(secret[i % len(secret)]))
                  for i in range(len(track_str)))
    encrypted = base64.b64encode(xor.encode("latin-1")).decode("ascii")
    combined = track_str + str(ts) + normalized + secret
    hashv = 0x811c9dc5
    for ch in combined:
        hashv ^= ord(ch)
        hashv = (hashv + ((hashv << 1) + (hashv << 4) + (hashv << 7) +
                          (hashv << 8) + (hashv << 24))) & 0xffffffff
    return (f"tn_r={normalized}&track={urllib.parse.quote(encrypted, safe='')}"
            f"&ts={ts}&sign={format(hashv, 'x')}")


def _h32(s: str) -> str:
    h = 0x811c9dc5
    for ch in s:
        h ^= ord(ch)
        h = (h * 0x01000193) & 0xffffffff
    return "%08x" % h


def make_fingerprint() -> str:
    canvas = base64.b64encode(os.urandom(30)).decode()[-40:]
    raw = "||".join([
        UA, "zh-CN,zh,en", "1920x1080x24", "-480", "8", "8", "Win32", canvas,
        "ANGLE (Intel, Intel(R) UHD Graphics 630 Direct3D11 vs_5_0 ps_5_0, D3D11)"])
    a = _h32(raw)
    b = _h32(a + raw[:len(raw) >> 1])
    c = _h32(b + raw[len(raw) >> 1:])
    d = _h32(c + str(len(raw)))
    return a + b + c + d


# ---------------- cookies / state ----------------
def jar_to_list(jar: http.cookiejar.CookieJar) -> List[dict]:
    return [{"name": c.name, "value": c.value, "domain": c.domain, "path": c.path,
             "expires": c.expires, "secure": c.secure, "rest": c._rest,
             "domain_specified": c.domain_specified,
             "domain_initial_dot": c.domain_initial_dot} for c in jar]


def mk_cookie(name, value, domain=HOST, path="/", expires=None, secure=False, rest=None,
              domain_specified=False, domain_initial_dot=False):
    return http.cookiejar.Cookie(
        0, name, value, None, False, domain, domain_specified, domain_initial_dot,
        path, True, secure, expires, expires is None, None, None, rest or {})


def list_to_jar(items, jar: http.cookiejar.CookieJar) -> None:
    for d in items or []:
        jar.set_cookie(mk_cookie(
            d["name"], d["value"], d["domain"], d.get("path", "/"), d.get("expires"),
            d.get("secure", False), d.get("rest"), d.get("domain_specified", False),
            d.get("domain_initial_dot", False)))


def load_state() -> dict:
    p = state_path()
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {}


def save_state(state: dict) -> None:
    p = state_path()
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        os.replace(str(tmp), str(p))
    except Exception:
        # Windows: replace can fail if target open; fallback
        if p.exists():
            p.unlink()
        tmp.rename(p)


def load_cred() -> Tuple[str, str]:
    user = os.environ.get("LAOWANG_USERNAME")
    pw = os.environ.get("LAOWANG_PASSWORD")
    cfg = config_path()
    if cfg.exists():
        c = json.loads(cfg.read_text(encoding="utf-8"))
        user = user or c.get("username")
        pw = pw or c.get("password")
    if not user or not pw:
        raise Error("missing credentials: set LAOWANG_USERNAME/LAOWANG_PASSWORD "
                    f"or write {cfg} with username/password", "auth")
    return user, pw


def text_of(h: str, n: int = 300) -> str:
    h = re.sub(r"(?is)<script.*?</script>|<style.*?</style>", " ", h or "")
    h = re.sub(r"<!\[CDATA\[|\]\]>|<[^>]+>", " ", h)
    return re.sub(r"\s+", " ", htmlmod.unescape(h)).strip()[:n]


# ---------------- HTTP client ----------------
class Client:
    def __init__(self, state: Optional[dict] = None):
        self.state = state if state is not None else load_state()
        self.jar = http.cookiejar.CookieJar()
        list_to_jar(self.state.get("cookies"), self.jar)
        self._ensure_agree()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.jar))
        self._last_req = 0.0
        if not self.state.get("fingerprint"):
            self.state["fingerprint"] = make_fingerprint()

    def _ensure_agree(self):
        if not any(c.name == "is_agree" for c in self.jar):
            self.jar.set_cookie(mk_cookie(
                "is_agree", "1", expires=int(time.time()) + 30 * 86400))

    def persist(self):
        self.state["cookies"] = jar_to_list(self.jar)
        save_state(self.state)

    def cookie(self, name: str) -> Optional[str]:
        for c in self.jar:
            if c.name == name:
                return c.value
        return None

    def _throttle(self):
        dt = time.time() - self._last_req
        if dt < MIN_INTERVAL:
            time.sleep(MIN_INTERVAL - dt)

    def request(self, method: str, path: str, data=None, headers=None, binary=False):
        self._throttle()
        url = path if path.startswith("http") else BASE + path
        h = {"User-Agent": UA, "Accept-Language": "zh-CN,zh;q=0.9",
             "Accept": "*/*", "Referer": BASE + "/", "Origin": BASE}
        if headers:
            h.update(headers)
        body = None
        if data is not None:
            if isinstance(data, dict):
                body = urllib.parse.urlencode(data).encode()
            elif isinstance(data, str):
                body = data.encode()
            else:
                body = data
            h.setdefault("Content-Type", "application/x-www-form-urlencoded")
        req = urllib.request.Request(url, data=body, headers=h, method=method)
        try:
            r = self.opener.open(req, timeout=45)
            st, hdrs, raw = r.status, r.headers, r.read()
        except urllib.error.HTTPError as e:
            st, hdrs, raw = e.code, e.headers, e.read()
        except Exception as e:
            raise Error(f"network {path}: {type(e).__name__}: {e}", "network")
        self._last_req = time.time()
        if binary:
            return st, hdrs, raw
        return st, hdrs, raw.decode("utf-8", "replace")

    def get(self, path, **kw):
        return self.request("GET", path, **kw)

    def post(self, path, data, **kw):
        return self.request("POST", path, data=data, **kw)

    def mobile(self, module: str, **params) -> dict:
        q = urllib.parse.urlencode({"module": module, **{k: v for k, v in params.items() if v is not None}})
        st, _, body = self.get(f"{MOBILE}&{q}",
                               headers={"Accept": "application/json"})
        if st != 200:
            raise Error(f"mobile {module} HTTP {st}", "http")
        try:
            return json.loads(body)
        except Exception:
            raise Error(f"mobile {module} non-JSON: {body[:120]!r}", "http")

    def is_logged_in(self) -> bool:
        return bool(self.cookie("X9wU_2132_auth"))

    def solve_captcha(self, tries: int = 3) -> str:
        last = None
        for i in range(tries):
            if i:
                time.sleep(random.uniform(2.0, 3.5))
            st, _, raw = self.get(
                f"/captcha/tncode.php?t={random.random()}&nowebp=1", binary=True)
            if st != 200 or not raw.startswith(b"\x89PNG"):
                last = f"image HTTP {st}"
                continue
            offset = find_offset(decode_png(raw)[2])
            body = generate_secure_payload(gen_track(offset), offset)
            st, _, txt = self.post(
                "/captcha/check.php", body,
                headers={"Content-Type": "application/x-www-form-urlencoded",
                         "X-Requested-With": "XMLHttpRequest"})
            if "_ok" in (txt or ""):
                return txt.strip()
            last = txt.strip()
        raise Error(f"captcha failed after {tries}: {last}", "captcha")

    def login(self, force: bool = False) -> dict:
        if self.is_logged_in() and not force:
            info = self.whoami()
            info["note"] = "already logged in (pass force to re-login)"
            return info
        user, pw = load_cred()
        try:
            pw.encode("ascii")
        except UnicodeEncodeError:
            raise Error("password must be ASCII-only for this site", "auth")
        for c in list(self.jar):
            if c.name.endswith("_auth") or c.name.endswith("_sid"):
                self.jar.clear(c.domain, c.path, c.name)
        st, _, page = self.get("/member.php?mod=logging&action=login")
        if st != 200:
            raise Error(f"login page HTTP {st}", "auth")
        m_hash = re.search(r"loginhash=([A-Za-z0-9]+)", page)
        m_form = re.search(r'name="formhash"\s+value="([a-f0-9]+)"', page)
        if not m_hash or not m_form:
            raise Error("loginhash/formhash missing", "auth")
        loginhash, formhash = m_hash.group(1), m_form.group(1)
        token = self.solve_captcha()
        pw_enc = "base64://" + base64.b64encode(pw.encode("ascii")).decode("ascii")
        data = {
            "formhash": formhash, "referer": BASE + "/forum.php",
            "loginfield": "username", "username": user, "password": pw_enc,
            "questionid": "0", "answer": "", "cookietime": "2592000",
            "clicaptcha-submit-info": token,
        }
        path = (f"/member.php?mod=logging&action=login&loginsubmit=yes"
                f"&loginhash={loginhash}&inajax=1")
        st, _, txt = self.post(path, data, headers={
            "Referer": BASE + "/member.php?mod=logging&action=login",
            "X-Requested-With": "XMLHttpRequest"})
        if re.search(r"安全提问|请填写安全提问", txt) and "登录成功" not in txt:
            raise Error("account requires security question (questionid/answer)", "auth")
        self.get("/forum.php")
        if not self.is_logged_in():
            raise Error(f"login failed: {text_of(txt, 200)}", "auth")
        self.state["last_login"] = int(time.time())
        self.persist()
        return self.whoami()

    def ensure_login(self):
        if not self.is_logged_in():
            self.login()

    def whoami(self) -> dict:
        self.ensure_login()
        d = self.mobile("profile")
        # profile without uid uses current user when logged in; some builds need uid
        v = d.get("Variables") or {}
        space = v.get("space") or {}
        if not space.get("uid"):
            # retry with member_uid from forumindex
            fi = self.mobile("forumindex")
            uid = (fi.get("Variables") or {}).get("member_uid")
            if uid:
                d = self.mobile("profile", uid=uid)
                v = d.get("Variables") or {}
                space = v.get("space") or {}
        ext = v.get("extcredits") or {}
        credits = {}
        for k, meta in ext.items():
            credits[meta.get("title") or f"ext{k}"] = {
                "id": int(k),
                "value": _to_num(space.get(f"extcredits{k}")),
                "unit": meta.get("unit") or "",
            }
        out = {
            "ok": True,
            "uid": space.get("uid") or v.get("member_uid"),
            "username": space.get("username") or v.get("member_username"),
            "groupid": space.get("groupid") or v.get("groupid"),
            "credits_total": _to_num(space.get("credits")),
            "balance": credits,
            "ruimeibi": credits.get("软妹币", {}).get("value"),
            "formhash": v.get("formhash"),
            "home": str(home_dir()),
            "time": now_iso(),
        }
        self.persist()
        return out


def _to_num(x):
    try:
        if x is None or x == "":
            return None
        return int(str(x).replace(",", ""))
    except Exception:
        try:
            return float(x)
        except Exception:
            return x


# ---------------- commands ----------------
def cmd_login(args):
    c = Client()
    info = c.login(force=args.force)
    emit(info)
    return 0


def cmd_whoami(args):
    c = Client()
    emit(c.whoami())
    return 0


def cmd_balance(args):
    c = Client()
    w = c.whoami()
    emit({
        "ok": True,
        "uid": w["uid"],
        "username": w["username"],
        "ruimeibi": w.get("ruimeibi"),
        "credits_total": w.get("credits_total"),
        "balance": w.get("balance"),
        "time": now_iso(),
    })
    return 0


def cmd_forums(args):
    c = Client()
    c.ensure_login()
    d = c.mobile("forumindex")
    v = d.get("Variables") or {}
    cats = v.get("catlist") or []
    forums = v.get("forumlist") or []
    fmap = {str(f.get("fid")): f for f in forums}
    out_cats = []
    for cat in cats:
        children = []
        for fid in cat.get("forums") or []:
            f = fmap.get(str(fid))
            if not f:
                continue
            children.append({
                "fid": _to_num(f.get("fid")),
                "name": f.get("name"),
                "threads": _to_num(f.get("threads")),
                "posts": _to_num(f.get("posts")),
                "todayposts": _to_num(f.get("todayposts")),
                "description": f.get("description") or "",
            })
        out_cats.append({
            "fid": _to_num(cat.get("fid")),
            "name": cat.get("name"),
            "forums": children,
        })
    emit({
        "ok": True,
        "categories": out_cats,
        "forum_count": len(forums),
        "member_uid": v.get("member_uid"),
        "member_username": v.get("member_username"),
        "member_credits": _to_num(v.get("member_credits")),
    })
    c.persist()
    return 0


def parse_search_html(html: str) -> dict:
    total = None
    m = re.search(r"大约有\s*<b>([\d,]+)</b>", html)
    if m:
        total = _to_num(m.group(1))
    results = []
    for block in re.finditer(
            r'<div class="result-item\s+uid_hidden_(\d+)"[^>]*>(.*?)</div>\s*</div>',
            html, re.S):
        author_id, inner = block.group(1), block.group(2)
        tm = re.search(r'viewthread&amp;tid=(\d+)', inner)
        if not tm:
            continue
        tid = tm.group(1)
        title_m = re.search(r'class="result-title".*?<a[^>]*>(.*?)</a>', inner, re.S)
        title = text_of(title_m.group(1), 200) if title_m else ""
        title = re.sub(r"^\d+\.\s*", "", title)
        title = re.sub(r"\[相关度：[^\]]+\]", "", title).strip()
        snippet_m = re.search(r'class="result-content">(.*?)</div>', inner, re.S)
        snippet = text_of(snippet_m.group(1), 300) if snippet_m else ""
        forum = author = date = None
        fm = re.search(r"板块:</strong>\s*<span>([^<]+)", inner)
        am = re.search(r"作者:</strong>\s*<span>.*?>([^<]+)</a>", inner, re.S)
        dm = re.search(r"发表时间:</strong>\s*<span>([^<]+)", inner)
        if fm:
            forum = fm.group(1).strip()
        if am:
            author = am.group(1).strip()
        if dm:
            date = dm.group(1).strip()
        rel = None
        rm = re.search(r"相关度：(\d+)%", inner)
        if rm:
            rel = int(rm.group(1))
        results.append({
            "tid": int(tid), "title": title, "forum": forum,
            "author": author, "author_id": int(author_id) if author_id.isdigit() else author_id,
            "date": date, "snippet": snippet, "relevance": rel,
            "url": f"{BASE}/forum.php?mod=viewthread&tid={tid}",
        })
    return {"total": total, "results": results}


def cmd_search(args):
    c = Client()
    c.ensure_login()
    params = {"q": args.keyword, "f": args.field, "p": str(args.page), "s": "relevance"}
    if args.forum:
        params["fid"] = str(args.forum)
    q = urllib.parse.urlencode(params)
    st, _, html = c.get(f"/search/s.php?{q}")
    if st != 200:
        raise Error(f"search HTTP {st}", "http")
    # flood / captcha detection
    if "tncode" in html or "secqaa" in html or "seccode" in html:
        raise Error("search requires captcha (rate limited?)", "captcha")
    if any(w in html for w in ("搜索过于频繁", "请稍候再试", "flood", "两次搜索")):
        raise Error(f"search flood control: {text_of(html, 160)}", "flood")
    parsed = parse_search_html(html)
    emit({
        "ok": True,
        "keyword": args.keyword,
        "field": args.field,
        "forum": args.forum,
        "page": args.page,
        "total": parsed["total"],
        "count": len(parsed["results"]),
        "results": parsed["results"],
    })
    c.persist()
    return 0


def extract_links_and_codes(text: str) -> Tuple[List[str], List[str]]:
    links = list(dict.fromkeys(LINK_RE.findall(text or "")))
    codes = list(dict.fromkeys(m.group(1) for m in CODE_RE.finditer(text or "")))
    return links, codes


def _encode_non_ascii_url(url: str) -> str:
    if not url:
        return ""
    if url.startswith("/"):
        url = BASE + url
    parts = urllib.parse.urlsplit(url)
    try:
        decoded_path = urllib.parse.unquote(parts.path)
    except Exception:
        decoded_path = parts.path
    encoded_path = urllib.parse.quote(decoded_path, safe="/:@!$&'()*+,;=-._~")
    return urllib.parse.urlunsplit((parts.scheme, parts.netloc, encoded_path, parts.query, parts.fragment))


def resolve_remote_play(c: Client, html_text: str) -> List[dict]:
    vids = list(dict.fromkeys(re.findall(r"/remote_play/video/play/(\d+)\.html", html_text or "")))
    items = []
    for vid in vids:
        try:
            st, _, body = c.get(f"/remote_play/index.php/play/ajax/{vid}.html",
                                headers={"X-Requested-With": "XMLHttpRequest"})
            if st != 200:
                continue
            data = json.loads(body)
        except Exception:
            continue
        playlink = data.get("playlink") or ""
        piclink = data.get("piclink") or ""
        dl_page = data.get("download") or ""
        m3u8_url = _encode_non_ascii_url(playlink) if playlink else None
        pic_url = _encode_non_ascii_url(piclink) if piclink else None
        torrent_url = None
        if dl_page and str(dl_page) != "0":
            try:
                st2, _, dl_html = c.get(dl_page if dl_page.startswith("/") or dl_page.startswith("http")
                                        else "/" + dl_page)
                if st2 == 200:
                    tm = re.search(
                        r'(?:https?://[^\s"\'<>]+?\.torrent|/remote_m3u8/torrents/[^\s"\'<>]+?\.torrent)',
                        dl_html)
                    if tm:
                        torrent_url = _encode_non_ascii_url(htmlmod.unescape(tm.group(0)))
            except Exception:
                pass
        items.append({
            "video_id": int(vid) if vid.isdigit() else vid,
            "title": data.get("title"),
            "m3u8_url": m3u8_url,
            "torrent_url": torrent_url,
            "pic_url": pic_url,
            "download_page": (BASE + dl_page if str(dl_page).startswith("/") else dl_page) if dl_page and str(dl_page) != "0" else None,
        })
    return items


def check_pansell_links(c: Client, tid: int, html_text: str) -> List[dict]:
    ks = list(dict.fromkeys(re.findall(r"jnpar_pansell:check&amp;tid=\d+&amp;k=(\d+)", html_text or "")))
    checks = []
    for k in ks:
        try:
            st, _, body = c.get(
                f"/plugin.php?id=jnpar_pansell:check&tid={tid}&k={k}&inajax=1",
                headers={"X-Requested-With": "XMLHttpRequest",
                         "Referer": f"{BASE}/forum.php?mod=viewthread&tid={tid}"})
            if st != 200:
                continue
            unesc = htmlmod.unescape(body or "")
            valid = ("/img/true.png" in unesc) or ("此链接目前有效" in unesc)
            invalid = ("/img/false.png" in unesc) or ("已经失效" in unesc)
            lm = re.search(r'<p[^>]*style="[^"]*display\s*:\s*none[^"]*"[^>]*>(.*?)</p>',
                           unesc, re.I | re.S)
            leaked = lm.group(1).strip() if lm and lm.group(1).strip() else None
            checks.append({
                "k": int(k) if k.isdigit() else k,
                "valid": True if valid else (False if invalid else None),
                "leaked_url": leaked,
            })
        except Exception:
            continue
    return checks


def parse_pv_card(html_text: str) -> Optional[dict]:
    """Parse the jnpar_pansell #downcon .pv-card block.

    Maps each resource title to its file entries ([size]link — magnets, pan
    links), which the flat `links` array loses. Card contents are
    double HTML-escaped, so unescape twice.
    """
    if not html_text:
        return None
    m = re.search(r'<div[^>]*class="pv-card"', html_text)
    if not m:
        return None
    depth, end = 0, len(html_text)
    for dm in re.finditer(r"<div\b|</div>", html_text[m.start():]):
        if dm.group(0) == "<div":
            depth += 1
        else:
            depth -= 1
            if depth == 0:
                end = m.start() + dm.end()
                break
    region = html_text[m.start():end]

    def clean(s: str) -> str:
        s = htmlmod.unescape(s)
        if "&amp;" in s:
            s = htmlmod.unescape(s)
        return re.sub(r"\s+", " ", s).strip()

    card: Dict[str, Any] = {"status": "locked", "price": None, "purchased": None, "files": []}
    sm = re.search(r"<strong>\s*(.*?)\s*</strong>", region, re.S)
    if sm and clean(sm.group(1)) in ("已解锁", "已购买", "已购", "解锁"):
        card["status"] = "unlocked"
    pm = re.search(r'class="pv-price">\s*(\d+)', region) or re.search(r"售价\s*(\d+)\s*软妹币", region)
    if pm:
        card["price"] = int(pm.group(1))
    em = re.search(r"<em>\s*已购\s*(\d+)", region)
    if em:
        card["purchased"] = int(em.group(1))

    current_title: Optional[str] = None
    for raw in re.findall(r'<div class="pv-file">(.*?)</div>', region, re.S):
        txt = clean(raw)
        if not txt or txt.startswith("售价"):
            continue
        fm = re.match(r"^\[([^\]]+)\]\s*(\S+)", txt)
        if fm and re.match(r"^(magnet:|https?://|ed2k://)", fm.group(2), re.I):
            entry: Dict[str, Any] = {
                "title": current_title,
                "size": fm.group(1).strip(),
                "url": fm.group(2),
            }
            cm = CODE_RE.search(txt[fm.end():])
            if cm:
                entry["code"] = cm.group(1)
            card["files"].append(entry)
        else:
            current_title = txt
    return card


def resolve_forum_name(c: Client, fid) -> Optional[str]:
    if fid is None:
        return None
    cache = c.state.setdefault("_forum_names", {})
    key = str(fid)
    if key in cache:
        return cache[key]
    try:
        d = c.mobile("forumindex")
        for f in (d.get("Variables") or {}).get("forumlist") or []:
            cache[str(f.get("fid"))] = f.get("name")
        c.persist()
    except Exception:
        pass
    return cache.get(key)


def parse_thread(c: Client, tid: int) -> dict:
    d = c.mobile("viewthread", tid=str(tid))
    v = d.get("Variables") or {}
    t = v.get("thread") or {}
    posts_raw = v.get("postlist") or []
    if isinstance(posts_raw, dict):
        posts_raw = list(posts_raw.values())
    posts = []
    all_links, all_codes = [], []
    attachments = []
    for p in posts_raw:
        msg = p.get("message") or ""
        plain = text_of(msg, 8000)
        links, codes = extract_links_and_codes(msg + "\n" + plain)
        all_links.extend(links)
        all_codes.extend(codes)
        atts = p.get("attachments") or {}
        if isinstance(atts, dict):
            for aid, a in atts.items():
                price = _to_num(a.get("price") or a.get("attachprice") or 0) or 0
                attachments.append({
                    "aid": _to_num(a.get("aid") or aid),
                    "filename": a.get("filename"),
                    "filesize": _to_num(a.get("filesize")),
                    "price": price,
                    "payed": str(a.get("payed") or "0") in ("1", "true", "True"),
                    "isimage": str(a.get("isimage") or "0") in ("1", "true"),
                    "url": a.get("url"),
                    "attachment": a.get("attachment"),
                })
        posts.append({
            "pid": _to_num(p.get("pid")),
            "author": p.get("author"),
            "authorid": _to_num(p.get("authorid")),
            "dateline": p.get("dateline"),
            "first": str(p.get("first") or "0") == "1",
            "message_html": msg,
            "message_text": plain,
            "links": links,
            "codes": codes,
        })

    # HTML pass: catch attachpay / thread pay / pansell / hide / remote_play that mobile may miss
    st, _, html = c.get(f"/forum.php?mod=viewthread&tid={tid}")
    paid_status = {
        "thread_price": _to_num(t.get("price")) or 0,
        "pansell_price": 0,
        "needs_thread_pay": False,
        "needs_pansell_pay": False,
        "needs_attach_pay": False,
        "needs_reply_to_view": False,
        "hidden_locked": False,
    }
    remote_videos = []
    pv_card: Optional[dict] = None
    if st == 200:
        if re.search(r"mod=misc&amp;action=pay&amp;tid=", html) or "购买主题" in html:
            paid_status["needs_thread_pay"] = True
        if "jnpar_pansell:pay" in html or 'class="pv-card"' in html:
            paid_status["needs_pansell_pay"] = True
            pv_card = parse_pv_card(html)
            pm_pan = re.search(r'class="pv-price">\s*(\d+)\s*<i>\s*软妹币', html)
            if pm_pan:
                paid_status["pansell_price"] = int(pm_pan.group(1))
                if not paid_status["thread_price"]:
                    paid_status["thread_price"] = int(pm_pan.group(1))
            pansell_checks = check_pansell_links(c, tid, html)
            if pansell_checks:
                paid_status["pansell_checks"] = pansell_checks
                for chk in pansell_checks:
                    if chk.get("leaked_url"):
                        all_links.append(chk["leaked_url"])
        if "action=attachpay" in html:
            paid_status["needs_attach_pay"] = True
            # enrich attachment prices from HTML
            for m in re.finditer(
                    r'action=attachpay&amp;aid=(\d+)&amp;tid=\d+[^>]*>.*?</a>'
                    r'.*?售价:\s*<strong>\s*(\d+)\s*软妹币',
                    html, re.S):
                aid, price = int(m.group(1)), int(m.group(2))
                for a in attachments:
                    if a["aid"] == aid:
                        a["price"] = price
            # simpler: aid + nearby 售价
            for m in re.finditer(
                    r'attachpay&amp;aid=(\d+)&amp;tid=(\d+)', html):
                aid = int(m.group(1))
                win = html[m.start():m.start() + 500]
                pm = re.search(r"售价:\s*<strong>\s*(\d+)\s*软妹币", win)
                if pm:
                    price = int(pm.group(1))
                    for a in attachments:
                        if a["aid"] == aid and not a["price"]:
                            a["price"] = price
        if "回复后可见" in html or "回复才能看" in html:
            paid_status["needs_reply_to_view"] = True
        if 'class="locked"' in html or "本帖隐藏的内容" in html:
            paid_status["hidden_locked"] = True
        # extra links from full HTML
        links2, codes2 = extract_links_and_codes(html)
        all_links.extend(links2)
        all_codes.extend(codes2)
        remote_videos = resolve_remote_play(
            c, html + "\n" + "\n".join(p.get("message_html") or "" for p in posts))
        for rv in remote_videos:
            if rv.get("torrent_url"):
                all_links.append(rv["torrent_url"])
            if rv.get("m3u8_url"):
                all_links.append(rv["m3u8_url"])

    # dedupe
    all_links = list(dict.fromkeys(all_links))
    all_codes = list(dict.fromkeys(all_codes))
    paid_atts = [a for a in attachments if (a.get("price") or 0) > 0 and not a.get("payed")]
    if paid_atts:
        paid_status["needs_attach_pay"] = True

    forum = v.get("forum") or {}
    if isinstance(forum, str):
        forum_name = forum
    elif isinstance(forum, dict):
        forum_name = forum.get("name")
    else:
        forum_name = None
    fid_n = _to_num(t.get("fid") or v.get("fid"))
    if not forum_name:
        forum_name = resolve_forum_name(c, fid_n)
    return {
        "ok": True,
        "tid": int(tid),
        "fid": fid_n,
        "forum": forum_name,
        "subject": t.get("subject"),
        "author": t.get("author"),
        "authorid": _to_num(t.get("authorid")),
        "dateline": t.get("dateline"),
        "replies": _to_num(t.get("replies")),
        "views": t.get("views"),
        "readperm": _to_num(t.get("readperm")),
        "price": paid_status["thread_price"],
        "paid": paid_status,
        "attachments": attachments,
        "unpaid_attachments": paid_atts,
        "remote_play": remote_videos,
        "pv_card": pv_card,
        "links": all_links,
        "codes": all_codes,
        "posts": posts,
        "formhash": v.get("formhash"),
        "url": f"{BASE}/forum.php?mod=viewthread&tid={tid}",
    }


def cmd_thread(args):
    c = Client()
    c.ensure_login()
    emit(parse_thread(c, int(args.tid)))
    c.persist()
    return 0


def preview_attach_pay(c: Client, tid: int, aid: int) -> dict:
    path = (f"/forum.php?mod=misc&action=attachpay&aid={aid}&tid={tid}"
            f"&inajax=1&infloat=yes&handlekey=attachpay")
    st, _, body = c.get(path, headers={
        "X-Requested-With": "XMLHttpRequest",
        "Referer": f"{BASE}/forum.php?mod=viewthread&tid={tid}"})
    if st != 200:
        raise Error(f"attachpay preview HTTP {st}", "http")
    formhash_m = re.search(r'name="formhash"\s+value="([^"]+)"', body)
    price_m = re.search(r"售价\(软妹币\)\s*</td>\s*<td>\s*(\d+)", body)
    bal_m = re.search(r"购买后余额\(软妹币\)\s*</td>\s*<td>\s*(\d+)", body)
    name_m = re.search(r"<td>附件</td>\s*<td><div[^>]*>([^<]+)", body)
    author_m = re.search(r"<td>作者</td>\s*<td><a[^>]*>([^<]+)", body)
    if "您已经购买" in body or "已经购买" in body:
        return {"ok": True, "already_bought": True, "tid": tid, "aid": aid,
                "raw": text_of(body, 200)}
    if not formhash_m:
        raise Error(f"attachpay form missing: {text_of(body, 200)}", "pay")
    return {
        "ok": True,
        "type": "attachpay",
        "tid": tid,
        "aid": aid,
        "filename": (name_m.group(1).strip() if name_m else None),
        "author": (author_m.group(1).strip() if author_m else None),
        "price": int(price_m.group(1)) if price_m else None,
        "balance_after": int(bal_m.group(1)) if bal_m else None,
        "formhash": formhash_m.group(1),
        "currency": "软妹币",
        "dry_run": True,
    }


def preview_thread_pay(c: Client, tid: int) -> dict:
    path = f"/forum.php?mod=misc&action=pay&tid={tid}&inajax=1&infloat=yes&handlekey=pay"
    st, _, body = c.get(path, headers={
        "X-Requested-With": "XMLHttpRequest",
        "Referer": f"{BASE}/forum.php?mod=viewthread&tid={tid}"})
    formhash_m = re.search(r'name="formhash"\s+value="([^"]+)"', body)
    # Discuz pay table varies; capture numbers near 售价/价格
    price = None
    for pat in [r"主题售价[^<\d]*(\d+)", r"售价[^<\d]*(\d+)\s*软妹币",
                r"价格[^<\d]*(\d+)"]:
        m = re.search(pat, body)
        if m:
            price = int(m.group(1))
            break
    if not formhash_m and "已经购买" not in body and "免费" not in body:
        raise Error(f"thread pay form missing: {text_of(body, 200)}", "pay")
    return {
        "ok": True,
        "type": "threadpay",
        "tid": tid,
        "price": price,
        "formhash": formhash_m.group(1) if formhash_m else None,
        "currency": "软妹币",
        "already_bought": "已经购买" in body,
        "snippet": text_of(body, 240),
        "dry_run": True,
    }


def preview_pansell_pay(c: Client, tid: int, price_hint: Optional[int] = None) -> dict:
    st_t, _, html = c.get(f"/forum.php?mod=viewthread&tid={tid}")
    if st_t != 200:
        raise Error(f"viewthread HTTP {st_t}", "http")
    pm = re.search(r'class="pv-price">\s*(\d+)\s*<i>\s*软妹币', html)
    price = int(pm.group(1)) if pm else price_hint
    pid_m = re.search(r'jnpar_pansell:pay&amp;tid=\d+&amp;pid=([^"&]*)', html)
    pid = pid_m.group(1) if pid_m else ""
    checks = check_pansell_links(c, tid, html)
    path = (f"/plugin.php?id=jnpar_pansell:pay&tid={tid}&pid={pid}"
            f"&infloat=yes&handlekey=dtpaytip&inajax=1")
    st, _, body = c.get(path, headers={
        "X-Requested-With": "XMLHttpRequest",
        "Referer": f"{BASE}/forum.php?mod=viewthread&tid={tid}"})
    formhash_m = re.search(r'name="formhash"\s+value="([^"]+)"', body)
    if not formhash_m and "已经购买" not in body and "已购" not in body:
        raise Error(f"pansell pay form missing: {text_of(body, 200)}", "pay")
    return {
        "ok": True,
        "type": "pansell",
        "tid": tid,
        "pid": pid,
        "price": price,
        "formhash": formhash_m.group(1) if formhash_m else None,
        "currency": "软妹币",
        "already_bought": "已经购买" in body,
        "pansell_checks": checks,
        "snippet": text_of(body, 240),
        "dry_run": True,
    }


def cmd_buy(args):
    c = Client()
    c.ensure_login()
    tid = int(args.tid)
    bal = c.whoami()
    ruimeibi = bal.get("ruimeibi")

    # resolve what to buy
    if args.aid:
        preview = preview_attach_pay(c, tid, int(args.aid))
    else:
        th = parse_thread(c, tid)
        unpaid = th.get("unpaid_attachments") or []
        if unpaid:
            # default: first unpaid attachment
            aid = unpaid[0]["aid"]
            if args.list_only:
                emit({"ok": True, "tid": tid, "balance_ruimeibi": ruimeibi,
                      "unpaid_attachments": unpaid, "thread_price": th.get("price"),
                      "paid": th.get("paid")})
                return 0
            preview = preview_attach_pay(c, tid, int(aid))
        elif th.get("paid", {}).get("needs_pansell_pay"):
            preview = preview_pansell_pay(c, tid, th.get("paid", {}).get("pansell_price"))
        elif (th.get("price") or 0) > 0 or th.get("paid", {}).get("needs_thread_pay"):
            preview = preview_thread_pay(c, tid)
        else:
            emit({"ok": True, "tid": tid, "nothing_to_buy": True,
                  "balance_ruimeibi": ruimeibi, "paid": th.get("paid"),
                  "attachments": th.get("attachments")})
            c.persist()
            return 0

    preview["balance_ruimeibi"] = ruimeibi
    if ruimeibi is not None and preview.get("price") is not None and preview.get("balance_after") is None:
        preview["balance_after"] = ruimeibi - preview["price"]
    preview["max_price"] = args.max_price
    preview["confirm"] = bool(args.confirm)

    price = preview.get("price")
    if price is None:
        preview["warning"] = "could not parse price; refusing to buy"
        emit(preview)
        c.persist()
        return 2

    checks = preview.get("pansell_checks") or []
    if checks and all(chk.get("valid") is False for chk in checks):
        preview["error"] = "all pansell cloud links reported invalid by server; refusing to buy dead links"
        emit(preview)
        c.persist()
        return 2

    if args.max_price is None:
        preview["error"] = "dry-run only: pass --max-price N (and --confirm to execute)"
        emit(preview)
        c.persist()
        return 0

    if price > args.max_price:
        preview["error"] = f"price {price} exceeds --max-price {args.max_price}"
        emit(preview)
        c.persist()
        return 2

    if ruimeibi is not None and price > ruimeibi:
        preview["error"] = f"insufficient balance: need {price}, have {ruimeibi}"
        emit(preview)
        c.persist()
        return 2

    if not args.confirm:
        preview["note"] = "dry-run OK — re-run with --confirm to execute purchase"
        emit(preview)
        c.persist()
        return 0

    # EXECUTE (only with --confirm)
    if preview["type"] == "attachpay":
        action = (f"/forum.php?mod=misc&action=attachpay&tid={tid}"
                  f"&paysubmit=yes&infloat=yes&inajax=1")
        data = {
            "formhash": preview["formhash"],
            "referer": f"{BASE}/forum.php?mod=viewthread&tid={tid}",
            "aid": str(preview["aid"]),
            "handlekey": "attachpay",
            "paysubmit": "true",
        }
        if args.buy_all:
            data["buyall"] = "yes"
    elif preview["type"] == "pansell":
        action = "/plugin.php?id=jnpar_pansell:pay&inajax=1"
        data = {
            "formhash": preview["formhash"],
            "handlekey": "dtpaytip",
            "tid": str(tid),
            "pid": str(preview.get("pid") or ""),
            "submit": "true",
        }
    else:
        action = f"/forum.php?mod=misc&action=pay&tid={tid}&paysubmit=yes&infloat=yes&inajax=1"
        data = {
            "formhash": preview["formhash"],
            "referer": f"{BASE}/forum.php?mod=viewthread&tid={tid}",
            "handlekey": "pay",
            "paysubmit": "true",
        }
    st, _, resp = c.post(action, data, headers={
        "X-Requested-With": "XMLHttpRequest",
        "Referer": f"{BASE}/forum.php?mod=viewthread&tid={tid}"})
    ok = any(w in resp for w in ("成功", "succeed", "已经购买", "购买成功"))
    emit({
        "ok": ok,
        "executed": True,
        "http": st,
        "type": preview["type"],
        "tid": tid,
        "aid": preview.get("aid"),
        "price": price,
        "response": text_of(resp, 300),
        "balance_before": ruimeibi,
    })
    c.persist()
    return 0 if ok else 1


def cmd_collect(args):
    c = Client()
    c.ensure_login()
    tids = [int(t) for t in args.tids]
    out_path = Path(args.out)
    fmt = "jsonl"
    if out_path.suffix.lower() in (".md", ".markdown"):
        fmt = "markdown"
    elif out_path.suffix.lower() == ".json":
        fmt = "json"
    rows = []
    for i, tid in enumerate(tids):
        if i:
            time.sleep(MIN_INTERVAL)
        try:
            rows.append(parse_thread(c, tid))
        except Error as e:
            rows.append({"ok": False, "tid": tid, "error": e.message, "code": e.code})
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if fmt == "jsonl":
        with out_path.open("w", encoding="utf-8") as f:
            for r in rows:
                # slim for collection
                slim = {k: r.get(k) for k in (
                    "ok", "tid", "fid", "forum", "subject", "author", "url",
                    "price", "paid", "attachments", "unpaid_attachments",
                    "pv_card",
                    "links", "codes", "error", "code") if k in r or r.get("ok") is False}
                if r.get("ok") and r.get("posts"):
                    first = next((p for p in r["posts"] if p.get("first")), r["posts"][0])
                    slim["message_text"] = (first.get("message_text") or "")[:2000]
                f.write(json.dumps(slim, ensure_ascii=False) + "\n")
    elif fmt == "json":
        out_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        lines = [f"# laowang collect ({now_iso()})", ""]
        for r in rows:
            if not r.get("ok"):
                lines += [f"## tid={r.get('tid')} ERROR", r.get("error", ""), ""]
                continue
            lines += [f"## [{r.get('subject')}]({r.get('url')})",
                      f"- tid: {r['tid']} / fid: {r.get('fid')} / {r.get('forum')}",
                      f"- author: {r.get('author')} / price: {r.get('price')}",
                      f"- paid: `{json.dumps(r.get('paid'), ensure_ascii=False)}`"]
            if r.get("links"):
                lines.append("- links:")
                lines += [f"  - `{x}`" for x in r["links"]]
            if r.get("codes"):
                lines.append("- codes: " + ", ".join(f"`{x}`" for x in r["codes"]))
            pc = r.get("pv_card")
            if pc:
                lines.append(f"- pv_card: {pc.get('status')} price={pc.get('price')} purchased={pc.get('purchased')}")
                for f in pc.get("files") or []:
                    lines.append(f"  - [{f.get('size')}] {f.get('title') or ''} → `{f.get('url')}`")
            if r.get("attachments"):
                lines.append("- attachments:")
                for a in r["attachments"]:
                    lines.append(
                        f"  - aid={a['aid']} {a.get('filename')} "
                        f"price={a.get('price')} payed={a.get('payed')}")
            if r.get("posts"):
                first = next((p for p in r["posts"] if p.get("first")), r["posts"][0])
                lines += ["", "```", (first.get("message_text") or "")[:3000], "```", ""]
        out_path.write_text("\n".join(lines), encoding="utf-8")
    emit({"ok": True, "out": str(out_path.resolve()), "format": fmt,
          "count": len(rows), "ok_count": sum(1 for r in rows if r.get("ok"))})
    c.persist()
    return 0


def build_parser():
    p = argparse.ArgumentParser(
        prog="laowang",
        description="laowang.vip CLI (Discuz X3.4) — search / read / dry-run buy")
    p.add_argument("--home", help="override LAOWANG_HOME (config/session dir)")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("login", help="login (TNCode captcha) and save session")
    s.add_argument("--force", action="store_true")
    s.set_defaults(func=cmd_login)

    s = sub.add_parser("whoami", help="current user profile")
    s.set_defaults(func=cmd_whoami)

    s = sub.add_parser("balance", help="credit balances (软妹币 etc.)")
    s.set_defaults(func=cmd_balance)

    s = sub.add_parser("forums", help="list categories and forums")
    s.set_defaults(func=cmd_forums)

    s = sub.add_parser("search", help="search threads via /search/s.php")
    s.add_argument("keyword")
    s.add_argument("--forum", type=int, default=None, help="fid filter")
    s.add_argument("--page", type=int, default=1)
    s.add_argument("--field", choices=("subject", "author", "_all"), default="subject")
    s.set_defaults(func=cmd_search)

    s = sub.add_parser("thread", help="view thread (content, links, paid status)")
    s.add_argument("tid", type=int)
    s.set_defaults(func=cmd_thread)

    s = sub.add_parser("buy", help="buy paid attachment/thread (dry-run unless --confirm)")
    s.add_argument("tid", type=int)
    s.add_argument("--aid", type=int, default=None, help="attachment id (attachpay)")
    s.add_argument("--max-price", type=int, default=None,
                   help="refuse if price > this (required to leave dry-run)")
    s.add_argument("--confirm", action="store_true",
                   help="actually submit purchase (DANGEROUS)")
    s.add_argument("--buy-all", action="store_true", help="buyall=yes for attachpay")
    s.add_argument("--list-only", action="store_true",
                   help="only list unpaid attachments")
    s.set_defaults(func=cmd_buy)

    s = sub.add_parser("collect", help="fetch tids and write jsonl/json/markdown")
    s.add_argument("tids", nargs="+")
    s.add_argument("--out", required=True, help="output path (.jsonl/.json/.md)")
    s.set_defaults(func=cmd_collect)

    return p


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.home:
        os.environ["LAOWANG_HOME"] = args.home
    try:
        return args.func(args)
    except Error as e:
        emit({"ok": False, "error": e.message, "code": e.code})
        return 1
    except KeyboardInterrupt:
        emit({"ok": False, "error": "interrupted", "code": "interrupt"})
        return 130


if __name__ == "__main__":
    sys.exit(main())
