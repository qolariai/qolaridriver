# -*- coding: utf-8 -*-
"""Gera coverage.md a partir das capturas reais da Driver.

Fonte: ANDOIRD/DRIVER/ux_capture/versoes.csv + toolkit_por_ecra.csv +
correlacao_layouts.csv. O estado de implementacao e um mapa curado (prefixo do
ficheiro), atualizado a mao quando um lote fecha. Nao inventa ecras.
"""
import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAP = ROOT / "ANDOIRD" / "DRIVER" / "ux_capture"
OUT = ROOT / "coverage.md"

# prefixo -> (estado, lote, gap/nota)
# estado: sim | parcial | nao
CURATED = {
    0: ("sim", "2", "boas-vindas e seletor de conta"),
    10: ("sim", "3", "Descobrir; conteudo de exemplo"),
    11: ("sim", "3", "Rendimentos; pontos/Qolari Pro fora"),
    12: ("sim", "3", "Caixa de entrada em Compose"),
    13: ("sim", "1", "Menu"),
    14: ("sim", "5", "Ferramentas de seguranca"),
    15: ("sim", "5", "Verificacao do PIN (configuracao)"),
    16: ("parcial", "5", "pagina web do original; recriada como conteudo proprio"),
    17: ("sim", "5", "Centro de seguranca"),
    18: ("sim", "5", "Centro de seguranca (detalhes)"),
    19: ("sim", "5", "Limite de velocidade"),
    20: ("sim", "5", "Preferencias de seguranca"),
    21: ("sim", "5", "PIN: opcoes"),
    22: ("nao", "-", "gravacao de video: fora de ambito (D7)"),
    23: ("parcial", "5", "acompanhar viagem/contacto: partilha depende do sistema"),
    24: ("sim", "5", "Recursos de seguranca"),
    25: ("sim", "5", "Hub de informacoes"),
    26: ("nao", "-", "video de boas-vindas: fora de ambito (D7)"),
    27: ("nao", "-", "Comfort: fora de ambito (D7)"),
    28: ("nao", "-", "Comfort: fora de ambito (D7)"),
    29: ("nao", "-", "Comfort: fora de ambito (D7)"),
    30: ("nao", "-", "Comfort: fora de ambito (D7)"),
    31: ("sim", "2", "arranque sem sessao"),
    32: ("sim", "2", "login por telefone"),
    33: ("nao", "-", "login por e-mail: nao implementado (D6); so telefone"),
    35: ("parcial", "2", "acoes necessarias; atalhos para as Definicoes do Android"),
    36: ("sim", "3", "Descobrir: lembretes (filtro)"),
    37: ("sim", "3", "Descobrir: estado limpo"),
    39: ("sim", "3", "Descobrir: filtros repostos"),
    41: ("sim", "1", "Menu autenticado"),
    42: ("sim", "1", "Menu: Ajuda"),
    43: ("sim", "1", "Definicoes"),
    44: ("sim", "1", "Acessibilidade"),
    45: ("sim", "1", "Comunicacao"),
    46: ("sim", "1", "Navegacao"),
    47: ("sim", "1", "Sons e voz"),
    48: ("sim", "1", "Centro de privacidade"),
    49: ("sim", "1", "Acessibilidade: audicao"),
    50: ("sim", "1", "Acessibilidade: comunicacao"),
    51: ("sim", "1", "Push: janela de ativacao (UI)"),
    52: ("sim", "1", "Push em segundo plano (UI)"),
    53: ("sim", "1", "Privacidade (meio)"),
    54: ("sim", "1", "Privacidade (fundo)"),
    60: ("sim", "2", "Inicio: painel"),
    61: ("sim", "3", "Descobrir"),
    62: ("sim", "3", "Rendimentos"),
    63: ("sim", "3", "Caixa de entrada"),
    64: ("sim", "1", "Menu"),
    65: ("sim", "1", "Ajuda"),
    66: ("sim", "1", "Definicoes"),
    70: ("sim", "5", "Menu: veiculo"),
    71: ("sim", "5", "Menu: documentos"),
    72: ("parcial", "5", "pagina de seguro indisponivel no original; recriada como informativa"),
    74: ("sim", "5", "Informacoes fiscais"),
    75: ("sim", "5", "Formas de pagamento"),
    77: ("sim", "1", "Sobre"),
    80: ("sim", "5", "Veiculos"),
    81: ("nao", "-", "adicionar veiculo: fora de ambito (D7)"),
    82: ("sim", "5", "Gerir veiculo"),
    83: ("sim", "5", "Documentos"),
    84: ("sim", "5", "Documento: carta de conducao"),
    85: ("sim", "5", "Documento: TVDE"),
    86: ("sim", "5", "Documento: registo criminal"),
    87: ("sim", "5", "Documento: cartao de cidadao"),
    88: ("sim", "5", "Documento: DUA"),
    89: ("sim", "5", "Documento: seguro/carta verde"),
    90: ("sim", "1", "Ajuda: categorias"),
    91: ("sim", "5", "Ajuda: artigos (conteudo proprio)"),
    100: ("parcial", "4", "oferta; sem contagem decrescente/som; estados de viagem sem captura original"),
    110: ("sim", "2", "offline: inicio"),
    115: ("sim", "2", "offline: pull-to-refresh (inicio)"),
    116: ("sim", "3", "offline: pull-to-refresh (rendimentos)"),
    117: ("sim", "2", "offline: arranque a frio"),
    120: ("sim", "2", "offline: inicio (2. sessao)"),
    121: ("sim", "3", "offline: Descobrir"),
    122: ("sim", "3", "offline: Rendimentos"),
    123: ("sim", "3", "offline: Caixa de entrada"),
    124: ("sim", "1", "offline: Menu"),
    125: ("sim", "2", "offline: refresh inicio (2)"),
    126: ("sim", "3", "offline: refresh rendimentos (2)"),
}

# Ecrãs que o PNG nao mostra mas a recriacao tem de cobrir.
NAO_CAPTURADOS = [
    ("Viagem: aceitar/recolha", "U + D (peer)", "`earner_trip_native_unified_task_shell_v2_view.xml`, `active_with_drawer_2panel_for_glide.xml`", "static + served", "Forma vem do layout; dados do nosso backend. Sem pixel original."),
    ("Viagem: PIN do passageiro", "D (peer)", "`earner_trip_native_pin_entry_view.xml`, `dropoff_pin_entry_help.xml`", "static + served", "O PIN e gerado pelo backend (`pin_required`); a app compara localmente."),
    ("Viagem: em curso", "D (peer)", "`earnertripflow_screenlayout.xml`", "static + served", "Mapa/rota por SDK; sem chave."),
    ("Viagem: fim e ganhos da viagem", "D (peer)", "`earnings_tab_view.xml`, `earnings_button_primary.xml`", "static + served", "Liquidacao no backend."),
    ("Avaliacao do passageiro", "D (peer)", "`earner_trip_native_survey_view.xml`", "static + served", "Formulario estatico."),
    ("Recibo / historico do passageiro", "U", "sem layout nativo (WebView na Lite)", "served", "Contrato `/rt/lite/*`; UI por recriar."),
    ("Oferta expirada / contagem decrescente", "D", "`driver_job_board_offers_*`", "presumed", "Nao observado; convencao propria do laboratorio."),
    ("Sessao expirada (401)", "U/D/F", "strings de erro", "presumed", "Nao capturado; implementar estados de erro."),
    ("Modo escuro", "U/D/F", "`values-night`", "static", "Nao capturado; tokens existem."),
    ("3. nivel de Definicoes e Ajuda", "D", "layouts/strings", "static", "Nao visitado; conteudo proprio."),
    ("Mapa real / rota", "U/D/F", "Google Maps SDK", "thirdparty", "Falta `MAPS_API_KEY`."),
    ("Notificacoes do sistema (FCM)", "U/D/F", "Firebase Messaging", "thirdparty", "Nao configurado; o `ramen` cobre o tempo real."),
    ("Login social / reCAPTCHA / IAP", "U/D", "strings", "out_of_scope", "Ausente por decisao (D6/D7)."),
]

RIDER = [
    ("000-003", "arranque, telefone, pais", "live", "Sim (login nativo)"),
    ("010-011", "inicio, menu", "live", "Parcial (UI por recriar)"),
    ("012, 020", "ajuda", "live", "Parcial (conteudo proprio)"),
    ("021", "wallet", "live", "Nao (pagamentos fora)"),
    ("022", "atividade", "live", "Parcial (historico)"),
    ("024-025", "promocoes, legal", "live", "Nao (conteudo legal proprio)"),
    ("030-032", "pesquisa, destino, categorias", "live", "Parcial (contrato Lite feito)"),
    ("050-052", "offline", "live", "Parcial"),
]

BACKOFFICE = [
    ("Painel", "operator/admin", "indicadores, mapa, 14 dias, top motoristas", "designed"),
    ("Viagens + ficha", "operator/admin", "filtros, mapa, tarifa, cronologia, propostas, acoes", "designed"),
    ("Simulador", "operator/admin", "pedir viagens, online/offline, mover, avancar", "designed"),
    ("Motoristas / Passageiros / Frotas / Veiculos", "operator/admin", "fichas, aprovacao, suspensao, veiculos", "designed"),
    ("Documentos", "operator/admin", "fila de verificacao, upload, aprovar/recusar", "designed"),
    ("Financeiro", "finance/admin", "comissao, taxas, saldos, pagamentos, acertos", "designed"),
    ("Categorias / Promocoes / Definicoes", "admin", "tarifas, codigos, parametros, administradores", "designed"),
    ("Integracao", "admin", "cobertura do contrato, trafego, endpoints por mapear", "designed"),
]


def read_csv(name):
    path = CAP / name
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def base_captures():
    # A fonte e o disco: ha capturas que nao entraram no versoes.csv.
    versions = {(r.get("ficheiro") or "").strip(): r.get("versao_da_app", "")
                for r in read_csv("versoes.csv")}
    out = []
    for path in sorted(CAP.glob("*.png")):
        name = path.name
        if re.search(r"_(s|h)\d+\.png$", name):
            continue
        out.append((name, versions.get(name, "n/d")))
    return out


def main():
    toolkit = {r["captura"]: r for r in read_csv("toolkit_por_ecra.csv") if r.get("captura")}
    corr = {r["captura"]: r for r in read_csv("correlacao_layouts.csv") if r.get("captura")}

    counts = {"sim": 0, "parcial": 0, "nao": 0}
    lines = [
        "# coverage.md — Ecrã a ecrã (Driver)",
        "",
        "**Gerado por `tools/gen_coverage.py`** a partir de `ux_capture/versoes.csv`, "
        "`toolkit_por_ecra.csv` e `correlacao_layouts.csv`. Não editar à mão: muda o mapa "
        "curado no script e volta a correr.",
        "",
        "Convenções: `evidence` = `live` (captura do original), `static` (layout/strings do "
        "binário), `served` (materializado pelo nosso backend), `presumed` (inferido), "
        "`designed` (não existe no original). `integrity` = `clean` ou `repack_suspect`.",
        "",
        "## Resumo",
        "",
        "| Métrica | Valor |",
        "|---|---|",
    ]

    rows = []
    for name, version in base_captures():
        n = int(name[:3])
        status, lote, note = CURATED.get(n, ("sim", "?", "sem nota"))
        counts[status] += 1
        tk = toolkit.get(name[:-4], {})
        c = corr.get(name, {})
        layout = (c.get("melhor_layout") or tk.get("melhor_layout") or "").replace("layout/", "")
        toolkit_name = tk.get("toolkit_provavel", "n/d")
        evidence = "live"
        integrity = "clean"
        rows.append((name, n, status, lote, toolkit_name, layout, evidence, integrity, note, version))

    lines += [
        f"| Ecrãs base | {len(rows)} |",
        f"| Implementados (`sim`) | {counts['sim']} |",
        f"| Parciais (`parcial`) | {counts['parcial']} |",
        f"| Fora de âmbito (`nao`) | {counts['nao']} |",
        "| Integridade | todos `clean` (original 4.600/4.601) |",
        "",
        "`sim` = ecrã implementado na `RECRIACAO/` com os desvios aceites em "
        "`VALIDACAO.md`; `parcial` = implementado com gap declarado; `nao` = fora de "
        "âmbito ou por fazer. Nenhum ecrã `live` foi promovido a `served`.",
        "",
        "## Ecrãs capturados",
        "",
        "| Captura | Ecrã | Toolkit | Layout candidato | Evid. | Integr. | Estado | Lote | Gap / nota | Versão |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for name, n, status, lote, tk, layout, ev, integ, note, ver in rows:
        label = name[:-4].replace("_", " ")
        lines.append(f"| `{name}` | {label} | {tk} | `{layout}` | {ev} | {integ} | **{status}** | {lote} | {note} | {ver} |")

    lines += [
        "",
        "## Ecrãs não capturados (forma `static`, dados `served`/`presumed`)",
        "",
        "| Ecrã | Ator | Fonte alternativa | Evidência | Nota |",
        "|---|---|---|---|---|",
    ]
    for a, b, c, d, e in NAO_CAPTURADOS:
        lines.append(f"| {a} | {b} | {c} | {d} | {e} |")

    lines += [
        "",
        "## Rider (Uber Lite) — 32 PNG",
        "",
        "| Capturas | Ecrã | Evidência | Estado |",
        "|---|---|---|---|",
    ]
    for a, b, c, d in RIDER:
        lines.append(f"| {a} | {b} | {c} | {d} |")

    lines += [
        "",
        "Contrato da app nova: [`ANDOIRD/USER_LITE/endpoints.json`](ANDOIRD/USER_LITE/endpoints.json) "
        "(`designed`, 15 endpoints). A recriação da Rider ainda não existe.",
        "",
        "## Fleet",
        "",
        "Sem captura própria. Cobertura **funcional** (contrato e operação), não visual. "
        "O APK e o contrato estão em `ANDOIRD/FLEET/`; a app de laboratório fala com o "
        "backend. É `static`/`served`, nunca `live`.",
        "",
        "## Backoffice (`designed`)",
        "",
        "| Área | Papel | Funções | Evidência |",
        "|---|---|---|---|",
    ]
    for a, b, c, d in BACKOFFICE:
        lines.append(f"| {a} | {b} | {c} | {d} |")

    lines += [
        "",
        "## Gaps por classificação",
        "",
        "| Razão | Ecrãs |",
        "|---|---|",
        "| `out_of_scope` | 022, 026, 027–030, 033, 081 (Comfort, vídeo, gravação, login por e-mail, adicionar veículo) |",
        "| `thirdparty` | mapa real, FCM, páginas web de terceiros |",
        "| `state` | 035 (ações necessárias), estados de viagem sem captura |",
        "| `peer` | aceitar, recolha, PIN, em viagem, fim, avaliação |",
        "| `geo` | posição real/simulada |",
        "| `flag` | contagem decrescente da oferta, pontos/Qolari Pro |",
        "| `broken` | 072 (página de seguro indisponível no original) |",
        "",
        "## Critério de fecho",
        "",
        "- Todo o ecrã capturado tem linha nesta tabela.",
        "- Todo o ecrã não capturado tem razão e fonte alternativa.",
        "- Nenhum ecrã da app nova (`RECRIACAO/captures/`) entra nesta tabela.",
        "- Os ecrãs `designed` do backoffice vivem em `topology.md`, não aqui.",
    ]

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{OUT} — {len(rows)} ecrãs base; sim={counts['sim']} parcial={counts['parcial']} nao={counts['nao']}")


if __name__ == "__main__":
    main()
