# -*- coding: utf-8 -*-
"""Classes definidas nos dex de uma APK e classes que faltam.

    python dex_classes.py <apk> has <Lpkg/Classe;> ...      # em que dex esta definida cada classe
    python dex_classes.py <apk> missing-supers              # superclasses/interfaces que nao existem em nenhum dex
                                                            # (excluindo android/java/kotlin...: vem do sistema)
    python dex_classes.py <apk> missing-refs                # qualquer tipo referido (type_ids) sem definicao
"""
import struct, sys, zipfile


def _uleb(b, i):
    n = s = 0
    while True:
        x = b[i]
        i += 1
        n |= (x & 0x7F) << s
        if not x & 0x80:
            return n, i
        s += 7


def type_ids(b: bytes):
    str_size, str_off, type_size, type_off = struct.unpack_from("<IIII", b, 0x38)
    out = []
    for t in range(type_size):
        off = struct.unpack_from("<I", b, str_off + 4 * struct.unpack_from("<I", b, type_off + 4 * t)[0])[0]
        _, i = _uleb(b, off)
        out.append(b[i:b.index(bytes(1), i)].decode("utf-8", "replace"))
    return out


def read_dex(b: bytes):
    str_size, str_off, type_size, type_off = struct.unpack_from("<IIII", b, 0x38)
    cd_size, cd_off = struct.unpack_from("<II", b, 0x60)
    tl_cache = {}

    def string(idx):
        off = struct.unpack_from("<I", b, str_off + 4 * idx)[0]
        _, i = _uleb(b, off)
        j = b.index(b"\x00", i)
        return b[i:j].decode("utf-8", "replace")

    def type_name(tidx):
        return string(struct.unpack_from("<I", b, type_off + 4 * tidx)[0])

    classes = []
    for k in range(cd_size):
        o = cd_off + 32 * k
        cls, _, sup, ifoff = struct.unpack_from("<IIII", b, o)
        name = type_name(cls)
        supers = [] if sup == 0xFFFFFFFF else [type_name(sup)]
        if ifoff:
            n = struct.unpack_from("<I", b, ifoff)[0]
            for t in struct.unpack_from(f"<{n}H", b, ifoff + 4):
                supers.append(type_name(t))
        classes.append((name, supers))
    return classes


SYSTEM = ("Ljava/", "Ljavax/", "Landroid/", "Ldalvik/", "Lkotlin/", "Lorg/w3c/", "Lorg/xml/", "Lorg/json/",
          "Lsun/", "Lorg/apache/http/", "Lcom/android/", "Ljunit/")


def main():
    apk, cmd = sys.argv[1], sys.argv[2]
    z = zipfile.ZipFile(apk)
    where, all_supers, refs = {}, [], {}
    for n in sorted((x for x in z.namelist() if x.startswith("classes") and x.endswith(".dex")),
                    key=lambda x: int(x[7:-4] or 1)):
        data = z.read(n)
        for name, supers in read_dex(data):
            where.setdefault(name, []).append(n)
            all_supers.append((name, supers, n))
        if cmd == "missing-refs":
            for t in type_ids(data):
                refs.setdefault(t.lstrip("["), set()).add(n)
    if cmd == "missing-refs":
        miss = sorted(t for t in refs if t.startswith("L") and t not in where and not t.startswith(SYSTEM))
        for t in miss:
            print(t, sorted(refs[t]))
        print(f"{len(miss)} tipos referidos sem definicao")
    if cmd == "has":
        for c in sys.argv[3:]:
            print(c, where.get(c, "NAO DEFINIDA"))
    elif cmd == "missing-supers":
        missing = {}
        for name, supers, n in all_supers:
            for s in supers:
                if s not in where and not s.startswith(SYSTEM):
                    missing.setdefault(s, []).append(name)
        for s, users in sorted(missing.items()):
            print(f"{s}  <- {len(users)} classe(s), ex.: {users[0]}")
        print(f"{len(missing)} tipos em falta | {len(where)} classes definidas | "
              f"duplicadas: {sum(1 for v in where.values() if len(v) > 1)}")


if __name__ == "__main__":
    main()
