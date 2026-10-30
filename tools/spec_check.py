# -*- coding: utf-8 -*-
"""Verifica os portoes do PROMPT_CLONE_MEGA para este projeto.

Uso:  python tools/spec_check.py
Saida: lista de PASS/FAIL e codigo 1 se algum portao falhar.
Nao substitui a validacao visual; verifica a existencia e a coerencia dos artefactos.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAP = ROOT / "ANDOIRD" / "DRIVER" / "ux_capture"
NEW = ROOT / "ANDOIRD" / "DRIVER" / "RECRIACAO" / "captures"

REQUIRED = [
    "plan.md",
    "access_plan.md",
    "coverage.md",
    "topology.md",
    "endpoints.json",
    "PROMPT_CLONE_MEGA.md",
    "PROMPT_CLONE_BUILD.md",
    "ux_reference/README.md",
    "device_apk/README.md",
    "ADAPTACAO_PROMPTS.md",
    "VALIDACAO_MEGA.md",
    "capabilities.md",
    "backlog.md",
    "RELATORIO_FINAL.md",
]

STATE_MACHINE = ["requested", "accepted", "arrived", "in_progress", "completed",
                 "cancelled", "no_drivers"]

EVIDENCE = {"live", "served", "static", "unverified", "presumed", "designed"}
INTEGRITY = {"clean", "repack_suspect"}
ENDPOINT_KEYS = {"id", "method", "path", "app", "owner", "producer", "consumers",
                 "screens", "evidence", "implemented"}

SECRET_PATTERNS = [
    re.compile(r"AIza[0-9A-Za-z_-]{20,}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"(?i)(password|passwd|senha)\s*[:=]\s*['\"][^'\"]{4,}['\"]"),
]

problems = []
checks = []


def ok(name, condition, detail=""):
    checks.append((name, bool(condition), detail))
    if not condition:
        problems.append(f"{name}: {detail}")


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def check_files():
    for name in REQUIRED:
        ok(f"artefacto {name}", (ROOT / name).is_file(), "em falta")


def check_closure():
    backlog = read("backlog.md")
    ok("backlog.md declara zero gaps abertos", "Nenhum para `funcional`" in backlog,
       "gaps abertos para o alvo")
    report = read("RELATORIO_FINAL.md")
    ok("RELATORIO_FINAL.md tem veredicto", "Veredicto" in report and "pronto para `funcional`" in report,
       "veredicto ausente")
    caps = read("capabilities.md")
    ok("capabilities.md tem matriz", "| Status |" in caps and "| ok |" in caps,
       "matriz ausente")
    ok("capabilities.md fecha o alvo", "Zero `gap`" in caps, "gaps por declarar")


def check_plan():
    text = read("plan.md")
    for token in ("Credenciais", "Topologia", "Cobertura prometida", "Tolerância declarada",
                  "Modo por role"):
        ok(f"plan.md tem '{token}'", token in text, "secao ausente")
    for token in ("live", "served", "static", "presumed", "designed"):
        ok(f"plan.md declara {token}", token in text, "nivel de evidencia ausente")


def check_coverage():
    text = read("coverage.md")
    rows = [ln for ln in text.splitlines() if ln.startswith("| `") and ln.count("|") >= 10]
    ok("coverage.md tem linhas de ecra", len(rows) >= 100, f"{len(rows)} linhas")
    for ln in rows:
        cols = [c.strip() for c in ln.strip("|").split("|")]
        if len(cols) < 10:
            ok("coverage.md linha completa", False, ln[:80])
            continue
        status = cols[6].replace("*", "")
        if status not in ("sim", "parcial", "nao"):
            ok("coverage.md estado valido", False, ln[:80])
        if status in ("parcial", "nao") and not cols[8]:
            ok("coverage.md gap declarado", False, ln[:80])
        if cols[4] not in EVIDENCE:
            ok("coverage.md evidencia valida", False, ln[:80])
        if cols[5] not in INTEGRITY:
            ok("coverage.md integridade valida", False, ln[:80])
    for token in ("out_of_scope", "thirdparty", "state", "peer", "geo", "flag", "broken"):
        ok(f"coverage.md classifica {token}", token in text, "classificacao ausente")


def check_topology():
    text = read("topology.md")
    for section in ("## 1. Classificação", "## 2. Atores", "## 3. Apps", "## 4. Backends",
                    "## 5. Backoffices", "## 6. Modelo de dados", "## 7. Tempo real",
                    "## 8. Orquestração", "## 9. Fora de âmbito", "## 10. Validação"):
        ok(f"topology.md tem '{section}'", section in text, "secao ausente")
    for state in STATE_MACHINE:
        ok(f"topology.md cobre '{state}'", f"`{state}`" in text, "estado ausente")
    ok("topology.md tem um escritor por campo", "Um escritor por campo" in text, "tabela ausente")
    ok("topology.md tem tres espelhos", "tres espelhos" in text.lower() or "três espelhos" in text,
       "teste ausente")


def check_endpoints():
    data = json.loads(read("endpoints.json"))
    eps = data.get("endpoints", [])
    ok("endpoints.json tem endpoints", len(eps) >= 20, f"{len(eps)} endpoints")
    ids = set()
    for e in eps:
        missing = ENDPOINT_KEYS - set(e)
        ok("endpoint tem chaves obrigatorias", not missing, f"{e.get('id')}: {missing}")
        ok("endpoint id unico", e.get("id") not in ids, f"duplicado {e.get('id')}")
        ids.add(e.get("id"))
        ok("endpoint evidencia valida", e.get("evidence") in EVIDENCE,
           f"{e.get('id')}: {e.get('evidence')}")
        if e.get("implemented"):
            ok("endpoint implementado tem ecra", bool(e.get("screens")), f"{e.get('id')} sem screens")
        ok("endpoint tem owner", bool(e.get("owner")), f"{e.get('id')} sem owner")
    ok("endpoints.json tem eventos", len(data.get("eventos", [])) >= 4, "poucos eventos")
    ok("endpoints.json tem catalogo extraido", "catalogo_extraido" in data, "em falta")
    ok("endpoints.json tem lacunas", "lacunas" in data, "em falta")


def check_captures():
    ok("ux_capture existe", CAP.is_dir(), "em falta")
    ok("capturas da app nova existem", NEW.is_dir(), "em falta")
    if CAP.is_dir():
        leaked = list(CAP.glob("newapp_*"))
        ok("ux_capture sem capturas da app nova", not leaked, f"{len(leaked)} ficheiros")
        ok("ux_capture tem PNG", len(list(CAP.glob("*.png"))) >= 100,
           f"{len(list(CAP.glob('*.png')))} PNG")
    if NEW.is_dir():
        bad = list(NEW.rglob("*.png"))
        ok("capturas da app nova marcadas", all("cmp_" in p.name or p.parent.name.startswith("lote") or p.name[:2].isdigit()
                                               for p in bad), "nomes fora da convencao")


def check_secrets():
    for name in REQUIRED:
        text = read(name)
        for pat in SECRET_PATTERNS:
            m = pat.search(text)
            ok(f"sem segredo em {name}", not m, f"padrao {pat.pattern[:20]}")


def main():
    check_files()
    check_plan()
    check_coverage()
    check_topology()
    check_endpoints()
    check_captures()
    check_closure()
    check_secrets()

    for name, passed, detail in checks:
        if passed:
            print(f"PASS  {name}")
        else:
            print(f"FAIL  {name}" + (f"  ({detail})" if detail else ""))
    print()
    if problems:
        print(f"{len(problems)} problema(s):")
        for p in problems:
            print(f"  - {p}")
        return 1
    print(f"OK — {len(checks)} verificacoes passaram.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
