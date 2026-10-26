# -*- coding: utf-8 -*-
"""Troca o endereco do backend dentro de uma APK ja compilada, sem a recompilar com o apktool.

    python patch_apk_host.py <apk-entrada> <apk-saida> <antigo> <novo> [classesN.dex=<ficheiro> ...]

- classesN.dex: substituido pelo ficheiro dado (montado com o smali a partir da fonte ja corrigida);
  um .dex que ainda contenha o endereco antigo e nao tenha substituto e assinalado.
- resources.arsc e XML binarios (res/*.xml): o string pool e reescrito
  (tamanhos/offsets recalculados; os spans de estilo sao deslocados).
- restantes ficheiros de texto (assets, ficheiros soltos): substituicao direta.
- META-INF/*.SF|RSA|EC|DSA|MANIFEST.MF sao retirados (a APK tem de ser assinada outra vez).
- AndroidManifest.xml nao e tocado: so la aparece o IP como android:host dos deep links (sem porta).

Tudo o resto (bibliotecas nativas, imagens, drawables corrigidos a mao, ordem e compressao das entradas)
fica igual. Depois: zipalign -p -f 4 + apksigner.
"""
import struct, sys, zipfile

RES_STRING_POOL = 0x0001
RES_TABLE = 0x0002
RES_XML = 0x0003
UTF8_FLAG = 0x100


# ---- string pool -----------------------------------------------------------------------------
def _dec_len8(b, i):
    n = b[i]
    if n & 0x80:
        return ((n & 0x7F) << 8) | b[i + 1], i + 2
    return n, i + 1


def _dec_len16(b, i):
    n = struct.unpack_from("<H", b, i)[0]
    if n & 0x8000:
        return ((n & 0x7FFF) << 16) | struct.unpack_from("<H", b, i + 2)[0], i + 4
    return n, i + 2


def _enc_len8(n):
    if n > 0x7FFF:
        raise ValueError("string demasiado longa para UTF-8 pool")
    return bytes([(n >> 8) | 0x80, n & 0xFF]) if n > 0x7F else bytes([n])


def _enc_len16(n):
    if n > 0x7FFF:
        return struct.pack("<HH", (n >> 16) | 0x8000, n & 0xFFFF)
    return struct.pack("<H", n)


def _u16len(s):
    return len(s.encode("utf-16le")) // 2


def rewrite_pool(chunk: bytes, old: str, new: str):
    """Devolve (novo_chunk, n_strings_alteradas)."""
    typ, hsz, size = struct.unpack_from("<HHI", chunk, 0)
    assert typ == RES_STRING_POOL
    count, scount, flags, sstart, ystart = struct.unpack_from("<IIIII", chunk, 8)
    utf8 = bool(flags & UTF8_FLAG)
    offs = struct.unpack_from(f"<{count}I", chunk, hsz)
    soffs = struct.unpack_from(f"<{scount}I", chunk, hsz + 4 * count)
    strings = []
    for o in offs:
        i = sstart + o
        if utf8:
            _, i = _dec_len8(chunk, i)
            blen, i = _dec_len8(chunk, i)
            strings.append(chunk[i:i + blen].decode("utf-8", "surrogatepass"))
        else:
            ulen, i = _dec_len16(chunk, i)
            strings.append(chunk[i:i + 2 * ulen].decode("utf-16le", "surrogatepass"))
    if not any(old in s for s in strings):
        return chunk, 0
    styles = bytearray(chunk[ystart:size]) if scount else bytearray()
    changed = 0
    for idx, s in enumerate(strings):
        if old not in s:
            continue
        changed += 1
        if idx < scount:  # deslocar spans (posicoes em unidades UTF-16)
            delta = _u16len(new) - _u16len(old)
            hits, p = [], s.find(old)
            while p >= 0:
                hits.append(_u16len(s[:p]))
                p = s.find(old, p + len(old))
            j = soffs[idx]
            while True:
                name, first, last = struct.unpack_from("<III", styles, j)
                if name == 0xFFFFFFFF:
                    break
                nf = first + delta * sum(1 for h in hits if h < first)
                nl = last + delta * sum(1 for h in hits if h <= last)
                struct.pack_into("<III", styles, j, name, nf, nl)
                j += 12
        strings[idx] = s.replace(old, new)
    data, new_offs = bytearray(), []
    for s in strings:
        new_offs.append(len(data))
        if utf8:
            raw = s.encode("utf-8", "surrogatepass")
            data += _enc_len8(_u16len(s)) + _enc_len8(len(raw)) + raw + b"\x00"
        else:
            raw = s.encode("utf-16le", "surrogatepass")
            data += _enc_len16(len(raw) // 2) + raw + b"\x00\x00"
    while len(data) % 4:
        data += b"\x00"
    nsstart = hsz + 4 * count + 4 * scount
    nystart = nsstart + len(data) if scount else 0
    body = struct.pack(f"<{count}I", *new_offs) + struct.pack(f"<{scount}I", *soffs) + bytes(data) + bytes(styles)
    nsize = hsz + len(body)
    header = struct.pack("<HHIIIIII", typ, hsz, nsize, count, scount, flags, nsstart, nystart) + chunk[28:hsz]
    return header + body, changed


def patch_container(buf: bytes, old: str, new: str):
    """resources.arsc ou XML binario: reescreve os string pools de 1.o nivel (o global do arsc; o do XML).
    Os pools dos pacotes (nomes de tipos/chaves) nao levam URLs."""
    typ, hsz, size = struct.unpack_from("<HHI", buf, 0)
    out, total = bytearray(buf[:hsz]), 0
    i = hsz
    while i < size:
        ctyp, chsz, csize = struct.unpack_from("<HHI", buf, i)
        chunk = buf[i:i + csize]
        if ctyp == RES_STRING_POOL:
            chunk, n = rewrite_pool(chunk, old, new)
            total += n
        out += chunk
        i += csize
    struct.pack_into("<I", out, 4, len(out))
    return bytes(out), total


def is_res_container(data: bytes):
    return len(data) >= 8 and struct.unpack_from("<H", data, 0)[0] in (RES_TABLE, RES_XML) \
        and struct.unpack_from("<I", data, 4)[0] == len(data)


SIG_EXT = (".SF", ".RSA", ".EC", ".DSA")


def main():
    src, dst, old, new = sys.argv[1:5]
    dex_map = dict(a.split("=", 1) for a in sys.argv[5:])
    ob, o16 = old.encode(), old.encode("utf-16le")
    zin = zipfile.ZipFile(src)
    zout = zipfile.ZipFile(dst, "w", allowZip64=True)
    report = {"dex": [], "res": [], "text": [], "AVISO": []}
    for info in zin.infolist():
        name = info.filename
        if name.startswith("META-INF/") and (name.upper().endswith(SIG_EXT) or name == "META-INF/MANIFEST.MF"):
            continue
        data = zin.read(info)
        if name in dex_map:
            data = open(dex_map[name], "rb").read()
            report["dex"].append(name)
            if ob in data:
                report["AVISO"].append(f"{name}: o dex novo ainda tem {old}")
        elif name != "AndroidManifest.xml" and (ob in data or o16 in data):
            if name.endswith(".dex"):
                report["AVISO"].append(f"{name}: tem {old} e nao foi remontado")
            elif is_res_container(data):
                data, n = patch_container(data, old, new)
                report["res"].append(f"{name} ({n} strings)")
                if ob in data or o16 in data:
                    report["AVISO"].append(f"{name}: ainda tem {old} fora dos string pools")
            else:
                try:
                    data.decode("utf-8")
                    data = data.replace(ob, new.encode())
                    report["text"].append(name)
                except UnicodeDecodeError:
                    report["AVISO"].append(f"{name}: binario com {old} (nao alterado)")
        zi = zipfile.ZipInfo(name, date_time=info.date_time)
        zi.compress_type = info.compress_type
        zi.external_attr, zi.internal_attr, zi.create_system = info.external_attr, info.internal_attr, info.create_system
        zout.writestr(zi, data)
    zout.close()
    for k, v in report.items():
        print(f"{k}: {len(v)}")
        for x in v[:40]:
            print("   ", x)


if __name__ == "__main__":
    main()
