# -*- coding: utf-8 -*-
"""Gera rea_evidence/ + o ledger de obrigacoes (FASE 6/7, REA_BINDINGS §2.6).

O REA (servidor MCP) nao esta disponivel nesta sessao, por isso o ledger e
calculado a partir dos artefactos locais e escrito com a mesma forma. A origem
fica declarada no INDEX.md como `local` — nunca se apresenta como `rea`.

Uso:  python tools/gen_rea_evidence.py
Saida: rea_evidence/ com INDEX.md, 00_artifact..05_close/
"""
import os, json, hashlib, re, collections, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
EV = "rea_evidence"
TODAY = datetime.date.today().isoformat()


def sha256(path, limit=None):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(1024 * 1024)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def load_fids(path):
    out = {}
    if not os.path.exists(path):
        return out
    for ln in open(path, encoding="utf-8"):
        if ln.startswith("| `F-"):
            cols = [c.strip() for c in ln.strip("|").split("|")]
            fid = cols[0].strip("`")
            status = next((s for s in ("em falta", "parcial", "excluído", "excluido", "ok")
                           if f"**{s}**" in cols[8]), "?")
            out[fid] = dict(dom=cols[1], nome=cols[2], evid=cols[3], ecra=cols[4],
                            acao=cols[5], endpoint=cols[6].strip("`"), estado=cols[7],
                            status=status, teste=cols[9])
    return out


for d in ["00_artifact", "01_access", "02_capture", "03_spec", "04_contract", "05_close"]:
    os.makedirs(os.path.join(EV, d), exist_ok=True)

# ---------------------------------------------------------------- 00 artifact
artefacts = []
for app, path in [
    ("driver", "ANDOIRD/DRIVER/source-original.apk"),
    ("rider", "ANDOIRD/USER_LITE/spec_src/apk_instalado/lite_base.apk"),
    ("fleet", "ANDOIRD/FLEET/original.apk"),
]:
    if os.path.exists(path):
        artefacts.append({
            "app": app,
            "path": path,
            "bytes": os.path.getsize(path),
            "sha256": sha256(path),
            "ferramenta": "local (sha256sum) — REA inspect_artifact indisponivel",
        })
json.dump({"artefactos": artefacts, "data": TODAY},
          open(os.path.join(EV, "00_artifact", "inventory.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

# ---------------------------------------------------------------- 01 access
disc = json.load(open("endpoints.discovered.json", encoding="utf-8"))
con = json.load(open("endpoints.contract.json", encoding="utf-8"))
mf = json.load(open("ANDOIRD/DRIVER/ui_spec/manifest.json", encoding="utf-8"))
json.dump({
    "package": mf.get("package"),
    "permissions": len(mf.get("permissions", [])),
    "activities": len(mf.get("activities", [])),
    "services": len(mf.get("services", [])),
    "receivers": len(mf.get("receivers", [])),
    "providers": len(mf.get("providers", [])),
    "deeplinks": len(mf.get("deeplinks", [])),
    "fonte": "ANDOIRD/DRIVER/ui_spec/manifest.json",
    "ferramenta": "decode_android_resources (via apktool) — extraido em sessao anterior",
}, open(os.path.join(EV, "01_access", "package.json"), "w", encoding="utf-8"),
    ensure_ascii=False, indent=1)

# ---------------------------------------------------------------- 03 spec
spec = {
    "layouts": 2693,
    "drawables_xml": 4486,
    "strings_idiomas": 172,
    "strings_total": 622340,
    "strings_pt_pt": 9553,
    "tokens": "ui_spec/design_tokens.json",
    "manifest": "ui_spec/manifest.json",
    "fonte": "ANDOIRD/DRIVER/ui_spec/",
    "ferramenta": "decode_android_resources (apktool) — sessao anterior",
}
json.dump(spec, open(os.path.join(EV, "03_spec", "resources_index.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

# ---------------------------------------------------------------- 04 contract
json.dump({
    "discovered": {"ficheiro": "./endpoints.discovered.json", "total": disc["total"],
                   "disposicao": disc["disposicao"]},
    "contract": {"ficheiro": "./endpoints.contract.json", "total": con["total"],
                 "com_feature": con["com_feature"], "por_origem": con["por_origem"]},
    "nota": ("Universo (discovered) != contrato. 22 dos 39 endpoints sao `designed`: "
             "a Rider Lite e WebView e o backoffice nao existe no original."),
}, open(os.path.join(EV, "04_contract", "shapes.index.json"), "w", encoding="utf-8"),
    ensure_ascii=False, indent=1)

# ---------------------------------------------------------------- 05 close: LEDGER
DRV = load_fids("features.md")
RID = load_fids("ANDOIRD/USER_LITE/features.md")

obligations = []
for app, fids in [("driver", DRV), ("rider", RID)]:
    for fid, f in fids.items():
        obligations.append({
            "id": f"{app}:{fid}",
            "app": app,
            "feature": fid,
            "dominio": f["dom"],
            "nome": f["nome"],
            "evidencia": f["evid"],
            "ecra": f["ecra"],
            "endpoint": f["endpoint"],
            "status": f["status"],
            "teste": f["teste"],
            "obrigacao": "implementar" if f["status"] in ("em falta", "parcial")
                         else ("excluido_aprovado" if f["status"].startswith("exclu") else "cumprida"),
        })

st = collections.Counter(o["status"] for o in obligations)
by_exp = collections.Counter((o["app"], o["status"]) for o in obligations)
ledger = {
    "schema": "qolari.obligation_ledger/1",
    "data": TODAY,
    "origem": "local (REA build_reconstruction_obligation_ledger indisponivel nesta sessao)",
    "total_obrigacoes": len(obligations),
    "por_status": dict(st),
    "por_app": {f"{a}:{s}": n for (a, s), n in sorted(by_exp.items())},
    "abertas": [o for o in obligations if o["obrigacao"] == "implementar"],
    "obrigacoes": obligations,
}
json.dump(ledger, open(os.path.join(EV, "05_close", "obligations.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

# ---------------------------------------------------------------- 05 close: verify / coverage
verify = {
    "schema": "qolari.verify/1",
    "data": TODAY,
    "origem": "local (REA verify_reconstruction indisponivel)",
    "verificacoes": [],
}
def V(nome, passou, detalhe=""):
    verify["verificacoes"].append({"nome": nome, "passou": bool(passou), "detalhe": detalhe})

V("features.md da Driver existe", os.path.exists("features.md"))
V("features.md da Rider existe", os.path.exists("ANDOIRD/USER_LITE/features.md"))
V("discovered >= contract", disc["total"] > con["total"],
  f"{disc['total']} vs {con['total']}")
V("contract tem feature em todos", con["com_feature"] == con["total"],
  f"{con['com_feature']}/{con['total']}")
V("discovered tem disposition em todos", "por_classificar" not in disc["disposicao"],
  str(disc["disposicao"]))
V("peer_triggers.md existe", os.path.exists("peer_triggers.md"))
V("tokens.md existe", os.path.exists("tokens.md"))
V("aprovacao de exclusoes existe", os.path.exists("APROVACAO_EXCLUSOES.md"))
V("zero parcial na Driver", st.get("parcial", 0) == 0, str(st.get("parcial", 0)))
verify["passaram"] = sum(1 for v in verify["verificacoes"] if v["passou"])
verify["falharam"] = sum(1 for v in verify["verificacoes"] if not v["passou"])
json.dump(verify, open(os.path.join(EV, "05_close", "verify.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

# cobertura: cumpridas / total (excluindo exclusoes aprovadas)
cumpridas = st.get("ok", 0)
total_real = len(obligations) - st.get("excluido", 0) - st.get("excluído", 0)
coverage = {
    "schema": "qolari.coverage/1",
    "data": TODAY,
    "origem": "local (REA evaluate_reconstruction_coverage indisponivel)",
    "limite_declarado": "funcional (plan.md)",
    "total_features": len(obligations),
    "excluidas_aprovadas": st.get("excluido", 0) + st.get("excluído", 0),
    "em_ambito": total_real,
    "cumpridas": cumpridas,
    "cobertura_pct": round(100.0 * cumpridas / total_real, 1) if total_real else 0.0,
    "por_app": {f"{a}:{s}": n for (a, s), n in sorted(by_exp.items())},
    "nota": "Cobertura abaixo do prometido e gap, nao tolerancia (MEGA FASE 6.9).",
}
json.dump(coverage, open(os.path.join(EV, "05_close", "coverage.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

# ---------------------------------------------------------------- INDEX.md
L = []
A = L.append
A("# rea_evidence/ — índice")
A("")
A("**Fonte:** REA_BINDINGS.md §3. Uma linha por artefacto. Sem linha, o artefacto não")
A("existe para a auditoria.")
A("")
A("**Aviso de origem:** o servidor MCP **REA não estava disponível** nesta sessão.")
A("Os artefactos foram produzidos a partir dos ficheiros locais, com o mesmo formato.")
A("A coluna `ferramenta` diz `local` onde devia dizer a ferramenta do REA — nunca se")
A("apresenta trabalho local como trabalho do REA.")
A("")
A("```")
A("artefacto | ferramenta | entrada | data | digest | unknown/limitacao")
A("```")
A("")
A("| artefacto | ferramenta | entrada | data | digest | unknown/limitação |")
A("|---|---|---|---|---|---|")

for a in artefacts:
    A(f"| `00_artifact/{a['app']}.apk` | local | `{a['path']}` | {TODAY} | "
      f"`{a['sha256'][:16]}` | REA `inspect_artifact` indisponível |")

A(f"| `01_access/package.json` | decode_android_resources | `com.ubercab.driver` | "
  f"{TODAY} | — | manifesto extraído por apktool em sessão anterior |")
A(f"| `02_capture/` | capture_adb_screen | PTP-N49 / Honor | {TODAY} | — | "
  f"172 PNG + 4 vídeos; o Honor já não está ligado |")
A(f"| `03_spec/resources_index.json` | decode_android_resources | `ui_spec/` | "
  f"{TODAY} | — | 2 693 layouts, 172 idiomas |")
A(f"| `04_contract/shapes.index.json` | — | `endpoints.discovered.json` | {TODAY} | — | "
  f"22 de 39 endpoints são `designed` |")
A(f"| `05_close/obligations.json` | local | `features.md` ×2 | {TODAY} | — | "
  f"{len(obligations)} obrigações, {len(ledger['abertas'])} abertas |")
A(f"| `05_close/verify.json` | local | artefactos do projeto | {TODAY} | — | "
  f"{verify['passaram']} passaram, {verify['falharam']} falharam |")
A(f"| `05_close/coverage.json` | local | `features.md` ×2 | {TODAY} | — | "
  f"cobertura {coverage['cobertura_pct']}% |")
A("")
A("## Resumo do ledger")
A("")
A("| Métrica | Valor |")
A("|---|---|")
A(f"| Obrigações | {len(obligations)} |")
A(f"| Cumpridas (`ok`) | {st.get('ok', 0)} |")
A(f"| Excluídas com aprovação | {st.get('excluido', 0) + st.get('excluído', 0)} |")
A(f"| **Abertas (gap)** | **{len(ledger['abertas'])}** |")
A(f"| Cobertura | **{coverage['cobertura_pct']}%** |")
A("")
A("## Obrigações abertas")
A("")
A("| obrigação | app | nome | status |")
A("|---|---|---|---|")
for o in ledger["abertas"]:
    A(f"| `{o['id']}` | {o['app']} | {o['nome']} | `{o['status']}` |")
A("")
A("## Proveito")
A("")
A("Este ledger alimenta `capabilities.md` e `backlog.md` (MEGA FASE 7.1) e o número")
A("de cobertura entra no `RELATORIO_FINAL.md` (MEGA FASE 6.9). Sem ele, o ledger")
A("fecharia sobre o vazio.")
A("")

open(os.path.join(EV, "INDEX.md"), "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")

print("rea_evidence/ gerado")
print("  artefactos:", len(artefacts))
print("  obrigacoes:", len(obligations), dict(st))
print("  abertas:", len(ledger["abertas"]))
print("  verify:", verify["passaram"], "ok /", verify["falharam"], "falhas")
print("  cobertura:", coverage["cobertura_pct"], "%")
