# -*- coding: utf-8 -*-
"""Mete os valores de um google-services.json numa APK ja compilada (o que o plugin Gradle faria).

    python set_firebase_res.py <apk-entrada> <apk-saida> <google-services.json> <package_name>
    python set_firebase_res.py --strings <strings.xml> <google-services.json> <package_name>

O plugin com.google.gms.google-services nao copia o JSON para a APK: gera recursos string
(google_app_id, google_api_key, gcm_defaultSenderId, project_id, ...). Aqui, no resources.arsc,
as strings novas sao acrescentadas ao fim do string pool global e so as entradas string/<nome>
desses recursos passam a apontar para elas (nenhum indice existente muda; nada e trocado por substring).
Recursos que o JSON nao traz (ex.: firebase_database_url sem Realtime Database) ficam como estavam.
META-INF/*.SF|RSA|EC|DSA|MANIFEST.MF sao retirados. Depois: zipalign -p -f 4 + apksigner.
"""
import json, re, struct, sys, zipfile

from patch_apk_host import RES_STRING_POOL, UTF8_FLAG, _dec_len8, _dec_len16, _enc_len8, _enc_len16, _u16len, SIG_EXT

RES_TABLE_PACKAGE = 0x0200
RES_TABLE_TYPE = 0x0201
TYPE_STRING = 0x03
FLAG_COMPLEX, FLAG_COMPACT = 0x0001, 0x0008
TYPE_FLAG_SPARSE, TYPE_FLAG_OFFSET16 = 0x01, 0x02


def firebase_values(gs_path, package):
    gs = json.load(open(gs_path, encoding="utf-8"))
    info = gs["project_info"]
    client = next(c for c in gs["client"] if c["client_info"]["android_client_info"]["package_name"] == package)
    vals = {
        "google_app_id": client["client_info"]["mobilesdk_app_id"],
        "gcm_defaultSenderId": info["project_number"],
        "project_id": info["project_id"],
    }
    if info.get("storage_bucket"):
        vals["google_storage_bucket"] = info["storage_bucket"]
    if info.get("firebase_url"):
        vals["firebase_database_url"] = info["firebase_url"]
    if client.get("api_key"):
        vals["google_api_key"] = vals["google_crash_reporting_api_key"] = client["api_key"][0]["current_key"]
    web = [o["client_id"] for o in client.get("oauth_client", []) if o.get("client_type") == 3]
    if web:
        vals["default_web_client_id"] = web[0]
    return vals


# ---- string pools ------------------------------------------------------------------------------
def read_pool(chunk):
    hsz = struct.unpack_from("<H", chunk, 2)[0]
    count, scount, flags, sstart, ystart = struct.unpack_from("<IIIII", chunk, 8)
    utf8 = bool(flags & UTF8_FLAG)
    out = []
    for o in struct.unpack_from(f"<{count}I", chunk, hsz):
        i = sstart + o
        if utf8:
            _, i = _dec_len8(chunk, i)
            n, i = _dec_len8(chunk, i)
            out.append(chunk[i:i + n].decode("utf-8", "surrogatepass"))
        else:
            n, i = _dec_len16(chunk, i)
            out.append(chunk[i:i + 2 * n].decode("utf-16le", "surrogatepass"))
    return out


def append_to_pool(chunk, extra):
    """Acrescenta strings ao fim do pool; devolve (novo_chunk, indice_da_primeira)."""
    typ, hsz, size = struct.unpack_from("<HHI", chunk, 0)
    count, scount, flags, sstart, ystart = struct.unpack_from("<IIIII", chunk, 8)
    utf8 = bool(flags & UTF8_FLAG)
    offs = list(struct.unpack_from(f"<{count}I", chunk, hsz))
    soffs = chunk[hsz + 4 * count:hsz + 4 * count + 4 * scount]
    data = bytearray(chunk[sstart:ystart if scount else size])
    styles = chunk[ystart:size] if scount else b""
    for s in extra:  # depois do enchimento antigo (os offsets sao diretos, zeros a mais nao fazem mal)
        offs.append(len(data))
        if utf8:
            raw = s.encode("utf-8")
            data += _enc_len8(_u16len(s)) + _enc_len8(len(raw)) + raw + b"\x00"
        else:
            raw = s.encode("utf-16le")
            data += _enc_len16(len(raw) // 2) + raw + b"\x00\x00"
    while len(data) % 4:
        data += b"\x00"
    ncount = count + len(extra)
    nsstart = hsz + 4 * ncount + 4 * scount
    nystart = nsstart + len(data) if scount else 0
    body = struct.pack(f"<{ncount}I", *offs) + soffs + bytes(data) + styles
    header = struct.pack("<HHIIIIII", typ, hsz, hsz + len(body), ncount, scount, flags, nsstart, nystart) + chunk[28:hsz]
    return header + body, count


# ---- resources.arsc ----------------------------------------------------------------------------
def string_entries(arsc, wanted):
    """[(offset_do_campo_data, nome)] das entradas string/<nome> com valor TYPE_STRING."""
    hits = []
    hsz, size = struct.unpack_from("<HI", arsc, 2)
    i = hsz
    while i < size:
        ctyp, chsz, csize = struct.unpack_from("<HHI", arsc, i)
        if ctyp == RES_TABLE_PACKAGE:
            type_off, _, key_off = struct.unpack_from("<III", arsc, i + 268)
            types = read_pool(arsc[i + type_off:])
            keys = read_pool(arsc[i + key_off:])
            j = i + chsz
            while j < i + csize:
                ttyp, thsz, tsize = struct.unpack_from("<HHI", arsc, j)
                if ttyp == RES_TABLE_TYPE and types[arsc[j + 8] - 1] == "string":
                    tflags = arsc[j + 9]
                    n, start = struct.unpack_from("<II", arsc, j + 12)
                    for k in range(n):
                        if tflags & TYPE_FLAG_SPARSE:
                            eo = struct.unpack_from("<H", arsc, j + thsz + 4 * k + 2)[0] * 4
                        elif tflags & TYPE_FLAG_OFFSET16:
                            eo = struct.unpack_from("<H", arsc, j + thsz + 2 * k)[0]
                            eo = 0xFFFFFFFF if eo == 0xFFFF else eo * 4
                        else:
                            eo = struct.unpack_from("<I", arsc, j + thsz + 4 * k)[0]
                        if eo == 0xFFFFFFFF:
                            continue
                        e = j + start + eo
                        esize, eflags = struct.unpack_from("<HH", arsc, e)
                        if eflags & FLAG_COMPACT:
                            key, dtype, data_at = esize, eflags >> 8, e + 4
                        elif eflags & FLAG_COMPLEX:
                            continue
                        else:
                            key = struct.unpack_from("<I", arsc, e + 4)[0]
                            dtype, data_at = arsc[e + 8 + 3], e + 8 + 4
                        if dtype == TYPE_STRING and keys[key] in wanted:
                            hits.append((data_at, keys[key]))
                j += tsize
        i += csize
    return hits


def patch_arsc(arsc, vals):
    hsz = struct.unpack_from("<H", arsc, 2)[0]
    gsize = struct.unpack_from("<I", arsc, hsz + 4)[0]
    names = sorted(vals)
    newpool, first = append_to_pool(arsc[hsz:hsz + gsize], [vals[n] for n in names])
    out = bytearray(arsc[:hsz] + newpool + arsc[hsz + gsize:])
    struct.pack_into("<I", out, 4, len(out))
    done = []
    for at, name in string_entries(bytes(out), set(names)):
        struct.pack_into("<I", out, at, first + names.index(name))
        done.append(name)
    return bytes(out), done


def mask(v):
    return v if len(v) <= 12 else v[:6] + "…" + v[-3:]


def patch_strings_xml(path, vals):
    txt = open(path, encoding="utf-8").read()
    for n, v in vals.items():
        txt, k = re.subn(rf'(<string name="{re.escape(n)}"[^>]*>)[^<]*(</string>)', lambda m: m.group(1) + v + m.group(2), txt)
        if not k:
            txt = txt.replace("</resources>", f'    <string name="{n}" translatable="false">{v}</string>\n</resources>')
        print(f"   {n} = {mask(v)}" + ("" if k else " (novo)"))
    open(path, "w", encoding="utf-8", newline="").write(txt)


def main():
    """Tambem:  --res <apk> <saida> nome=valor [...]          (recursos string/<nome>, ex. a chave do Google Maps)
                --manifest <apk> <saida> antigo=novo [...]   (literal no AndroidManifest.xml binario, ex. geo.API_KEY)"""
    if sys.argv[1] == "--strings":
        xml, gs, pkg = sys.argv[2:5]
        patch_strings_xml(xml, firebase_values(gs, pkg))
        return
    if sys.argv[1] in ("--res", "--manifest"):
        mode, (src, dst), pairs = sys.argv[1], sys.argv[2:4], dict(a.split("=", 1) for a in sys.argv[4:])
        return rewrite_apk(src, dst, pairs if mode == "--res" else {}, pairs if mode == "--manifest" else {})
    src, dst, gs, pkg = sys.argv[1:5]
    rewrite_apk(src, dst, firebase_values(gs, pkg), {})


def rewrite_apk(src, dst, vals, manifest):
    from patch_apk_host import patch_container
    zin = zipfile.ZipFile(src)
    zout = zipfile.ZipFile(dst, "w", allowZip64=True)
    for info in zin.infolist():
        name = info.filename
        if name.startswith("META-INF/") and (name.upper().endswith(SIG_EXT) or name == "META-INF/MANIFEST.MF"):
            continue
        data = zin.read(info)
        if name == "AndroidManifest.xml" and manifest:
            for old, new in manifest.items():
                data, n = patch_container(data, old, new)
                print(f"   AndroidManifest.xml: {mask(old)} -> {mask(new)} ({n} strings)")
        if name == "resources.arsc" and vals:
            data, done = patch_arsc(data, vals)
            for n in sorted(set(done)):
                print(f"   {n} = {mask(vals[n])} ({done.count(n)} config)")
            for n in sorted(set(vals) - set(done)):
                print(f"   AVISO: {n} nao existe na APK (nao acrescentado)")
        zi = zipfile.ZipInfo(name, date_time=info.date_time)
        zi.compress_type = info.compress_type
        zi.external_attr, zi.internal_attr, zi.create_system = info.external_attr, info.internal_attr, info.create_system
        zout.writestr(zi, data)
    zout.close()


if __name__ == "__main__":
    main()
