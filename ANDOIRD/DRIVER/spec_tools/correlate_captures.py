# -*- coding: utf-8 -*-
"""P2e - correlaciona capturas (ux_capture) com layouts extraidos (ui_spec/layouts) por resource-id.

Uso: python correlate_captures.py --capture <ux_capture> --layouts <ui_spec/layouts> --out <csv> [--package com.ubercab.driver]

Cada dump de uiautomator tem resource-id (ex.: com.ubercab.driver:id/ub__foo). Procura esses ids em
android:id="@+id/..." dos layouts e pontua com peso 1/n (ids raros pesam mais).
Ecras em Compose, ou sem ids, ficam marcados como tal (sem layout XML correspondente).
"""
import argparse
import csv
import math
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

ID_DEF = re.compile(r'android:id="@\+?id/([\w.]+)"')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--capture", required=True, type=Path)
    ap.add_argument("--layouts", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--package", default="com.ubercab.driver")
    a = ap.parse_args()

    id2layouts = defaultdict(set)
    nlay = 0
    for f in a.layouts.rglob("*.xml"):
        nlay += 1
        try:
            txt = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        rel = f"{f.parent.name}/{f.name}"
        for m in ID_DEF.finditer(txt):
            id2layouts[m.group(1)].add(rel)
    print("layouts lidos:", nlay, "| ids definidos:", len(id2layouts))

    versions = {}
    vf = a.capture / "versoes.csv"
    if vf.exists():
        for r in csv.DictReader(vf.open(encoding="utf-8")):
            versions[r["ficheiro"]] = r["versao_da_app"]

    caps = []
    for dumpf in sorted((a.capture / "dumps").glob("*.xml")):
        name = dumpf.stem
        png = a.capture / f"{name}.png"
        if not png.exists():
            continue
        try:
            root = ET.parse(dumpf).getroot()
        except ET.ParseError:
            continue
        ids = set()
        for n in root.iter("node"):
            rid = n.get("resource-id") or ""
            if ":id/" in rid:
                pkg, short = rid.split(":id/", 1)
                if pkg == a.package:
                    ids.add(short)
        caps.append((name, ids))
    df = defaultdict(int)
    for _, ids in caps:
        for i in ids:
            df[i] += 1
    limite = max(3, int(0.20 * len(caps)))
    ubiquos = {i for i, n in df.items() if n > limite}
    print(f"ids ubiquos ignorados (> {limite} capturas): {len(ubiquos)}")
    rows = []
    for name, ids_all in caps:
        ids = ids_all - ubiquos
        score = defaultdict(float)
        common = defaultdict(list)
        for i in ids:
            ls = id2layouts.get(i)
            if not ls:
                continue
            w = 1.0 / len(ls)
            for l in ls:
                score[l] += w
                common[l].append(i)
        ranked = sorted(score.items(), key=lambda kv: -kv[1])
        ver = versions.get(f"{name}.png", "")
        if not ids:
            conf, nota, best, sc, others = "nenhuma", "so ids da estrutura comum, ou sem ids (Compose / pagina web)", "", "", ""
        elif not ranked:
            conf, nota, best, sc, others = "nenhuma", "ids sem layout correspondente", "", "", ""
        else:
            best, sc = ranked[0][0], round(ranked[0][1], 2)
            others = "; ".join(f"{l} ({round(s, 2)})" for l, s in ranked[1:4])
            k = len(common[best])
            conf = "forte" if k >= 3 else ("media" if k == 2 else "fraca")
            nota = f"{k} ids especificos em comum de {len(ids)}"
        rows.append([f"{name}.png", ver, len(ids), best, sc, others, conf, nota])

    a.out.parent.mkdir(parents=True, exist_ok=True)
    with a.out.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["captura", "versao_da_app", "ids_distintos", "melhor_layout", "pontuacao", "outros_candidatos", "confianca", "nota"])
        w.writerows(rows)
    from collections import Counter
    c = Counter(r[6] for r in rows)
    print(f"capturas: {len(rows)} | confianca: {dict(c)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
