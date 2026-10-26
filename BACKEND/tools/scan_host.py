# -*- coding: utf-8 -*-
"""Onde aparece o endereco do backend dentro de um APK (utf-8 e utf-16le).  python scan_host.py <apk> [host]"""
import sys, zipfile, collections
apk = sys.argv[1]
host = sys.argv[2] if len(sys.argv) > 2 else "192.168.1.204"
pats = {"utf8": host.encode(), "utf16": host.encode("utf-16le")}
z = zipfile.ZipFile(apk)
tot = collections.Counter()
for i in z.infolist():
    if i.is_dir():
        continue
    data = z.read(i)
    hit = {k: data.count(p) for k, p in pats.items() if p in data}
    if hit:
        print(f"{i.filename:45} {'STORED' if i.compress_type == 0 else 'DEFL  '} {i.file_size:>10} {hit}")
        tot.update(hit)
print("TOTAL", dict(tot), "| entradas:", len(z.infolist()))
