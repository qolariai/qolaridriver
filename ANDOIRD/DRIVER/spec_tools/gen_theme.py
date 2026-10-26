# -*- coding: utf-8 -*-
"""Gera res/values/colors_core.xml a partir de ui_spec/design_tokens.json (paleta ub__ui_core_v3_*).

Uso: python gen_theme.py --tokens ui_spec/design_tokens.json --out <res>
So os valores hexadecimais da paleta (medidas de cor); os nomes passam a qd_core_* (proprios).
Aliases (@color/...) e cores de bibliotecas (abc_, material_...) nao entram.
"""
import argparse
import json
import re
import sys
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tokens", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    d = json.loads(a.tokens.read_text(encoding="utf-8"))
    light = d["colors_light"]
    rows = []
    for k, v in sorted(light.items()):
        m = re.match(r"^ub__ui_core_v3_(.+)$", k)
        if m and re.fullmatch(r"#[0-9a-fA-F]{6,8}", v):
            rows.append((("qd_core_" + m.group(1)).replace("-", "_"), v.lower()))
    (a.out / "values").mkdir(parents=True, exist_ok=True)
    xml = ['<?xml version="1.0" encoding="utf-8"?>',
           "<!-- Gerado por spec_tools/gen_theme.py a partir de ui_spec/design_tokens.json. Nao editar. -->", "<resources>"]
    xml += [f'    <color name="{n}">{v}</color>' for n, v in rows]
    xml.append("</resources>")
    (a.out / "values" / "colors_core.xml").write_text("\n".join(xml) + "\n", encoding="utf-8")
    print(f"{len(rows)} cores da paleta ->", a.out / "values" / "colors_core.xml")
    want = ["black", "white", "blue600", "blue700", "gray50", "gray100", "gray900", "red600", "green600"]
    print("tokens usados no tema:", {w: next((v for n, v in rows if n == f"qd_core_{w}"), None) for w in want})
    return 0


if __name__ == "__main__":
    sys.exit(main())
