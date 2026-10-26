# -*- coding: utf-8 -*-
"""Drawables partidos numa APK: referencias que o apktool perdeu e ficaram @null (ex.: <bitmap src=@null>),
que rebentam a app ao inflar ("<bitmap> requires a valid 'src' attribute").

    python fix_null_drawables.py scan <apk>
    python fix_null_drawables.py fix  <apk-entrada> <apk-saida>

`fix` troca cada ficheiro partido pelos bytes de um drawable valido da propria APK (como o
DRIVER/fix_res/patch_apk.py fez a mao na Driver): forma transparente por omissao, cinzento escuro
para splash/botoes primarios, branco para botoes secundarios. Nao toca em codigo nem no resources.arsc.
Depois: zipalign -p -f 4 + apksigner.
"""
import struct, sys, zipfile

TYPE_NULL, TYPE_REFERENCE = 0x00, 0x01
NEEDS = {  # elemento -> atributo obrigatorio quando o elemento nao tem filhos
    "bitmap": "src", "nine-patch": "src", "item": "drawable", "inset": "drawable", "clip": "drawable",
    "scale": "drawable", "rotate": "drawable", "animated-rotate": "drawable", "layer": "drawable",
}
DONOR_CANDIDATES = {
    "trans": ["res/drawable/common_google_signin_btn_icon_dark_focused.xml"],
    "dark": ["res/drawable/divider_horizontal_dark.xml"],
    "white": ["res/drawable/abc_cab_background_internal_bg.xml"],
}


def _pool(buf, off):
    count, _, flags, sstart = struct.unpack_from("<IIII", buf, off + 8)
    hsz = struct.unpack_from("<H", buf, off + 2)[0]
    utf8 = flags & 0x100
    out = []
    for k in range(count):
        o = off + sstart + struct.unpack_from("<I", buf, off + hsz + 4 * k)[0]
        if utf8:
            n = buf[o]; o += 2 if n & 0x80 else 1
            n = buf[o]
            if n & 0x80:
                n = ((n & 0x7F) << 8) | buf[o + 1]; o += 2
            else:
                o += 1
            out.append(buf[o:o + n].decode("utf-8", "replace"))
        else:
            n = struct.unpack_from("<H", buf, o)[0]; o += 2
            if n & 0x8000:
                n = ((n & 0x7FFF) << 16) | struct.unpack_from("<H", buf, o)[0]; o += 2
            out.append(buf[o:o + 2 * n].decode("utf-16le", "replace"))
    return out


def broken_elements(buf: bytes):
    """[(elemento, atributo)] com o atributo obrigatorio a @null e sem elementos filhos."""
    if len(buf) < 8 or struct.unpack_from("<H", buf, 0)[0] != 0x0003:
        return []
    strings, i, size = [], 8, len(buf)
    stack, found = [], []
    while i < size:
        typ, hsz, csz = struct.unpack_from("<HHI", buf, i)
        if csz == 0:
            break
        if typ == 0x0001:
            strings = _pool(buf, i)
        elif typ == 0x0102:  # start element
            name = strings[struct.unpack_from("<I", buf, i + 20)[0]]
            astart, asize, acount = struct.unpack_from("<HHH", buf, i + 24)
            attrs = {}
            for k in range(acount):
                a = i + 16 + astart + k * asize
                aname = strings[struct.unpack_from("<I", buf, a + 4)[0]]
                dtype, data = buf[a + 15], struct.unpack_from("<I", buf, a + 16)[0]
                attrs[aname] = (dtype, data)
            if stack:
                stack[-1][2] = True  # o pai tem filhos
            stack.append([name, attrs, False])
        elif typ == 0x0103:  # end element
            name, attrs, has_children = stack.pop()
            need = NEEDS.get(name)
            if need and not has_children and "color" not in attrs:  # <item android:color> = seletor de cor
                v = attrs.get(need)
                if v is None or v[0] == TYPE_NULL or (v[0] == TYPE_REFERENCE and v[1] == 0):
                    found.append((name, need))
        i += csz
    return found


def scan(apk):
    z = zipfile.ZipFile(apk)
    res = {}
    for info in z.infolist():
        n = info.filename
        if n.startswith("res/") and n.endswith(".xml") and "/drawable" in n:
            b = broken_elements(z.read(info))
            if b:
                res[n] = b
    return res


def donor_kind(name: str) -> str:
    low = name.lower()
    if "splash" in low or "button_primary" in low:
        return "dark"
    if "button_secondary" in low or "button_split" in low:
        return "white"
    return "trans"


def main():
    cmd, apk = sys.argv[1], sys.argv[2]
    broken = scan(apk)
    for n, b in sorted(broken.items()):
        print(f"{n:80} {b}")
    print(f"{len(broken)} drawables partidos")
    if cmd != "fix":
        return
    zin = zipfile.ZipFile(apk)
    names = set(zin.namelist())
    donors = {}
    for kind, cands in DONOR_CANDIDATES.items():
        c = next((x for x in cands if x in names and not broken_elements(zin.read(x))), None)
        if not c:
            sys.exit(f"sem dador '{kind}' nesta APK")
        donors[kind] = zin.read(c)
    zout = zipfile.ZipFile(sys.argv[3], "w", allowZip64=True)
    for info in zin.infolist():
        n = info.filename
        if n.startswith("META-INF/") and n.upper().endswith((".SF", ".RSA", ".EC", ".DSA", "MANIFEST.MF")):
            continue
        data = donors[donor_kind(n)] if n in broken else zin.read(info)
        zi = zipfile.ZipInfo(n, date_time=info.date_time)
        zi.compress_type = info.compress_type
        zi.external_attr, zi.internal_attr, zi.create_system = info.external_attr, info.internal_attr, info.create_system
        zout.writestr(zi, data)
    zout.close()
    print("corrigidos:", len(broken))


if __name__ == "__main__":
    main()
