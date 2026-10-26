# -*- coding: utf-8 -*-
"""Apoio a recompilacao incremental com o apktool (so os classesN.dex cujas fontes mudaram).

    python apk_cache.py seed <apk> <pasta-fonte>   # copia dex/arsc/manifest/res da APK atual para <fonte>/build/apk
    python apk_cache.py diff <apk-antiga> <apk-nova>  # que entradas mudaram/faltam/sobram

O apktool (sem -f) so volta a montar uma pasta smali_classesN se algum ficheiro dela for mais recente
que build/apk/classesN.dex; o mesmo para res/ (resources.arsc) e AndroidManifest.xml.
"""
import os, shutil, sys, time, zipfile
from pathlib import Path


def seed(apk: str, src: str):
    dst = Path(src, "build", "apk")
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True)
    z = zipfile.ZipFile(apk)
    n = 0
    for i in z.infolist():
        name = i.filename
        top = name.split("/")[0]
        if (top.startswith("classes") and top.endswith(".dex")) or name in ("resources.arsc", "AndroidManifest.xml") \
                or top == "res":
            z.extract(i, dst)
            n += 1
    t = time.time()
    for dp, dn, fn in os.walk(dst):
        for f in fn:
            os.utime(Path(dp, f), (t, t))
    print(f"{n} entradas copiadas para {dst}")


def diff(old: str, new: str):
    a = {i.filename: i for i in zipfile.ZipFile(old).infolist() if not i.filename.startswith("META-INF/")}
    b = {i.filename: i for i in zipfile.ZipFile(new).infolist() if not i.filename.startswith("META-INF/")}
    changed = [n for n in a if n in b and a[n].CRC != b[n].CRC]
    gone = [n for n in a if n not in b]
    added = [n for n in b if n not in a]
    print(f"iguais {len(a) - len(changed) - len(gone)}  alteradas {len(changed)}  so na antiga {len(gone)}  so na nova {len(added)}")
    for title, lst in (("ALTERADAS", changed), ("SO NA ANTIGA", gone), ("SO NA NOVA", added)):
        if lst:
            print(title)
            for n in lst[:60]:
                print("   ", n)
            if len(lst) > 60:
                print(f"    ... +{len(lst) - 60}")


if __name__ == "__main__":
    {"seed": seed, "diff": diff}[sys.argv[1]](*sys.argv[2:])
