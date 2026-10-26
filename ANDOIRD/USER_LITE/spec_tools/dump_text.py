# -*- coding: utf-8 -*-
"""Extrai texto, bounds e classe de cada no' dos dumps do uiautomator.

Uso: python dump_text.py [nome-do-dump ...]  (sem nomes = todos)
Saida: um bloco por dump, no stdout. Serve para medir a spec da User Lite.
"""
import os
import sys
import xml.etree.ElementTree as ET

BASE = os.path.join(os.path.dirname(__file__), "..", "ux_capture", "dumps")


def dump(name: str) -> None:
    path = os.path.join(BASE, name + ".xml")
    if not os.path.exists(path):
        return
    root = ET.parse(path).getroot()
    print("\n###", name)
    for node in root.iter("node"):
        text = (node.get("text") or "").strip()
        desc = (node.get("content-desc") or "").strip()
        if not text and not desc:
            continue
        cls = node.get("class", "").split(".")[-1]
        print(f"{cls:14} {node.get('bounds', ''):28} text={text!r} desc={desc!r}")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    names = sys.argv[1:] or sorted(
        f[:-4] for f in os.listdir(BASE) if f.endswith(".xml")
    )
    for n in names:
        dump(n)
