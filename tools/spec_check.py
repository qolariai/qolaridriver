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
    "endpoints.discovered.json",
    "endpoints.contract.json",
    "PROMPT_CLONE_MEGA.md",
    "PROMPT_CLONE_BUILD.md",
    "FEATURE_TAXONOMY.md",
    "REA_BINDINGS.md",
    "peer_triggers.md",
    "tokens.md",
    "ux_reference/README.md",
    "device_apk/README.md",
    "ADAPTACAO_PROMPTS.md",
    "VALIDACAO_MEGA.md",
    "capabilities.md",
    "backlog.md",
    "RELATORIO_FINAL.md",
    "features.md",
    "APROVACAO_EXCLUSOES.md",
    "ANDOIRD/USER_LITE/features.md",
    "rea_evidence/INDEX.md",
    "rea_evidence/05_close/obligations.json",
]

FEATURE_STATUS = {"ok", "parcial", "em falta", "excluído", "excluido"}

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
    report = read("RELATORIO_FINAL.md")
    caps = read("capabilities.md")

    # O veredicto tem de estar coerente com os gaps abertos, nao apenas presente.
    caps_features = read("features.md")
    open_gaps = len(re.findall(r"\*\*aberto\*\*", backlog))
    ok("backlog.md indexa por F-ID", "F-ID" in backlog, "sem ligacao ao inventario")
    ok("backlog.md tem contagem de gaps", "gaps abertos" in backlog.lower() or "**aberto**" in backlog,
       "contagem ausente")
    ok("backlog.md tem os gaps abertos contados", str(open_gaps) in backlog,
       f"{open_gaps} linhas 'aberto' mas a contagem nao bate")

    ok("RELATORIO_FINAL.md tem veredicto", "Veredicto" in report,
       "veredicto ausente")
    ok("capabilities.md tem matriz", "| Status |" in caps and "| ok |" in caps,
       "matriz ausente")
    ok("capabilities.md cita o inventario", "features.md" in caps,
       "sem ligacao a FASE 4.7")

    # Nao se afirma 'zero gaps' com gaps abertos: seria fecho falso.
    afirma_zero = bool(re.search(r"(?i)zero\s+`?gap`?", caps)) or "Nenhum para `funcional`" in backlog
    if open_gaps:
        ok("nao declara zero gaps com gaps abertos", not afirma_zero,
           f"{open_gaps} gaps abertos mas o texto afirma zero")
    else:
        ok("fecho declara zero gaps", afirma_zero, "gaps fechados mas sem declaracao")

    # features.md tem de existir e ter linhas com F-ID
    feats = [ln for ln in caps_features.splitlines()
             if ln.startswith("| `F-") and ln.count("|") >= 10]
    ok("features.md tem linhas com F-ID", len(feats) >= 50, f"{len(feats)} linhas")


def check_features():
    """FASE 4.7 — o gate do inventario."""
    text = read("features.md")
    rows = [ln for ln in text.splitlines() if ln.startswith("| `F-")]
    ok("features.md tem inventario", len(rows) >= 50, f"{len(rows)} features")

    seen = set()
    statuses = {}
    for ln in rows:
        cols = [c.strip() for c in ln.strip("|").split("|")]
        if len(cols) < 10:
            ok("features.md linha completa", False, ln[:80])
            continue
        fid = cols[0].strip("`")
        ok("features.md F-ID unico", fid not in seen, f"duplicado {fid}")
        seen.add(fid)

        status_cell = cols[8]
        found = [s for s in ("em falta", "parcial", "excluído", "excluido", "ok")
                 if f"**{s}**" in status_cell]
        ok("features.md status valido", len(found) == 1,
           f"{fid}: {status_cell[:40]}")
        if found:
            statuses[fid] = found[0]

        ok("features.md tem evidencia", cols[3] not in ("", "?", "—") or cols[4] == "—",
           f"{fid}: sem evidencia")

    # Feature 'ok' sem teste e 'parcial' disfarcado (taxonomia, anti-padroes)
    for ln in rows:
        cols = [c.strip() for c in ln.strip("|").split("|")]
        if len(cols) < 10:
            continue
        fid = cols[0].strip("`")
        if statuses.get(fid) == "ok":
            ok("feature ok tem teste", cols[9] not in ("", "—", "?", "-"),
               f"{fid}: ok sem teste")

    # Excluido exige aprovacao escrita
    excl = [f for f, s in statuses.items() if s in ("excluído", "excluido")]
    if excl:
        ap = read("APROVACAO_EXCLUSOES.md")
        ok("exclusoes tem aprovacao escrita", len(re.findall(r"X-\d\d", ap)) >= len(excl),
           f"{len(excl)} exclusoes, {len(re.findall(r'X-\d\d', ap))} aprovacoes")

    # Nenhuma captura pode ficar sem linha (F-ID ou exclusao aprovada)
    if CAP.is_dir():
        caps = {f[:-4] for f in __import__("os").listdir(CAP)
                if f.endswith(".png") and not re.search(r"_(s|h)\d+\.png$", f)}
        citadas = set(re.findall(r"`(\d{3}_[a-z0-9_]+)\.png`", text))
        citadas |= set(re.findall(r"`(\d{3}_[a-z0-9_]+)`", text))
        orfas = sorted(c for c in caps if c not in citadas)
        ok("features.md cobre todas as capturas", not orfas,
           f"{len(orfas)} sem linha, ex.: {orfas[:3]}")

    ok("features.md declara zero orfaos de string", "orfa" in text or "atribuida" in text,
       "sem classificacao de strings")
    ok("features.md declara o gate", "Gate da FASE 4.7" in text, "gate ausente")


def check_features_rider():
    """FASE 4.7 — o gate do inventario da Rider."""
    path = ROOT / "ANDOIRD" / "USER_LITE" / "features.md"
    ok("Rider tem features.md", path.is_file(), "FASE 4.7 da Rider em falta")
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    rows = [ln for ln in text.splitlines() if ln.startswith("| `F-")]
    ok("Rider features.md tem inventario", len(rows) >= 20, f"{len(rows)} features")

    seen = set()
    for ln in rows:
        cols = [c.strip() for c in ln.strip("|").split("|")]
        if len(cols) < 10:
            ok("Rider features.md linha completa", False, ln[:80])
            continue
        fid = cols[0].strip("`")
        ok("Rider features.md F-ID unico", fid not in seen, f"duplicado {fid}")
        seen.add(fid)
        found = [s for s in ("em falta", "parcial", "excluído", "excluido", "ok")
                 if f"**{s}**" in cols[8]]
        ok("Rider features.md status valido", len(found) == 1,
           f"{fid}: {cols[8][:40]}")

    # Todas as capturas da Rider precisam de linha
    rcap = ROOT / "ANDOIRD" / "USER_LITE" / "ux_capture"
    if rcap.is_dir():
        caps = {f[:-4] for f in __import__("os").listdir(rcap)
                if f.endswith(".png") and not re.search(r"_(s|h)\d+\.png$", f)}
        citadas = set(re.findall(r"`(\d{3}_[a-z0-9_]+)`", text))
        orfas = sorted(c for c in caps if c not in citadas)
        ok("Rider features.md cobre todas as capturas", not orfas,
           f"{len(orfas)} sem linha, ex.: {orfas[:3]}")

    ok("Rider features.md declara a diferenca WebView", "WebView" in text,
       "nota de evidencia ausente")
    ok("Rider features.md declara o gate", "Gate da FASE 4.7" in text, "gate ausente")


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


def check_endpoints_split():
    """FASE 4 — dois ficheiros: universo (discovered) e contrato (implementado)."""
    disc = json.loads(read("endpoints.discovered.json"))
    con = json.loads(read("endpoints.contract.json"))

    ok("discovered > contract", disc["total"] > con["total"],
       f"{disc['total']} vs {con['total']}")
    ok("discovered tem disposition em todos",
       "por_classificar" not in disc.get("disposicao", {}),
       str(disc.get("disposicao")))
    ok("discovered sem disposicao invalida",
       all(e.get("disposition") in ("contract", "substituir", "descartar", "telemetry")
           for e in disc["endpoints"]), "disposicao invalida")

    ok("contract tem feature em todos", con["com_feature"] == con["total"],
       f"{con['com_feature']}/{con['total']}")
    ok("contract declara origem por endpoint",
       all(e.get("origin") in ("extracted", "designed") for e in con["endpoints"]),
       "endpoint sem origin")
    ok("contract declara a separacao", "designed" in con.get("nota", ""),
       "nota ausente")


def check_rea_evidence():
    """FASE 6/7 — ledger, verify e cobertura."""
    idx = read("rea_evidence/INDEX.md")
    ok("rea_evidence tem aviso de origem", "REA não estava disponível" in idx
       or "REA nao estava disponivel" in idx, "origem nao declarada")

    led = json.loads(read("rea_evidence/05_close/obligations.json"))
    ok("ledger tem obrigacoes", led["total_obrigacoes"] >= 50,
       f"{led['total_obrigacoes']}")
    ok("ledger tem abertas declaradas", "abertas" in led, "sem lista de abertas")
    ok("ledger liga a features.md", all("feature" in o for o in led["obrigacoes"]),
       "obrigacao sem F-ID")

    ver = json.loads(read("rea_evidence/05_close/verify.json"))
    ok("verify sem falhas", ver["falharam"] == 0, f"{ver['falharam']} falharam")
    ok("verify tem verificacoes", len(ver["verificacoes"]) >= 5,
       f"{len(ver['verificacoes'])}")

    cov = json.loads(read("rea_evidence/05_close/coverage.json"))
    ok("coverage tem percentagem", "cobertura_pct" in cov, "sem numero")
    ok("coverage declara o limite", bool(cov.get("limite_declarado")), "limite ausente")


def check_peer_tokens():
    text = read("peer_triggers.md")
    rows = [ln for ln in text.splitlines() if ln.startswith("| P-")]
    ok("peer_triggers tem triggers", len(rows) >= 8, f"{len(rows)}")
    ok("peer_triggers liga a F-ID",
       all(re.search(r"F-[a-z0-9]+-\d\d", ln) for ln in rows), "linha sem F-ID")
    ok("peer_triggers tem ator",
       all("Driver" in ln or "Rider" in ln or "sistema" in ln or "backoffice" in ln
           for ln in rows), "linha sem ator")

    tok = read("tokens.md")
    ok("tokens tem cores", "#" in tok, "sem hex")
    ok("tokens tem tipografia", "sp" in tok, "sem tamanhos")
    ok("tokens regista divergencias", "Divergências registadas" in tok
       or "Divergencias registadas" in tok, "sem registo de divergencia")
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
    check_endpoints_split()
    check_features()
    check_features_rider()
    check_peer_tokens()
    check_rea_evidence()
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
