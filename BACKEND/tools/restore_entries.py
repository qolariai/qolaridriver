# -*- coding: utf-8 -*-
"""Copia entradas de texto de terceiros (protos da Google, public-suffix-list da Mozilla, ...) da APK original
da Uber para a APK final - o rebrand antigo tinha-lhes trocado type.googleapis.com/dominios pelo backend.

    python restore_entries.py <apk-entrada> <apk-saida> <apk-original> <padrao-glob> [...]

So substitui entradas que existam nas duas APKs. Assinaturas retiradas: depois zipalign + apksigner.
"""
import fnmatch, sys, zipfile

from patch_apk_host import SIG_EXT


def main():
    src, dst, orig = sys.argv[1:4]
    pats = sys.argv[4:]
    zo = zipfile.ZipFile(orig)
    onames = set(zo.namelist())
    zin, zout = zipfile.ZipFile(src), zipfile.ZipFile(dst, "w", allowZip64=True)
    done = []
    for info in zin.infolist():
        name = info.filename
        if name.startswith("META-INF/") and (name.upper().endswith(SIG_EXT) or name == "META-INF/MANIFEST.MF"):
            continue
        data = zin.read(info)
        if name in onames and any(fnmatch.fnmatch(name, p) for p in pats):
            new = zo.read(name)
            if new != data:
                data = new
                done.append(name)
        zi = zipfile.ZipInfo(name, date_time=info.date_time)
        zi.compress_type = info.compress_type
        zi.external_attr, zi.internal_attr, zi.create_system = info.external_attr, info.internal_attr, info.create_system
        zout.writestr(zi, data)
    zout.close()
    print(f"{len(done)} entradas repostas do original")
    for n in done:
        print("   ", n)


if __name__ == "__main__":
    main()
