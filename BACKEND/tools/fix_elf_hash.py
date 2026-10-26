# -*- coding: utf-8 -*-
"""Corrige as tabelas de hash das bibliotecas nativas (.so) cujos nomes de simbolos o rebrand trocou no sitio.

    python fix_elf_hash.py scan <apk>            # lista as .so com simbolos que o dlsym ja nao encontra
    python fix_elf_hash.py fix  <apk> <saida>    # recalcula a .hash (SysV) dessas .so; resto da APK igual

O rebrand antigo trocou texto dentro das .so (ex. Java_com_uber_h3_* -> Java_com_qint_h3_*) sem recalcular a
tabela de hash do ELF: a biblioteca carrega, mas o ART nao encontra as funcoes JNI (UnsatisfiedLinkError
"No implementation found ... is the library loaded?"). A .hash SysV recalcula-se no mesmo espaco (mesmos
nbucket/nchain, so mudam os indices). .gnu.hash nao e tratada (seria preciso reordenar a .dynsym) - so assinalada.
Assinaturas retiradas: depois zipalign -p + apksigner.
"""
import struct, sys, zipfile

from patch_apk_host import SIG_EXT

SHT_HASH, SHT_DYNSYM, SHT_GNU_HASH = 5, 11, 0x6FFFFFF6


def elf_hash(name: bytes):
    h = 0
    for c in name:
        h = ((h << 4) + c) & 0xFFFFFFFF
        g = h & 0xF0000000
        if g:
            h ^= g >> 24
        h &= ~g & 0xFFFFFFFF
    return h


def _sections(d):
    if d[:4] != b"\x7fELF" or d[4] != 2:  # so ELF64 (arm64-v8a)
        return None
    shoff = struct.unpack_from("<Q", d, 0x28)[0]
    shentsize, shnum = struct.unpack_from("<HH", d, 0x3A)
    return [struct.unpack_from("<IIQQQQIIQQ", d, shoff + i * shentsize) for i in range(shnum)]


def _symbols(d, secs):
    dynsym = next(s for s in secs if s[1] == SHT_DYNSYM)
    dynstr = secs[dynsym[6]]
    out = []
    for i in range(dynsym[5] // 24):
        n = struct.unpack_from("<I", d, dynsym[4] + i * 24)[0]
        out.append(d[dynstr[4] + n:d.index(b"\0", dynstr[4] + n)])
    return out


def check(d):
    """(tem_gnu_hash, [nomes que a .hash nao encontra]) ou None se nao for ELF64 com .hash"""
    secs = _sections(d)
    if not secs or not any(s[1] == SHT_HASH for s in secs):
        return None
    syms = _symbols(d, secs)
    off = next(s for s in secs if s[1] == SHT_HASH)[4]
    nb, nc = struct.unpack_from("<II", d, off)
    buckets = struct.unpack_from(f"<{nb}I", d, off + 8)
    chains = struct.unpack_from(f"<{nc}I", d, off + 8 + 4 * nb)
    miss = []
    for name in syms[1:]:
        if not name:
            continue
        i, seen = buckets[elf_hash(name) % nb], 0
        while i and syms[i] != name and seen < nc:
            i, seen = chains[i], seen + 1
        if not i or syms[i] != name:
            miss.append(name.decode("utf-8", "replace"))
    return any(s[1] == SHT_GNU_HASH for s in secs), miss


def rebuild(d):
    secs = _sections(d)
    syms = _symbols(d, secs)
    off = next(s for s in secs if s[1] == SHT_HASH)[4]
    nb, nc = struct.unpack_from("<II", d, off)
    assert nc == len(syms)
    buckets, chains = [0] * nb, [0] * nc
    for i in range(1, nc):  # mesma regra do ld: cada simbolo entra no inicio da cadeia do seu balde
        b = elf_hash(syms[i]) % nb
        chains[i], buckets[b] = buckets[b], i
    out = bytearray(d)
    struct.pack_into(f"<{nb}I", out, off + 8, *buckets)
    struct.pack_into(f"<{nc}I", out, off + 8 + 4 * nb, *chains)
    return bytes(out)


def main():
    mode, apk = sys.argv[1], sys.argv[2]
    zin = zipfile.ZipFile(apk)
    zout = zipfile.ZipFile(sys.argv[3], "w", allowZip64=True) if mode == "fix" else None
    for info in zin.infolist():
        name = info.filename
        if zout and name.startswith("META-INF/") and (name.upper().endswith(SIG_EXT) or name == "META-INF/MANIFEST.MF"):
            continue
        data = zin.read(info)
        if name.endswith(".so"):
            r = check(data)
            if r and r[1]:
                gnu, miss = r
                print(f"{name}: {len(miss)} simbolos inacessiveis{' (TEM .gnu.hash - nao corrigido)' if gnu else ''}: "
                      + ", ".join(miss[:4]) + (" ..." if len(miss) > 4 else ""))
                if zout and not gnu:
                    data = rebuild(data)
                    left = check(data)[1]
                    print(f"   -> corrigido, restam {len(left)}")
        if zout:
            zi = zipfile.ZipInfo(name, date_time=info.date_time)
            zi.compress_type = info.compress_type
            zi.external_attr, zi.internal_attr, zi.create_system = info.external_attr, info.internal_attr, info.create_system
            zout.writestr(zi, data)
    if zout:
        zout.close()


if __name__ == "__main__":
    main()
