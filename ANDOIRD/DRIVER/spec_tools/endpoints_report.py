# -*- coding: utf-8 -*-
"""Gera ENDPOINTS.md (resumo legivel) a partir de endpoints.json. Os numeros saem sempre do JSON.

Uso: python endpoints_report.py --json endpoints.json --out ENDPOINTS.md
"""
import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    d = json.loads(a.json.read_text(encoding="utf-8"))
    eps, hosts = d["endpoints"], d["hosts"]
    ch, ce = Counter(h["classe"] for h in hosts), Counter(e["classe"] for e in eps)
    cp = Counter(e["prioridade"] for e in eps if e["classe"] == "rebuild")
    cv = Counter(e["http"] for e in eps)
    co = Counter(e["origem"] for e in eps)
    impl = [e for e in eps if e["backend_handler"]]
    L = [f"# ENDPOINTS.md — contrato de rede da {d['app'].capitalize()} {d['versao_referencia']}", "",
         "Gerado por `spec_tools/endpoints_report.py` a partir de `endpoints.json`. **Não editar à mão.**", "",
         d["nota"], "",
         "## Resumo", "",
         f"- **Hosts:** {len(hosts)}. rebuild {ch['rebuild']}, substituir {ch['substituir']}, descartar {ch['descartar']}. "
         f"Sem classificação: {sum(1 for h in hosts if h['regra'] == '(omissao)')}.",
         f"- **Endpoints:** {len(eps)}. rebuild {ce['rebuild']}, substituir {ce['substituir']}, descartar {ce['descartar']}.",
         f"- **Prioridade dos `rebuild`:** essencial {cp['essencial']}, secundário {cp['secundario']}, por avaliar {cp['por avaliar']}, "
         f"fora de âmbito {cp['fora de ambito (produto nao usado pela Driver capturada)']}.",
         f"- **Já implementados no backend do laboratório:** {len(impl)}. Com chamadas no tráfego registado: {sum(1 for e in eps if e['chamadas_registadas'])}.",
         f"- **Por verbo:** " + ", ".join(f"{k} {v}" for k, v in cv.most_common()) + ".",
         f"- **Por origem:** " + "; ".join(f"{k}: {v}" for k, v in co.most_common()) + ".",
         f"- **Resposta com DTO já mapeado em `BACKEND/contracts`:** {sum(e['resposta_mapeada_no_backend'] for e in eps)} de {sum(1 for e in eps if e['resposta'])}.",
         "",
         "**Classes:** `rebuild` (o nosso backend implementa), `substituir` (equivalente próprio), `descartar` (não se reconstrói).",
         "**Prioridade:** essencial = já implementado ou chamado no tráfego; secundário = ligado a um ecrã capturado pelo nome; "
         "por avaliar = sem ecrã identificado; fora de âmbito = produto que a Driver capturada não usa.", "",
         "## Hosts", "", "| Host | Classe | Papel | Motivo |", "|---|---|---|---|"]
    for h in sorted(hosts, key=lambda h: (h["classe"], h["host"])):
        L.append(f"| `{h['host']}` | {h['classe']} | {h['papel']} | {h['motivo']} |")
    L += ["", f"Falsos positivos da extração (não são hosts): {len(d.get('falsos_positivos_extracao', []))}.", "",
          "## Endpoints essenciais (o mínimo para os ecrãs capturados)", "",
          "| Verbo | Path | Ecrãs | Handler no backend |", "|---|---|---|---|"]
    for e in sorted((e for e in eps if e["prioridade"] == "essencial"), key=lambda e: e["path"]):
        L.append(f"| {e['http']} | `{e['path']}` | {'; '.join(e['screens'])} | {e['backend_handler'] or '—'} |")
    by_scr = defaultdict(int)
    for e in eps:
        for s in e["screens"] or ["(sem ecrã identificado)"]:
            by_scr[s] += 1
    L += ["", "## Endpoints por ecrã (todas as classes)", "", "| Ecrã | Endpoints |", "|---|---|"]
    for s, n in sorted(by_scr.items(), key=lambda kv: -kv[1]):
        L.append(f"| {s} | {n} |")
    L += ["", "Confiança da ligação a ecrãs: " + "; ".join(f"{k}: {v}" for k, v in Counter(e["screens_confianca"] for e in eps).most_common()) + ".", ""]
    au = d["auth"]
    L += ["## Autenticação", "",
          "- Sinais no smali: " + ", ".join(f"`{x}`" for x in au["sinais_no_smali"][:15]) + ".",
          "- Rotas já implementadas no backend: " + ", ".join(f"`{x}`" for x in au["rotas_no_backend"]) + ".",
          "- Esquema validado no laboratório (`TESTE/ui_spec_android/contract_main_flow.md`): OAuth2 com `grant_type` password e refresh, e o token vai no header `x-uber-token` (ou `Authorization: Bearer`). Login social (Google) e conta por e-mail aparecem nos ecrãs 032 e 033.", ""]
    rt = d["realtime_e_push"]
    L += ["## Tempo real e push", "",
          "- Push: " + ", ".join(f"`{x}`" for x in rt["push_fcm"]) + " → `substituir` (projeto Firebase próprio).",
          "- Canal em tempo real: " + ", ".join(f"`{x}`" for x in rt["canal_tempo_real"][:10]) + " → `rebuild`.", ""]
    L += ["## Uploads", "", f"{len(d['uploads'])} sinais (multipart e paths com upload), por exemplo: " + ", ".join(f"`{x}`" for x in d["uploads"][:8]) + ".", ""]
    L += ["## Configuração remota", "", ", ".join(f"`{x}`" for x in d["config_remota"]) + ".", ""]
    rm = d["persistencia_local_room"]
    L += ["## Persistência local (Room)", "",
          f"- Bases de dados: {len(rm['bases_de_dados'])} ({', '.join(rm['bases_de_dados'])}). Tabelas: {len(rm['tabelas'])}.",
          ("- **Só existe a base interna do WorkManager (biblioteca de tarefas em segundo plano). A app não tem esquema Room próprio, por isso não há modelo de dados local a replicar.**"
           if rm['bases_de_dados'] and all(b.startswith('androidx.work') for b in rm['bases_de_dados']) else "- Tabelas da app:"),
          *[f"  - `{t}`: {v['colunas'][:160]}" for t, v in list(rm["tabelas"].items())[:25]], ""]
    ts = d.get("trafego_servidor")
    if ts:
        L += ["## Tráfego real no servidor (agregado)", "",
              f"- Fonte: {ts['fonte']}. {ts['linhas_de_pedido']} pedidos em {len(ts['ficheiros'])} ficheiros de log.",
              f"- **{ts['paths_da_app']} caminhos da app** ({ts['chamadas_da_app']} chamadas), todos dentro do contrato: {len(ts['paths_da_app_fora_do_contrato'])} fora dele.",
              f"- Ruído de rastreadores da internet ignorado: {ts['paths_de_ruido_ignorados']} caminhos ({ts['chamadas_de_ruido_ignoradas']} chamadas) — `robots.txt`, `.env`, `.git/config` e afins.",
              f"- {ts['promovidos_a_essencial']} endpoints `rebuild` foram promovidos a **essencial** por aparecerem em tráfego real.",
              f"- {ts['nota']}", ""]
        lac = d.get("lacunas_backend", [])
        L += [f"## Lacunas do backend: a app chama e o servidor não tem handler ({len(lac)})", "",
              "Só `rebuild`. Ordenadas por número de chamadas.", "", "| Chamadas | Verbo | Path | Ecrã provável |", "|---|---|---|---|"]
        for l in lac:
            L.append(f"| {l['chamadas']} | {l['http']} | `{l['path']}` | {(l['screens'] or ['—'])[0]} |")
        fl = d.get("fluxo_viagem_observado_no_laboratorio", [])
        L += ["", "## Fluxo de viagem observado no laboratório (15-10, UTC)", "",
              "Ordem real dos pedidos na viagem completa feita com a app renomeada contra o nosso backend. A chegada e o PIN não geram pedido próprio (a chegada é automática por posição).", "",
              "| Hora | Verbo | Path | Handler |", "|---|---|---|---|"]
        for f in fl:
            L.append(f"| {f['hora_utc']} | {f['http']} | `{f['path']}` | {f['handler']} |")
        L += [""]
    L += ["## Limites", "",
          "- A ligação endpoint → ecrã é inferida pelo nome do path, exceto nos endpoints já implementados e validados no laboratório.",
          "- O tráfego vem dos logs do servidor e do backend local, agregados (sem corpos de pedidos). É tráfego da app renomeada e da app de teste, e não da Uber.",
          "- As capturas da pasta TESTE são posteriores à viagem do laboratório (a partir das 19:09 locais), por isso **não se consegue ligar ecrãs da viagem a pedidos pela hora**. Essa ligação continua inferida pelo nome.",
          "- Os tipos de resposta saem das assinaturas Retrofit. Os genéricos e os erros podem esconder o DTO real.", ""]
    a.out.write_text("\n".join(L), encoding="utf-8")
    print("->", a.out)


if __name__ == "__main__":
    main()
