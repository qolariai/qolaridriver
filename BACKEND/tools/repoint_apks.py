# -*- coding: utf-8 -*-
"""Troca o endereco do backend gravado nas fontes descompiladas (smali/res/assets) das 3 APKs.

    python repoint_apks.py scan  <app>     # so conta e mostra contextos (nada e alterado)
    python repoint_apks.py apply <app> [smali|rest]  # substitui (so pastas smali*, so o resto, ou tudo)

<app> = rider | driver | fleet.  A lista fica em BACKEND/tools/repoint_<app>.json (para refazer/desfazer)
e diz que pastas smali_classesN mudaram -> so esses classesN.dex precisam de ser montados de novo.
"""
import json, os, sys, collections
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OLD_IP = b"192.168.1.204"
# (pastas fonte, [(antigo, novo)])  -- a ordem conta: com porta primeiro
APPS = {
    "rider": (["USER/work_base", "USER/work_splits"], [(b"192.168.1.204:8090", b"127.0.0.1:8090")]),
    # o Driver tinha o IP sem porta (porta 80); no telemovel o adb reverse nao abre portas < 1024
    "driver": (["DRIVER/decoded"], [(b"192.168.1.204", b"127.0.0.1:8091")]),
    "fleet": (["FLEET/qolarifleet_src"], [(b"192.168.1.204:3000", b"127.0.0.1:3000")]),
}
SKIP_DIRS = {"build", "original"}


def files_with_ip(src: Path, part: str = ""):
    src = Path("\\\\?\\" + str(src.resolve()))  # prefixo \\?\ : caminhos com mais de 260 caracteres
    for dp, dn, fn in os.walk(src):
        if Path(dp) == src:
            dn[:] = [d for d in dn if d not in SKIP_DIRS
                     and (not part or (d.startswith("smali") == (part == "smali")))]
        for f in fn:
            if Path(dp) == src and f == "AndroidManifest.xml":
                continue  # so tem o IP como android:host dos deep links (uma porta ai nao faz sentido)
            p = Path(dp, f)
            try:
                data = p.read_bytes()
            except OSError:
                continue
            if OLD_IP in data or OLD_IP.decode().encode("utf-16le") in data:
                yield p, data


def main():
    mode, app = sys.argv[1], sys.argv[2]
    part = sys.argv[3] if len(sys.argv) > 3 else ""
    srcs, reps = APPS[app]
    report = {"files": [], "dirs": collections.Counter(), "binary": [], "utf16": [], "leftover": []}
    contexts = collections.Counter()
    for s in srcs:
        src = ROOT / s
        if s.endswith("work_splits"):
            walk = (x for sp in sorted(src.iterdir()) if sp.is_dir() for x in files_with_ip(sp, part))
        else:
            walk = files_with_ip(src, part)
        for p, data in walk:
            rel = Path(str(p)[4:]).relative_to(ROOT).as_posix()
            top = "/".join(Path(str(p)[4:]).relative_to(src).parts[:2 if s.endswith("work_splits") else 1])
            if OLD_IP.decode().encode("utf-16le") in data:
                report["utf16"].append(rel)
            try:
                data.decode("utf-8")
                is_text = True
            except UnicodeDecodeError:
                is_text = False
            if not is_text:
                report["binary"].append(rel)
                continue
            new = data
            for a, b in reps:
                new = new.replace(a, b)
            if OLD_IP in new:
                report["leftover"].append(rel)
            i = data.find(OLD_IP)
            while i >= 0:
                contexts[data[max(0, i - 25):i + 25].decode("utf-8", "replace").replace("\n", "\\n")] += 1
                i = data.find(OLD_IP, i + 1)
            if new != data:
                report["files"].append(rel)
                report["dirs"][f"{s}/{top}"] += 1
                if mode == "apply":
                    p.write_bytes(new)
    out = Path(__file__).with_name(f"repoint_{app}{'_' + part if part else ''}.json")
    if mode == "apply":
        out.write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"{app}: {len(report['files'])} ficheiros de texto {'alterados' if mode == 'apply' else 'a alterar'}")
    for d, n in sorted(report["dirs"].items()):
        print(f"   {n:6}  {d}")
    for k in ("binary", "utf16", "leftover"):
        if report[k]:
            print(f" {k}: {len(report[k])}")
            for r in report[k][:30]:
                print("    ", r)
    if mode == "scan":
        print(" contextos mais comuns:")
        for c, n in contexts.most_common(60):
            print(f"   {n:5}  {c}")


if __name__ == "__main__":
    main()
