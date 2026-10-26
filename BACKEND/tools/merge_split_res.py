# -*- coding: utf-8 -*-
"""Junta a uma APK os recursos de ficheiro (drawables por densidade) que so existiam num split da Play Store.

    python merge_split_res.py <apk> <split.apk> <saida.apk> [--type drawable] [--check-r <R.smali>] [--only a,b]

A Driver foi rebrandeada a partir da base.apk sem os splits de densidade: 176 drawables (icone da notificacao do
servico "online" ub__ic_carbon_notification, marcadores de recolha/destino, setas de navegacao...) ficaram sem
entrada no resources.arsc. Ao ficar online a app caia com BadForegroundServiceNotificationException
("Couldn't create icon ... id=0x7f080cf3"). Visto a 12-10.

Para cada entrada do tipo no split que falta na APK (mesmo ID; com --check-r confirma-se o nome no R da app):
- nomes acrescentados ao pool de chaves do pacote, caminhos ao pool global do resources.arsc;
- a entrada vai para o bloco da APK com a mesma configuracao (densidade...) ou para um bloco novo;
- os ficheiros (png/webp) do split sao copiados para a APK no mesmo caminho.
Depois: zipalign -p -f 4 + apksigner (a assinatura antiga e retirada).
"""
import re, struct, sys, zipfile

sys.path.insert(0, __file__.rsplit("\\", 1)[0] if "\\" in __file__ else __file__.rsplit("/", 1)[0])
from set_firebase_res import append_to_pool, read_pool  # noqa: E402

RES_TABLE, RES_POOL, RES_PACKAGE, RES_TYPE, RES_SPEC = 0x0002, 0x0001, 0x0200, 0x0201, 0x0202
TYPE_STRING = 0x03
NO_ENTRY = 0xFFFFFFFF


def chunks(buf, start, end):
    i = start
    while i < end:
        t, h, s = struct.unpack_from("<HHI", buf, i)
        yield i, t, h, s
        i += s


def parse(arsc):
    """-> dict com pool global, pacote (offsets, pools) e lista de chunks do pacote."""
    hsz, size = struct.unpack_from("<HI", arsc, 2)
    out = {}
    for i, t, h, s in chunks(arsc, hsz, size):
        if t == RES_POOL:
            out["gpool"] = (i, s)
        elif t == RES_PACKAGE:
            ts, _, ks, _ = struct.unpack_from("<IIII", arsc, i + 268)
            out["pkg"] = (i, h, s, ts, ks)
            out["types"] = read_pool(arsc[i + ts:])
            out["keys"] = read_pool(arsc[i + ks:])
            out["pkg_chunks"] = [c for c in chunks(arsc, i + h, i + s) if c[1] != RES_POOL]  # sem os 2 pools
    return out


def raw_entries(arsc, j, th):
    """{indice: bytes} de todas as entradas (simples ou complexas) de um RES_TYPE nao esparso."""
    flags, = struct.unpack_from("<B", arsc, j + 9)
    if flags:
        raise SystemExit(f"bloco com flags {flags} (esparso/offset16) nao suportado")
    n, start = struct.unpack_from("<II", arsc, j + 12)
    out = {}
    for k, eo in enumerate(struct.unpack_from(f"<{n}I", arsc, j + th)):
        if eo == NO_ENTRY:
            continue
        e = j + start + eo
        esize, eflags = struct.unpack_from("<HH", arsc, e)
        if eflags & 1:  # complexa: cabecalho + count * ResTable_map (12 bytes)
            total = esize + 12 * struct.unpack_from("<I", arsc, e + 12)[0]
        else:
            total = esize + struct.unpack_from("<H", arsc, e + esize)[0]
        out[k] = bytes(arsc[e:e + total])
    return out


def type_entries(arsc, j, th):
    """{indice: (key, dtype, data)} das entradas simples."""
    out = {}
    for k, raw in raw_entries(arsc, j, th).items():
        esize, eflags, key = struct.unpack_from("<HHI", raw, 0)
        if not eflags & 1:
            _, _, dtype, data = struct.unpack_from("<HBBI", raw, esize)
            out[k] = (key, dtype, data)
    return out


def file_entry(key: int, string_idx: int) -> bytes:
    return struct.pack("<HHI", 8, 0, key) + struct.pack("<HBBI", 8, 0, TYPE_STRING, string_idx)


def build_type(type_id, config: bytes, entry_count: int, entries: dict) -> bytes:
    """RES_TYPE nao esparso: entries {indice: bytes da entrada}."""
    hdr = 20 + len(config)
    offs, body = [NO_ENTRY] * entry_count, bytearray()
    for k in sorted(entries):
        offs[k] = len(body)
        body += entries[k]
    start = hdr + 4 * entry_count
    size = start + len(body)
    return (struct.pack("<HHIBBHII", RES_TYPE, hdr, size, type_id, 0, 0, entry_count, start) + config
            + struct.pack(f"<{entry_count}I", *offs) + bytes(body))


def main():
    a = sys.argv[1:]
    apk, split, out = a[0], a[1], a[2]
    tname = a[a.index("--type") + 1] if "--type" in a else "drawable"
    rnames = {}
    only = set(a[a.index("--only") + 1].split(",")) if "--only" in a else None
    if "--check-r" in a:
        txt = open(a[a.index("--check-r") + 1], encoding="utf-8").read()
        rnames = {int(v, 16): n for n, v in re.findall(r"\.field public static final (\w+):I = (0x[0-9a-f]{8})", txt)}

    za, zs = zipfile.ZipFile(apk), zipfile.ZipFile(split)
    arsc, sarsc = za.read("resources.arsc"), zs.read("resources.arsc")
    A, B = parse(arsc), parse(sarsc)
    tid = A["types"].index(tname) + 1
    if B["types"].index(tname) + 1 != tid:
        raise SystemExit("id do tipo diferente entre a APK e o split")
    pkg_id = struct.unpack_from("<I", arsc, A["pkg"][0] + 8)[0]
    spec = next(i for i, t, h, s in A["pkg_chunks"] if t == RES_SPEC and arsc[i + 8] == tid)
    count = struct.unpack_from("<I", arsc, spec + 12)[0]

    # o que a APK ja tem (qualquer configuracao) e os blocos por configuracao
    have, ours = set(), {}
    for i, t, h, s in A["pkg_chunks"]:
        if t == RES_TYPE and arsc[i + 8] == tid:
            have |= set(raw_entries(arsc, i, h))
            ours.setdefault(arsc[i + 20:i + h], i)

    gstr, skeys = read_pool(sarsc[B["gpool"][0]:]), B["keys"]
    add = {}  # config -> {indice: (nome, caminho)}
    for i, t, h, s in B["pkg_chunks"]:
        if t != RES_TYPE or sarsc[i + 8] != tid:
            continue
        for k, (key, dtype, data) in type_entries(sarsc, i, h).items():
            if k in have or dtype != TYPE_STRING or k >= count or (only and skeys[key] not in only):
                continue
            rid = (pkg_id << 24) | (tid << 16) | k
            if rnames and rnames.get(rid) != skeys[key]:
                raise SystemExit(f"{rid:#x}: split '{skeys[key]}' != R '{rnames.get(rid)}'")
            add.setdefault(sarsc[i + 20:i + h], {})[k] = (skeys[key], gstr[data])
    files = sorted({p for d in add.values() for _, p in d.values()})
    names = sorted({n for d in add.values() for n, _ in d.values()})
    print(f"{len({k for d in add.values() for k in d})} entradas novas em {len(add)} configuracoes, "
          f"{len(files)} ficheiros")
    if not add:
        raise SystemExit("nada a acrescentar")

    # pools: chaves no pacote, caminhos no pool global
    akeys = A["keys"]
    kpos = {n: i for i, n in enumerate(akeys)}
    new_keys = [n for n in names if n not in kpos]
    p0, ph, ps, pts, pks = A["pkg"]
    kchunk_size = struct.unpack_from("<I", arsc, p0 + pks + 4)[0]
    kchunk, kfirst = append_to_pool(arsc[p0 + pks:p0 + pks + kchunk_size], new_keys)
    kpos.update({n: kfirst + i for i, n in enumerate(new_keys)})
    g0, gs = A["gpool"]
    gchunk, gfirst = append_to_pool(arsc[g0:g0 + gs], files)
    gpos = {p: gfirst + i for i, p in enumerate(files)}

    # blocos do tipo: preencher os existentes com a mesma configuracao, criar os que faltam
    new_chunks = {}
    for cfg, ents in add.items():
        e = {k: file_entry(kpos[n], gpos[p]) for k, (n, p) in ents.items()}
        if cfg in ours:
            j = ours[cfg]
            h = struct.unpack_from("<H", arsc, j + 2)[0]
            old = raw_entries(arsc, j, h)
            new_chunks[j] = build_type(tid, cfg, count, {**old, **e})
        else:
            new_chunks.setdefault("extra", []).append(build_type(tid, cfg, count, e))
    last = max(i for i, t, h, s in A["pkg_chunks"] if t == RES_TYPE and arsc[i + 8] == tid)
    body = bytearray()
    for i, t, h, s in A["pkg_chunks"]:
        body += new_chunks.get(i, arsc[i:i + s])
        if i == last:
            for c in new_chunks.get("extra", []):
                body += c
    # pacote = cabecalho + pool de tipos + pool de chaves (novo) + [o que houver ate ao 1.o filho] + filhos
    first_child = A["pkg_chunks"][0][0]
    pkg = bytearray(arsc[p0:p0 + pks]) + kchunk + arsc[p0 + pks + kchunk_size:first_child] + body
    struct.pack_into("<I", pkg, 4, len(pkg))
    hsz = struct.unpack_from("<H", arsc, 2)[0]
    table = bytearray(arsc[:hsz]) + gchunk + arsc[g0 + gs:p0] + pkg + arsc[p0 + ps:]
    struct.pack_into("<I", table, 4, len(table))

    existing = set(za.namelist())
    with zipfile.ZipFile(out, "w") as zo:
        for info in za.infolist():
            n = info.filename
            if n.startswith("META-INF/") and n.rsplit(".", 1)[-1] in ("SF", "RSA", "EC", "DSA", "MF"):
                continue
            data = table if n == "resources.arsc" else za.read(n)
            zo.writestr(info, bytes(data), compress_type=info.compress_type)
        for p in files:
            if p in existing:
                print("ja existe na APK:", p)
                continue
            zo.writestr(zipfile.ZipInfo(p, (1981, 1, 1, 1, 1, 0)), zs.read(p), compress_type=zipfile.ZIP_STORED)
    print("escrito", out, "- falta zipalign + apksigner")


if __name__ == "__main__":
    main()
