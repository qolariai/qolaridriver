# -*- coding: utf-8 -*-
"""P2d - gera stack.md a partir de uma pasta apktool (so leitura).

Uso: python stack_report.py --decoded <pasta_apktool> --out <stack.md> [--inventory <inventory.json>]
Conta pacotes de bibliotecas em smali*/ e sufixos de classes (ViewModel, Presenter, ...). Nao le logica de negocio.
"""
import argparse
import json
import os
import sys
from pathlib import Path

LIBS = [
    ("Compose (UI)", "androidx/compose"), ("ConstraintLayout", "androidx/constraintlayout"),
    ("Material Components", "com/google/android/material"), ("Navigation (AndroidX)", "androidx/navigation"),
    ("Retrofit", "retrofit2"), ("OkHttp", "okhttp3"), ("Gson", "com/google/gson"), ("Moshi", "com/squareup/moshi"),
    ("RxJava", "io/reactivex"), ("Coroutines", "kotlinx/coroutines"), ("Dagger", "dagger"), ("Hilt", "dagger/hilt"),
    ("RIBs (Uber)", "com/uber/rib"), ("Room", "androidx/room"), ("DataStore", "androidx/datastore"),
    ("WorkManager", "androidx/work"), ("Glide", "com/bumptech/glide"), ("Coil", "coil"), ("Picasso", "com/squareup/picasso"),
    ("Lottie", "com/airbnb/lottie"), ("ExoPlayer", "com/google/android/exoplayer2"), ("Media3", "androidx/media3"),
    ("Protobuf", "com/google/protobuf"), ("gRPC", "io/grpc"),
    ("Google Maps SDK", "com/google/android/gms/maps"), ("Play Services Location", "com/google/android/gms/location"),
    ("Firebase Messaging (push)", "com/google/firebase/messaging"), ("Firebase Crashlytics", "com/google/firebase/crashlytics"),
    ("Firebase (geral)", "com/google/firebase"), ("Braintree", "com/braintreepayments"), ("Twilio", "com/twilio"),
    ("Facebook SDK", "com/facebook"), ("AppsFlyer", "com/appsflyer"), ("Adjust", "com/adjust"), ("Sentry", "io/sentry"),
    ("Adyen", "com/adyen"), ("Stripe", "com/stripe"), ("Google Pay", "com/google/android/gms/wallet"),
]
SUFFIXES = ["ViewModel", "Presenter", "Interactor", "Router", "Repository", "Activity", "Fragment", "Worker"]


def smali_roots(dec):
    return sorted(p for p in dec.iterdir() if p.is_dir() and p.name.startswith("smali"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--decoded", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--inventory", type=Path, default=None)
    a = ap.parse_args()
    dec = a.decoded.resolve()
    roots = smali_roots(dec)
    found = []
    for name, pkg in LIBS:
        n = 0
        where = []
        for r in roots:
            d = r / pkg
            if d.is_dir():
                where.append(r.name)
                for _, _, fs in os.walk(d):
                    n += sum(1 for f in fs if f.endswith(".smali"))
        found.append((name, pkg, n, where))
    suf = {s: 0 for s in SUFFIXES}
    total = 0
    for r in roots:
        for _, _, fs in os.walk(r):
            for f in fs:
                if f.endswith(".smali"):
                    total += 1
                    stem = f[:-6]
                    for s in SUFFIXES:
                        if stem.endswith(s):
                            suf[s] += 1
    inv = json.loads(a.inventory.read_text(encoding="utf-8")) if a.inventory and a.inventory.exists() else {}
    compose = next((n for nm, _, n, _ in found if nm.startswith("Compose")), 0)
    lines = ["# stack.md (gerado por stack_report.py)", "",
             f"Fonte: `{dec}` (apktool, read-only). Ficheiros smali: {total} em {len(roots)} pastas.", "",
             "## Toolkit de UI", "",
             f"- Compose: {'presente' if compose else 'ausente'} ({compose} classes em `androidx/compose`).",
             f"- Layouts XML: {inv.get('layouts', 'n/d')} (Views), menus: {inv.get('menu', 'n/d')}.",
             "- Conclusao: a app mistura Views XML e Compose; ver contagens acima antes de escolher a stack da recriacao.", "",
             "## Bibliotecas detetadas (pacote em smali)", "", "| Biblioteca | Pacote | Classes | Presente em |", "|---|---|---|---|"]
    for nm, pkg, n, where in found:
        lines.append(f"| {nm} | `{pkg}` | {n if where else 0} | {', '.join(where) if where else '-'} |")
    lines += ["", "## Padrao arquitetural (sufixos de nomes de classe)", "", "| Sufixo | Classes |", "|---|---|"]
    lines += [f"| {s} | {suf[s]} |" for s in SUFFIXES]
    lines += ["", "Nota: nomes ofuscados reduzem estas contagens; servem so como indicio.", ""]
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text("\n".join(lines), encoding="utf-8")
    print("stack ->", a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
