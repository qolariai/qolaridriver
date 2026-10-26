# -*- coding: utf-8 -*-
"""Desfaz colisoes de classes criadas pelo rebrand da Driver (com.uber.X e com.ubercab.X -> ambos com.qolari.X).

    python fix_class_collisions.py <fonte-smali> <apk-original> <baksmali-dos-dex-mistos> <mapa> [--apply]

<mapa> = "orig:mini,..." p.ex. "2:,7:2,8:3,13:4,15:5,17:6" (dex N da APK original -> pasta smali_classesM do
baksmali feito a esses dex; "" = pasta smali). As classes com.uber.* que colidem passam a <Nome>U (mesmo pacote,
para nao partir acessos de pacote); as referencias sao decididas pela APK original:
- dex que so referem uma das versoes -> decidido ao nivel do dex;
- dex que referem as duas -> linha a linha, comparando com o ficheiro original correspondente.
Sem --apply so lista o que mudaria. Ficheiros novos/alterados ficam com mtime atual (apktool incremental).
Visto a 12-10: NavigationManager (classes2 vs classes3) fazia a app cair logo depois do login (NoSuchMethodError D()/g0()).
"""
import os, re, sys, zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from dex_classes import type_ids  # noqa: E402

ROOT, ORIG_APK, MINI, MAP = sys.argv[1:5]
if os.name == "nt":  # caminhos smali com mais de 260 caracteres
    ROOT, MINI = ("\\\\?\\" + os.path.abspath(x) for x in (ROOT, MINI))
APPLY = "--apply" in sys.argv
mini_dir = {int(a): ("smali" if b == "" else f"smali_classes{b}") for a, b in (x.split(":") for x in MAP.split(","))}

def dexnum(d):  # "smali" -> 1, "smali_classes7" -> 7
    return 1 if d == "smali" else int(d[len("smali_classes"):])

# 1) classes definidas em com/uber e com/ubercab com o mesmo resto de caminho (as colisoes)
orig = zipfile.ZipFile(ORIG_APK)
dexes = sorted((n for n in orig.namelist() if re.fullmatch(r"classes\d*\.dex", n)), key=lambda s: int(s[7:-4] or 1))
types = {int(n[7:-4] or 1): set(type_ids(orig.read(n))) for n in dexes}
from dex_classes import read_dex  # noqa: E402
defined = set()
for n in dexes:
    defined.update(c for c, _ in read_dex(orig.read(n)))
rest = lambda c, p: c[len(p):] if c.startswith(p) else None
uber = {rest(c, "Lcom/uber/") for c in defined if c.startswith("Lcom/uber/")}
cab = {rest(c, "Lcom/ubercab/") for c in defined if c.startswith("Lcom/ubercab/")}
coll = sorted(uber & cab)
# as classes internas/irmas da versao uber de cada colisao tambem mudam de nome (Nome$x -> NomeU$x)
outer = lambda r: r[:-1].split("$")[0]
coll_outer = {outer(r) for r in coll}
ren = {}  # resto (ex. "navigation/b;") -> resto novo
for r in sorted(uber):
    o = outer(r)
    if o in coll_outer:
        ren[r] = o + "U" + r[len(o):]
print("colisoes:", [c[:-1] for c in coll])
print("a renomear (com.uber):", {k[:-1]: v[:-1] for k, v in ren.items()})

Q = "Lcom/qolari/"
qre = re.compile(r"Lcom/qolari/(" + "|".join(re.escape(r[:-1]) for r in coll) + r");")
# por dex original: que versoes de cada colisao sao referidas
def kind(n, r):
    u, c = ("Lcom/uber/" + r) in types.get(n, ()), ("Lcom/ubercab/" + r) in types.get(n, ())
    return "both" if u and c else "uber" if u else "cab" if c else None

def new_name(r):
    return Q + ren[r] if r in ren else None

changes, todo, problems = [], {}, []
for d in sorted(os.listdir(ROOT)):
    if not d.startswith("smali"):
        continue
    n = dexnum(d)
    for dp, _, fn in os.walk(Path(ROOT, d)):
        for f in fn:
            if not f.endswith(".smali"):
                continue
            p = Path(dp, f)
            txt = p.read_text(encoding="utf-8")
            if not qre.search(txt):
                continue
            rel = p.relative_to(Path(ROOT, d)).as_posix()
            lines = txt.split("\n")
            ol = None
            ks = {m.group(1) + ";" for m in qre.finditer(txt)}
            if any(kind(n, r) == "both" for r in ks):
                if n not in mini_dir:
                    problems.append(f"{d}/{rel}: dex misto {n} sem baksmali")
                    continue
                cands = [rel]
                if rel.startswith("com/qolari/"):
                    cands = ["com/uber/" + rel[11:], "com/ubercab/" + rel[11:]]
                found = [c for c in cands if Path(MINI, mini_dir[n], c).exists()]
                if len(found) != 1:
                    problems.append(f"{d}/{rel}: original {found or cands}")
                    continue
                ol = Path(MINI, mini_dir[n], found[0]).read_text(encoding="utf-8").split("\n")
                if len(ol) != len(lines):
                    problems.append(f"{d}/{rel}: {len(lines)} linhas vs {len(ol)} no original {found[0]}")
                    continue
            out, cnt = [], [0]
            for i, line in enumerate(lines):
                def sub(m):
                    r = m.group(1) + ";"
                    k = kind(n, r)
                    if k == "both":
                        o = ol[i]
                        u, c = ("Lcom/uber/" + r) in o, ("Lcom/ubercab/" + r) in o
                        if u and c:
                            problems.append(f"{d}/{rel}:{i+1}: linha com as duas versoes")
                            return m.group(0)
                        k = "uber" if u else "cab" if c else None
                        if k is None:
                            problems.append(f"{d}/{rel}:{i+1}: original sem a referencia")
                            return m.group(0)
                    if k == "uber" and new_name(r):
                        cnt[0] += 1
                        return new_name(r)
                    return m.group(0)
                out.append(qre.sub(sub, line))
            nch = cnt[0]
            # o proprio ficheiro de definicao de uma classe uber renomeada muda de nome
            target = p
            if rel.startswith("com/qolari/") and (rel[11:-6] + ";") in ren:
                r = rel[11:-6] + ";"
                head = out[0] if out else ""
                if head.startswith(".class") and head.rstrip().endswith(Q + ren[r]):
                    target = Path(ROOT, d, "com/qolari", ren[r][:-1] + ".smali")
            if nch or target != p:
                changes.append((p, target, nch))
                todo[p] = (target, "\n".join(out))

for p, t, nch in changes:
    print(f"{nch:3d}  {p.relative_to(ROOT).as_posix()}" + (f"  ->  {t.name}" if t != p else ""))
print(f"{len(changes)} ficheiros; problemas: {len(problems)}")
for x in problems:
    print("  !", x)
if APPLY and not problems:
    for p, (t, txt) in todo.items():
        t.write_text(txt, encoding="utf-8", newline="\n")
        if t != p:
            p.unlink()
    print("aplicado")
