# -*- coding: utf-8 -*-
"""P4 (complemento) - servicos gRPC e esquema Room que o scan_network.py nao apanha (so leitura).

Uso: python scan_extra.py --decoded <pasta_apktool> --out <extra_raw.json>
- gRPC: em ficheiros que usam Lio/grpc/MethodDescriptor, recolhe nomes de servico (pkg.Servico) e metodos (CamelCase).
- Room: o @Entity nao chega ao dex (retencao CLASS); recolhe os CREATE TABLE gerados e as subclasses de RoomDatabase.
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

RE_STR = re.compile(r"const-string(?:/jumbo)? [vp]\d+, \"((?:[^\"\\]|\\.)*)\"")
RE_SVC = re.compile(r"^[a-z][\w-]*(?:\.[\w-]+)*\.[A-Z]\w*$")
RE_MTH = re.compile(r"^[A-Z][A-Za-z0-9]{2,60}$")
RE_CREATE = re.compile(r"CREATE TABLE IF NOT EXISTS `([^`]+)` \((.*?)\)(?:,|$)")
RE_CLASS = re.compile(r"^\.class [^\n]*?(L[^;\s]+;)", re.M)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--decoded", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    dec = a.decoded.resolve()
    grpc, tables, dbs = {}, {}, []
    for r in sorted(p for p in dec.iterdir() if p.is_dir() and p.name.startswith("smali")):
        for dp, _, fs in os.walk(r):
            for f in fs:
                if not f.endswith(".smali"):
                    continue
                p = os.path.join(dp, f)
                try:
                    s = open(p, encoding="utf-8", errors="ignore").read()
                except OSError:
                    continue
                m = RE_CLASS.search(s)
                cls = m.group(1)[1:-1].replace("/", ".") if m else f
                if "Lio/grpc/MethodDescriptor;" in s:
                    st = RE_STR.findall(s)
                    svcs = [x for x in st if RE_SVC.match(x)]
                    mths = [x for x in st if RE_MTH.match(x)]
                    for sv in svcs:
                        g = grpc.setdefault(sv, {"metodos": set(), "classes": set()})
                        g["classes"].add(cls)
                        if len(set(svcs)) == 1:
                            g["metodos"].update(mths)
                    for x in st:
                        if "/" in x and RE_SVC.match(x.split("/")[0]) and RE_MTH.match(x.split("/")[-1]):
                            g = grpc.setdefault(x.split("/")[0], {"metodos": set(), "classes": set()})
                            g["metodos"].add(x.split("/")[-1]); g["classes"].add(cls)
                if "CREATE TABLE IF NOT EXISTS" in s:
                    for x in RE_STR.findall(s):
                        for t in RE_CREATE.finditer(x):
                            tables.setdefault(t.group(1), {"colunas": t.group(2)[:400], "classe": cls})
                if ".super Landroidx/room/RoomDatabase;" in s:
                    dbs.append(cls)
    out = {"grpc_services": {k: {"metodos": sorted(v["metodos"])[:40], "classes": sorted(v["classes"])[:3]} for k, v in sorted(grpc.items())},
           "room_tables": tables, "room_databases": sorted(dbs)}
    a.out.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"gRPC servicos: {len(grpc)} | Room tabelas: {len(tables)} | RoomDatabase: {len(dbs)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
