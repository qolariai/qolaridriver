# -*- coding: utf-8 -*-
"""Arvore de um modelo gerado da Uber (com.qint.model.core.generated...) a partir do smali da app.

    python model_tree.py <rider|driver|fleet> <classe> [profundidade=3]
    ex.: python model_tree.py rider edge.services.pudopresentationhelix.TextSearchResponse

Por campo: nome, tipo e '*' se o Builder.build() o exige ("<campo> is null!"); enums mostram os valores;
listas/mapas mostram o tipo dos elementos (assinatura generica). Serve para montar respostas que a app
consegue ler: faltando um campo obrigatorio, o build() lanca e a app trata a resposta como erro de rede.
"""
import re, sys
from pathlib import Path

AND = Path(__file__).resolve().parents[2] / "ANDOIRD"
SRC = {"rider": AND / "USER/work_base", "driver": AND / "DRIVER/decoded", "fleet": AND / "FLEET/qolarifleet_src"}
PREFIX = "com/qint/model/core/generated/"  # Rider; Driver e Fleet: com/qolari/... (ver __main__)
_cache = {}


def find(src, cls):
    rel = cls.replace(".", "/")
    if not rel.startswith("com/"):
        rel = PREFIX + rel
    if rel in _cache:
        return _cache[rel]
    for d in sorted(src.glob("smali*")):
        p = d / (rel + ".smali")
        if p.exists():
            _cache[rel] = p
            return p
    _cache[rel] = None
    return None


def read(p):
    return p.read_text(encoding="utf-8", errors="replace") if p and p.exists() else ""


def fields(txt):
    out = []
    for m in re.finditer(r"^\.field private final (\w+):(\S+)(?:\n\s+\.annotation system Ldalvik/annotation/Signature;\n\s+value = \{\n((?:\s+\".*\",?\n)+))?", txt, re.M):
        sig = "".join(re.findall(r'"(.*)"', m.group(3) or "")) or m.group(2)
        out.append((m.group(1), sig))
    return out


def required(src, cls_path):
    b = read(cls_path.with_name(cls_path.stem + "$Builder.smali"))
    return set(re.findall(r'"(\w+) is null!"', b))


def enum_values(txt):
    if ".super Ljava/lang/Enum;" not in txt:
        return None
    return re.findall(r"^\.field public static final enum (\w+):", txt, re.M)


def short(t):
    return t.replace("L" + PREFIX, "").replace("Lcom/google/common/collect/", "").replace("Ljava/lang/", "").replace(";", "")


def walk(src, cls, depth, ind="", seen=None):
    seen = seen or set()
    p = find(src, cls)
    if not p:
        return
    txt = read(p)
    ev = enum_values(txt)
    if ev is not None:
        print(f"{ind}enum: {' | '.join(v for v in ev if v != '$VALUES')}")
        return
    req = required(src, p)
    fl = [(n, s) for n, s in fields(txt) if n not in ("Companion", "unknownItems") and not n.startswith("$")]
    if len(fl) == 1 and fl[0][0] == "value":  # typedef (ex. LatitudeDegrees -> double): nao expandir
        print(f"{ind}(= {short(fl[0][1])})")
        return
    for name, sig in fields(txt):
        if name in ("Companion", "unknownItems") or name.startswith("$"):
            continue
        print(f"{ind}{'*' if name in req else ' '} {name}: {short(sig)}")
        if depth > 0:
            for inner in re.findall(r"L" + PREFIX + r"([\w/$]+);", sig):
                c = inner.replace("/", ".")
                if c not in seen:
                    walk(src, c, depth - 1, ind + "    ", seen | {c})


if __name__ == "__main__":
    app, cls = sys.argv[1], sys.argv[2]
    if app != "rider":
        PREFIX = "com/qolari/model/core/generated/"
    depth = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    print(cls)
    walk(SRC[app], cls, depth)
