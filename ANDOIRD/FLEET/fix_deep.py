#!/usr/bin/env python3
# Re-run rebrand transform with long-path support (\\?\ prefix).
# rebrand.py silently skipped files whose absolute path >260 chars.
import os, re, sys

ROOT = r"qolarifleet_src"
BRAND_L, BRAND_T, BRAND_U = "qolari", "Qolari", "QOLARI"
BACKEND = "192.168.1.204:3000"

HOSTPAT = (r'(?:[a-zA-Z0-9*-]+\.)*'
           r'(?:ubereats|uberinternal|uber|oojoovae)\.(?:com|org)'
           r'|loggi-uber\.zendesk\.com'
           r'|d183q68ssszldn\.cloudfront\.net'
           r'|d4p17acsd5wyj\.cloudfront\.net'
           r'|d1goeicueq33a8\.cloudfront\.net'
           r'|d1a3f4spazzrp4\.cloudfront\.net')
RE_SCHEME = re.compile(r'https?://(?:' + HOSTPAT + r')')
RE_HOST = re.compile(HOSTPAT)

TEXT_REPS = [
    ('ubercab', BRAND_L), ('Ubercab', BRAND_T), ('UberCab', BRAND_T), ('UBERCAB', BRAND_U),
    ('uber', BRAND_L), ('Uber', BRAND_T), ('UBER', BRAND_U),
]
BIN_REPS = [
    (b'UBERCAB', b'QOLACAB'), (b'UberCab', b'QolaCab'), (b'Ubercab', b'Qolacab'),
    (b'ubercab', b'qolacab'),
    (b'UBER', b'QOLA'), (b'Uber', b'Qola'), (b'uber', b'qola'),
]

def xp(p):
    p = os.path.abspath(p)
    if not p.startswith('\\\\?\\'):
        return '\\\\?\\' + p
    return p

def transform_text(s):
    s = RE_SCHEME.sub('http://' + BACKEND, s)
    s = RE_HOST.sub(BACKEND, s)
    for a, b in TEXT_REPS:
        s = s.replace(a, b)
    return s

stats = {'text': 0, 'bin': 0, 'renamed': 0, 'err': 0, 'files': 0}

# walk the whole tree via \\?\ prefixed root so deep paths are reachable
root_xp = xp(ROOT)
for dp, dn, fn in os.walk(root_xp):
    if '\\build\\' in dp:
        continue
    for f in fn:
        stats['files'] += 1
        p = os.path.join(dp, f)
        try:
            raw = open(p, 'rb').read()
        except OSError as e:
            stats['err'] += 1
            print('ERR', p, e)
            continue
        try:
            s = raw.decode('utf-8')
        except UnicodeDecodeError:
            new = raw
            for a, b in BIN_REPS:
                new = new.replace(a, b)
            if new != raw:
                open(p, 'wb').write(new)
                stats['bin'] += 1
            continue
        ns = transform_text(s)
        if ns != s:
            open(p, 'wb').write(ns.encode('utf-8'))
            stats['text'] += 1

# rename files/dirs carrying the brand (bottom-up, xp-safe)
def brand_name(n):
    for a, b in TEXT_REPS:
        n = n.replace(a, b)
    return n

def merge_move(src, dst):
    if not os.path.exists(dst):
        os.rename(src, dst); return
    for item in os.listdir(src):
        merge_move(os.path.join(src, item), os.path.join(dst, item))
    os.rmdir(src)

for dp, dn, fn in os.walk(root_xp, topdown=False):
    if '\\build\\' in dp:
        continue
    for f in fn:
        nn = brand_name(f)
        if nn != f:
            os.rename(os.path.join(dp, f), os.path.join(dp, nn))
            stats['renamed'] += 1
    for d in dn:
        nn = brand_name(d)
        if nn != d:
            merge_move(os.path.join(dp, d), os.path.join(dp, nn))
            stats['renamed'] += 1

print('files walked :', stats['files'])
print('text patched :', stats['text'])
print('bin patched  :', stats['bin'])
print('renamed      :', stats['renamed'])
print('errors       :', stats['err'])
