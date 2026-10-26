# -*- coding: utf-8 -*-
"""Valores serializados (Gson @SerializedName) dos enums de um modelo Uber gerado.

    python enum_names.py <rider|driver|fleet> <classe> [<classe> ...]
    ex.: python enum_names.py driver rtapi.models.offers.offeractions.OfferType

Enums sem anotacao serializam com o nome Java; nas unioes Thrift o `type` e o nome do campo.
"""
import re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import model_tree  # noqa: E402

app = sys.argv[1]
if app != "rider":
    model_tree.PREFIX = "com/qolari/model/core/generated/"
for cls in sys.argv[2:]:
    p = model_tree.find(model_tree.SRC[app], cls)
    txt = model_tree.read(p)
    out = []
    for m in re.finditer(r"^\.field public static final enum (\w+):\S+\n((?:\s+\.annotation[^\n]*\n(?:\s+value = \"[^\"]*\"\n)?\s+\.end annotation\n)?)", txt, re.M):
        v = re.search(r'value = "([^"]*)"', m.group(2) or "")
        out.append(f"{m.group(1)}={v.group(1)}" if v else m.group(1))
    print(cls.split(".")[-1], "->", " | ".join(out) if out else "(nao encontrado)")
