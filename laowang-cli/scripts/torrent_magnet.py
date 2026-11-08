#!/usr/bin/env python3
"""解析 .torrent：最小 bencode → info hash / 磁力 / 名称 / 体积 / tracker / 文件清单。
用法: python torrent_magnet.py <a.torrent> [b.torrent ...]   # 每个文件输出一行 JSON
纯标准库，无第三方依赖（本机 pip 常不可用，别改依赖）。info hash = SHA1(info dict 的 bencode 编码)。
"""
import hashlib, json, sys


def bdecode(data, i=0):
    if data[i:i+1] == b'i':
        end = data.index(b'e', i)
        return data[i+1:end].decode('utf-8', 'replace'), end + 1
    c = data[i:i+1]
    if c.isdigit():
        colon = data.index(b':', i)
        n = int(data[i:colon])
        start = colon + 1
        return data[start:start+n], start + n
    if c == b'l':
        i += 1
        out = []
        while data[i:i+1] != b'e':
            v, i = bdecode(data, i)
            out.append(v)
        return out, i + 1
    if c == b'd':
        i += 1
        out = {}
        while data[i:i+1] != b'e':
            k, i = bdecode(data, i)
            v, i = bdecode(data, i)
            out[k] = v
        return out, i + 1
    raise ValueError(f'bdecode: unexpected byte {c!r} @ {i}')


def bencode(x):
    if isinstance(x, bytes):
        return str(len(x)).encode() + b':' + x
    if isinstance(x, int):
        return b'i' + str(x).encode() + b'e'
    if isinstance(x, str):
        return bencode(x.encode('utf-8'))
    if isinstance(x, list):
        return b'l' + b''.join(bencode(v) for v in x) + b'e'
    if isinstance(x, dict):
        return b'd' + b''.join(bencode(k) + bencode(v) for k, v in sorted(x.items())) + b'e'
    raise TypeError(type(x))


def human(n):
    for u in ('B', 'K', 'M', 'G', 'T'):
        if n < 1024 or u == 'T':
            return f'{n}B' if u == 'B' else f'{n:.1f}{u}'
        n /= 1024.0


def main():
    for path in sys.argv[1:]:
        raw = open(path, 'rb').read()
        d, _ = bdecode(raw)
        info = d.get(b'info')
        h = hashlib.sha1(bencode(info)).hexdigest()
        name = info.get(b'name', b'').decode('utf-8', 'replace')
        size = info[b'length'] if b'length' in info else sum(int(f[b'length']) for f in info.get(b'files', []))
        files = []
        if b'files' in info:
            for f in info[b'files']:
                files.append({'path': b'/'.join(f[b'path']).decode('utf-8', 'replace'),
                              'size': int(f[b'length'])})
        trackers = []
        tr = d.get(b'trackers', [])
        if isinstance(tr, list):
            for tier in tr:
                trackers.extend(t.decode() for t in tier)
        elif isinstance(tr, dict):
            for tier in tr.values():
                trackers.extend(t.decode() for t in tier)
        print(json.dumps({'file': path, 'name': name, 'info_hash': h,
                          'magnet': f'magnet:?xt=urn:btih:{h}',
                          'size': int(size), 'size_human': human(int(size)),
                          'trackers': trackers, 'files': files}, ensure_ascii=False))


if __name__ == '__main__':
    main()
