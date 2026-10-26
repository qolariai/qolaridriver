# -*- coding: utf-8 -*-
"""Aponta as fontes smali das 3 APKs do backend local (127.0.0.1:PORTA + adb reverse) para o servidor.

    python repoint_server.py plan  <app>    # mostra o que muda (nada e escrito)
    python repoint_server.py apply <app>    # escreve as fontes + repoint_<app>_server.json (antes/depois, p/ desfazer)

<app> = rider | driver | fleet.  Ficheiros: os de repoint_<app>_smali.json (os unicos com o endereco).

- strings da Google/Firebase que o rebrand antigo tinha mandado para o backend (type.googleapis.com dos protos e
  do Tink, firebaseremoteconfig, app-measurement, firebase.google.com, ...) voltam ao texto original, tirado das
  strings dos .dex da APK original da Uber (Rider sem original: usa as da Driver e da Fleet - mesmos SDKs);
- o resto: http(s)://127.0.0.1:PORTA -> https://<app>.qolari.com, ws:// -> wss://, 127.0.0.1:PORTA -> <app>.qolari.com.
Depois: apktool b incremental (so os smali_classesN alterados) + patch_apk_host.py (dex + recursos) + zipalign + apksigner.
"""
import collections, json, os, re, struct, sys, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AND = ROOT / "ANDOIRD"
APPS = {
    "driver": {"port": 8091, "host": "driver.qolari.com", "orig": ["DRIVER/source-original.apk"]},
    "fleet": {"port": 3000, "host": "fleet.qolari.com", "orig": ["FLEET/original.apk"]},
    "rider": {"port": 8090, "host": "rider.qolari.com", "orig": ["DRIVER/source-original.apk", "FLEET/original.apk"],
              "own_original": False},
}
GOOGLE = (r"(?:[a-z0-9-]+\.)*(?:googleapis\.com|google\.com|app-measurement\.com|googleadservices\.com|"
          r"googlesyndication\.com|doubleclick\.net|firebaseio\.com|crashlytics\.com|gstatic\.com|"
          r"google-analytics\.com|googleusercontent\.com|youtube\.com|android\.com|firebaseapp\.com)")
GOOGLE_RE = re.compile(r"(?:https?://)?" + GOOGLE, re.I)
# qualquer host (com/sem esquema) - o indice tem tambem os originais da Uber: so se repoe quando o UNICO
# original com o mesmo esqueleto e da Google
HOST_RE = re.compile(r"((?:https?|wss?)://)?(?:[A-Za-z0-9-]+\.)+(?:com|net|org|io|co|app|dev|me|info|biz|link|ly|gl|us|uk|br|pt|in|cn|tv)"
                     r"(?::\d+)?(?![A-Za-z0-9-])")
IP_RE = re.compile(r"((?:\w+)://)?127\.0\.0\.1(?::\d+)?")
H, HS = "\x00H\x00", "\x00HS\x00"


def skel(s, rx):
    return rx.sub(lambda m: HS if m.group(1) else H, s)
LIT_RE = re.compile(r'"((?:[^"\\]|\\.)*)"')


# ---- strings dos .dex originais ----------------------------------------------------------------
def _uleb(b, i):
    r = s = 0
    while True:
        x = b[i]; i += 1
        r |= (x & 0x7F) << s
        if x < 0x80:
            return r, i
        s += 7


def dex_strings(data):
    n, off = struct.unpack_from("<II", data, 0x38)
    for k in range(n):
        p = struct.unpack_from("<I", data, off + 4 * k)[0]
        _, p = _uleb(data, p)
        e = data.index(b"\x00", p)
        yield data[p:e].decode("utf-8", "replace")


def originals(apks):
    """esqueleto (hosts -> H / HS com esquema) -> {originais}"""
    idx = collections.defaultdict(set)
    for a in apks:
        z = zipfile.ZipFile(AND / a)
        for name in z.namelist():
            if re.fullmatch(r"classes\d*\.dex", name):
                for s in dex_strings(z.read(name)):
                    if HOST_RE.search(s):
                        idx[skel(s, HOST_RE)].add(s)
    return idx


# hosts soltos em classes com/google (o esqueleto nao chega: "H" casa com todos os hosts).
# Valores confirmados nas strings da APK original; chave = (fim do caminho da classe, string atual sem porta)
MANUAL = {
    ("firebase/remoteconfig/internal/ConfigFetchHttpClient.smali", "http://127.0.0.1/v1/projects/"):
        "https://firebaseremoteconfig.googleapis.com/v1/projects/",
    ("firebase/remoteconfig/internal/e.smali", "http://127.0.0.1/v1/projects/"):  # :streamFetchInvalidations
        "https://firebaseremoteconfigrealtime.googleapis.com/v1/projects/",
}
# flags do Google Analytics (measurement/internal/r.smali): o host por omissao vem logo a seguir ao nome da flag
FLAG_DEFAULTS = {
    "measurement.config.url_authority": "app-measurement.com",
    "measurement.rb.attribution.uri_authority": "google-analytics.com",
}
FLAG_RE = re.compile(r'(const-string(?:/jumbo)? \w+, "(' + "|".join(map(re.escape, FLAG_DEFAULTS)) +
                     r')"\s+const-string(?:/jumbo)? \w+, )"127\.0\.0\.1(?::\d+)?"')


# ---- literais smali ------------------------------------------------------------------------------
def unesc(s):
    return re.sub(r'\\(u[0-9a-fA-F]{4}|.)', lambda m: chr(int(m.group(1)[1:], 16)) if m.group(1)[0] == "u" and len(m.group(1)) == 5
                  else {"n": "\n", "t": "\t", "r": "\r", "b": "\b", "f": "\f", "0": "\0"}.get(m.group(1), m.group(1)), s)


def esc(s):
    out = []
    for c in s:
        if c in '"\\':
            out.append("\\" + c)
        elif c == "\n":
            out.append("\\n")
        elif c == "\t":
            out.append("\\t")
        elif c == "\r":
            out.append("\\r")
        elif ord(c) < 0x20 or ord(c) > 0x7E:
            out.append("\\u%04x" % ord(c))
        else:
            out.append(c)
    return "".join(out)


def to_server(s, port, host):
    ip = re.escape(f"127.0.0.1:{port}")
    s = re.sub(r"(?:http|https)://" + ip, "https://" + host, s)
    s = re.sub(r"(?:ws|wss)://" + ip, "wss://" + host, s)
    return re.sub(ip, host, s)


def read(p):
    for q in (str(p), "\\\\?\\" + str(p.resolve())):
        try:
            return open(q, "rb").read()
        except OSError:
            pass
    raise OSError(p)


def write(p, data):
    for q in (str(p), "\\\\?\\" + str(p.resolve())):
        try:
            open(q, "wb").write(data)
            return
        except OSError:
            pass
    raise OSError(p)


def main():
    mode, app = sys.argv[1], sys.argv[2]
    cfg = APPS[app]
    port, host = cfg["port"], cfg["host"]
    files = json.load(open(Path(__file__).with_name(f"repoint_{app}_smali.json"), encoding="utf-8"))["files"]
    idx = originals(cfg["orig"])
    log = {"google": collections.Counter(), "server": collections.Counter(), "ambiguous": collections.Counter(),
           "manual": collections.Counter(), "leftover": [], "dirs": collections.Counter(), "files": {}}
    for rel in files:
        p = AND / rel
        txt = read(p).decode("utf-8")
        changes = []

        def fix(m):
            raw = m.group(1)
            if "127.0.0.1" not in raw:
                return m.group(0)
            s = unesc(raw)
            cands = idx.get(skel(s, IP_RE), set())
            goog = "/com/google/" in rel
            key = (rel.split("/com/google/")[-1], re.sub(r"127\.0\.0\.1:\d+", "127.0.0.1", s))
            if goog and key in MANUAL:
                new = MANUAL[key]
                log["google"][(s, new)] += 1
            elif len(cands) == 1 and GOOGLE_RE.search(next(iter(cands))) and \
                    (cfg.get("own_original", True) or re.search(r"google|firebase", s, re.I)):
                # sem APK original propria (Rider) o indice nao tem os hosts Uber da app: so com "google" no texto
                new = next(iter(cands))
                log["google"][(s, new)] += 1
            else:
                if len(cands) > 1:
                    log["manual" if goog else "ambiguous"][(rel.split("/com/google/")[-1] if goog else "", s,
                                                             " | ".join(sorted(cands)[:4]))] += 1
                new = to_server(s, port, host)
                log["server"][(s, new)] += 1
            changes.append((s, new))
            return '"' + esc(new) + '"'

        def flag(m):
            log["google"][(m.group(2) + " = 127.0.0.1", FLAG_DEFAULTS[m.group(2)])] += 1
            changes.append(("127.0.0.1 (" + m.group(2) + ")", FLAG_DEFAULTS[m.group(2)]))
            return m.group(1) + '"' + FLAG_DEFAULTS[m.group(2)] + '"'

        new_txt = LIT_RE.sub(fix, FLAG_RE.sub(flag, txt) if "/com/google/" in rel else txt)
        if "127.0.0.1" in new_txt:
            log["leftover"].append(rel)
        if new_txt != txt:
            log["files"][rel] = changes
            log["dirs"][rel.split("/")[0] + "/" + rel.split("/")[1] + "/" + rel.split("/")[2]] += 1
            if mode == "apply":
                write(p, new_txt.encode("utf-8"))
    print(f"{app}: {len(log['files'])} ficheiros {'alterados' if mode == 'apply' else 'a alterar'}; "
          f"strings -> Google original {sum(log['google'].values())}, -> servidor {sum(log['server'].values())}, "
          f"ambiguas {sum(log['ambiguous'].values())}, ficheiros ainda com 127.0.0.1 {len(log['leftover'])}")
    print(" pastas:", dict(sorted(log["dirs"].items())))
    print(" Google repostas:")
    for (a, b), n in sorted(log["google"].items()):
        print(f"   {n}x {a[:70]}  ->  {b[:90]}")
    for k in ("manual", "ambiguous"):
        if log[k]:
            print(f" {k} (foram para o servidor):")
            for (f, a, b), n in sorted(log[k].items(), key=lambda x: -x[1])[:25]:
                print(f"   {n}x {f[:60]} | {a[:60]}  ~  {b[:160]}")
    print(" servidor (amostra):")
    for (a, b), n in log["server"].most_common(12):
        print(f"   {n}x {a[:70]}  ->  {b[:80]}")
    for r in log["leftover"][:20]:
        print("  AINDA COM 127.0.0.1:", r)
    if mode == "apply":
        out = {"files": {k: v for k, v in log["files"].items()}, "dirs": dict(log["dirs"]), "leftover": log["leftover"]}
        Path(__file__).with_name(f"repoint_{app}_server.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
