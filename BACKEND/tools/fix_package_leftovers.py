# -*- coding: utf-8 -*-
"""Corrige ligacoes partidas pelo rebrand: classes que ficaram no pacote antigo (com/uber, com/ubercab)
enquanto outras as referem ja no novo (com/qolari), ou o contrario -> NoClassDefFoundError em tempo de execucao.

    python fix_package_leftovers.py <apk> <raiz-smali> <novo-prefixo> scan|apply

Para cada supertipo em falta (dex_classes.py missing-supers) cujo "gemeo" no outro pacote existe, junta a
familia de classes (Outer e Outer$...) ao mapa de renomeacao antigo->novo. `apply` troca esses descritores
em todos os .smali (definicoes e referencias) e diz que pastas smali_classesN mudaram.
So toca em descritores `Lpacote/...;` dessas classes; textos com nomes de pacote ficam como estao.
"""
import os, sys, zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from dex_classes import SYSTEM, read_dex  # noqa: E402

OLD = ("Lcom/ubercab/", "Lcom/uber/")


def main():
    apk, root, new, mode = sys.argv[1], Path(sys.argv[2]), sys.argv[3], sys.argv[4]
    newp = f"L{new.strip('/')}/"
    z = zipfile.ZipFile(apk)
    where, supers = {}, []
    for n in z.namelist():
        if n.startswith("classes") and n.endswith(".dex"):
            for name, s in read_dex(z.read(n)):
                where[name] = n
                supers.append(s)
    missing = {t for s in supers for t in s if t not in where and not t.startswith(SYSTEM)}

    def twin(t):
        if t.startswith(newp):
            rest = t[len(newp):]
            return [o + rest for o in OLD if o + rest in where]
        for o in OLD:
            if t.startswith(o) and newp + t[len(o):] in where:
                return [t]  # referencia antiga para classe ja renomeada: so trocar a referencia
        return []

    rename = {}
    for t in sorted(missing):
        for old in twin(t):
            outer = old[:-1].split("$")[0]
            for k in where:
                if k == outer + ";" or k.startswith(outer + "$"):
                    rename[k] = newp + k[len(next(o for o in OLD if k.startswith(o))):]
            if old not in where:  # referencia antiga sem definicao
                rename[old] = newp + old[len(next(o for o in OLD if old.startswith(o))):]
    print(f"{len(missing)} tipos em falta; {len(rename)} descritores a renomear")
    for a, b in list(rename.items())[:15]:
        print("   ", a, "->", b)
    if mode != "apply":
        return
    needles = [a.encode() for a in rename]
    touched, dirs = 0, {}
    for top in sorted(p for p in root.iterdir() if p.is_dir() and p.name.startswith("smali")):
        # prefixo \\?\ : ha caminhos smali com mais de 260 caracteres (limite do Windows)
        for dp, dn, fn in os.walk("\\\\?\\" + str(top.resolve())):
            for f in fn:
                p = Path(dp, f)
                data = p.read_bytes()
                if b"Lcom/uber" not in data:
                    continue
                new_data = data
                for a in needles:
                    if a in new_data:
                        new_data = new_data.replace(a, rename[a.decode()].encode())
                if new_data != data:
                    p.write_bytes(new_data)
                    touched += 1
                    dirs[top.name] = dirs.get(top.name, 0) + 1
    print(f"{touched} ficheiros alterados:", dirs)


if __name__ == "__main__":
    main()
