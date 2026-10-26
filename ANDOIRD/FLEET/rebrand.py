#!/usr/bin/env python3
# Rebrand + backend repoint for decompiled APK (local learning use)
import os, re, sys, struct, zlib

ROOT = r"qolarifleet_src"
BRAND_L, BRAND_T, BRAND_U = "qolari", "Qolari", "QOLARI"
BACKEND = "192.168.1.204:3000"
DL_HOST = "fleet.qolari.local"

# hosts owned by the brand -> point to local backend
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
# length-preserving replaces for binary blobs (safe for length-prefixed formats)
BIN_REPS = [
    (b'UBERCAB', b'QOLACAB'), (b'UberCab', b'QolaCab'), (b'Ubercab', b'Qolacab'),
    (b'ubercab', b'qolacab'),
    (b'UBER', b'QOLA'), (b'Uber', b'Qola'), (b'uber', b'qola'),
]

stats = {'text': 0, 'bin': 0, 'renamed': 0, 'hosts': 0}
text_files, bin_files = [], []

for dp, dn, fn in os.walk(ROOT):
    for f in fn:
        text_files.append(os.path.join(dp, f))

def transform_text(s):
    s = RE_SCHEME.sub('http://' + BACKEND, s)
    s = RE_HOST.sub(BACKEND, s)
    for a, b in TEXT_REPS:
        s = s.replace(a, b)
    return s

for path in text_files:
    try:
        raw = open(path, 'rb').read()
    except OSError:
        continue
    try:
        s = raw.decode('utf-8')
    except UnicodeDecodeError:
        bin_files.append(path)
        continue
    new = transform_text(s)
    if new != s:
        stats['text'] += 1
        stats['hosts'] += len(RE_HOST.findall(s)) + len(RE_SCHEME.findall(s))
        open(path, 'wb').write(new.encode('utf-8'))

# binaries: same-length replace
for path in bin_files:
    raw = open(path, 'rb').read()
    new = raw
    for a, b in BIN_REPS:
        new = new.replace(a, b)
    if new != raw:
        stats['bin'] += 1
        open(path, 'wb').write(new)

# ---- manifest structural fixes ----
mpath = os.path.join(ROOT, 'AndroidManifest.xml')
m = open(mpath, encoding='utf-8').read()
# deep-link hosts must be valid hostnames (no port)
m = m.replace(f'android:host="{BACKEND}"', f'android:host="{DL_HOST}"')
# standalone install: drop split-bundle attrs
m = m.replace(' android:requiredSplitTypes="base__abi,base__density"', '')
m = m.replace(' android:splitTypes=""', '')
# launcher icon + cleartext for local http backend
m = m.replace('android:icon="@null"', 'android:icon="@mipmap/ic_launcher"')
m = m.replace('android:hardwareAccelerated="true"',
              'android:hardwareAccelerated="true" android:usesCleartextTraffic="true"', 1)
open(mpath, 'w', encoding='utf-8').write(m)

# ---- rename files/dirs carrying the brand ----
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

for dp, dn, fn in os.walk(ROOT, topdown=False):
    for f in fn:
        nn = brand_name(f)
        if nn != f:
            os.rename(os.path.join(dp, f), os.path.join(dp, nn)); stats['renamed'] += 1
    for d in dn:
        nn = brand_name(d)
        if nn != d:
            merge_move(os.path.join(dp, d), os.path.join(dp, nn)); stats['renamed'] += 1

# ---- generic launcher icon (rounded square + "Q") ----
def png(path, N):
    R, r_in = 0.30 * N, 0.19 * N
    cx, cy = 0.5 * N, 0.47 * N
    rad = 0.18 * N

    def inside_round(x, y):
        if rad <= x < N - rad or rad <= y < N - rad:
            return True
        cxx = rad if x < rad else N - 1 - rad
        cyy = rad if y < rad else N - 1 - rad
        return (x - cxx) ** 2 + (y - cyy) ** 2 <= rad * rad

    rows = []
    for y in range(N):
        row = bytearray([0])
        for x in range(N):
            if not inside_round(x, y):
                row += b'\x00\x00\x00\x00'; continue
            dx, dy = x - cx, y - cy
            d2 = dx * dx + dy * dy
            ring = r_in * r_in <= d2 <= R * R
            # tail of Q: band along diagonal bottom-right
            tail = abs(dx - dy) <= 0.05 * N and 0.30 * N <= dx + dy <= 0.66 * N
            if ring or tail:
                row += b'\xff\xff\xff\xff'
            else:
                row += bytes((0x4F, 0x46, 0xE5, 0xFF))
        rows.append(bytes(row))
    def chunk(t, d):
        c = struct.pack('>I', len(d)) + t + d
        return c + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    data = b'\x89PNG\r\n\x1a\n'
    data += chunk(b'IHDR', struct.pack('>IIBBBBB', N, N, 8, 6, 0, 0, 0))
    data += chunk(b'IDAT', zlib.compress(b''.join(rows), 9))
    data += chunk(b'IEND', b'')
    open(path, 'wb').write(data)

for dpi, n in [('mdpi', 48), ('hdpi', 72), ('xhdpi', 96), ('xxhdpi', 144), ('xxxhdpi', 192)]:
    d = os.path.join(ROOT, 'res', f'mipmap-{dpi}')
    os.makedirs(d, exist_ok=True)
    png(os.path.join(d, 'ic_launcher.png'), n)

print('text files modified :', stats['text'])
print('binary files patched:', stats['bin'])
print('host occurrences    :', stats['hosts'])
print('renamed entries     :', stats['renamed'])
