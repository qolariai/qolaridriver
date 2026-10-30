# Qolari Driver — laboratório de recriação (Driver + Rider + Fleet + backoffice)

Clone de aprendizagem da Uber, com marca e código próprios (**Qolari**). Não se
distribui nem se opera a sério. O que se estuda é UI, UX, comportamento, contrato e
topologia; não se copiam código, assets nem marca.

## Começar por aqui

| Documento | Para quê |
|---|---|
| [`PROMPT_CLONE_MEGA.md`](PROMPT_CLONE_MEGA.md) | programa de trabalho **v4** (fases, portões, evidência, FASE 4.7) |
| [`PROMPT_CLONE_BUILD.md`](PROMPT_CLONE_BUILD.md) | executar **uma fatia vertical** (F-ID/ecrã), com medição e aceitação |
| [`FEATURE_TAXONOMY.md`](FEATURE_TAXONOMY.md) | método do inventário: domínios, F-ID, estados, órfãos |
| [`REA_BINDINGS.md`](REA_BINDINGS.md) | capacidade → ferramenta → artefacto (anexo do MEGA) |
| [`features.md`](features.md) | **inventário FASE 4.7**: 86 features da Driver |
| [`ANDOIRD/USER_LITE/features.md`](ANDOIRD/USER_LITE/features.md) | **inventário FASE 4.7**: 52 features da Rider |
| [`APROVACAO_EXCLUSOES.md`](APROVACAO_EXCLUSOES.md) | aprovação escrita das 8 exclusões (X-01..X-08) |
| [`endpoints.discovered.json`](endpoints.discovered.json) | catálogo **completo** do binário (1 104 endpoints) |
| [`endpoints.contract.json`](endpoints.contract.json) | **subconjunto** implementado (39, com F-ID) |
| [`peer_triggers.md`](peer_triggers.md) | estados que dependem de outro ator (11 triggers) |
| [`tokens.md`](tokens.md) | tokens de design partilhados (cor, tipo, espaço, movimento) |
| [`rea_evidence/`](rea_evidence/INDEX.md) | prova: ledger, verify, cobertura |
| [`plan.md`](plan.md) | declaração inicial: apps, credenciais, modo, cobertura, tolerância |
| [`topology.md`](topology.md) | atores, 1 backend, 1 backoffice, máquina de estados, orquestração |
| [`access_plan.md`](access_plan.md) | decisão de acesso por app/role |
| [`coverage.md`](coverage.md) | 109 ecrãs da Driver: evidência, integridade, estado, gap |
| [`endpoints.json`](endpoints.json) | contrato do ecossistema implementado (39 endpoints + 6 eventos) |
| [`ADAPTACAO_PROMPTS.md`](ADAPTACAO_PROMPTS.md) | o que mudou dos prompts antigos para os novos |
| [`VALIDACAO_MEGA.md`](VALIDACAO_MEGA.md) | relatório de fecho: testes, evidência, tolerância, gaps |
| [`capabilities.md`](capabilities.md) | matriz capacidade → ação → endpoint → teste → estado |
| [`backlog.md`](backlog.md) | gaps priorizados por F-ID; 6 abertos, zero `parcial` |
| [`RELATORIO_FINAL.md`](RELATORIO_FINAL.md) | evidência, tolerância e veredicto final |

## Código

| Pasta | O quê | Estado |
|---|---|---|
| [`ANDOIRD/DRIVER/RECRIACAO/`](ANDOIRD/DRIVER/RECRIACAO/) | app Driver nova (Kotlin, Views + Compose por evidência) | lotes 0–5; 74 testes; validada no Honor |
| [`ANDOIRD/USER_LITE/RECRIACAO/`](ANDOIRD/USER_LITE/RECRIACAO/) | app Rider nova (Kotlin + Views) | 10 testes; `features.md` por fazer |
| [`ANDOIRD/USER_LITE/`](ANDOIRD/USER_LITE/) | captura e contrato da Rider Lite | captura parcial; contrato `designed` |
| [`ANDOIRD/FLEET/`](ANDOIRD/FLEET/) | APK e contrato da Fleet | sem recriação própria; contrato + operação |
| [`BACKEND/`](BACKEND/) | FastAPI + SQLite: 3 apps + consola | 88 testes |
| [`BACKOFFICE/`](BACKOFFICE/) | consola React | operacional, `designed` |

## Estado face ao V4

A **FASE 4.7** está feita nas **duas apps com recriação**:

| App | features | `ok` | `excluído` | `em falta` | `parcial` |
|---|---|---|---|---|---|
| Driver | 86 | 72 | 8 | 6 | 0 |
| Rider | 52 | 44 | 0 | 8 | 0 |
| **Total** | **138** | **116** | **8** | **14** | **0** |

**Cobertura:** 116 / 130 em âmbito = **89,2 %**.

**Falta:** os 14 gaps de plataforma (`backlog.md` §1–§2) e a decisão de âmbito
G-07 sobre as verticais de produto no binário (2 858 strings). Nenhum é ecrã.

## Validar

```powershell
# portões do MEGA (artefactos, inventário FASE 4.7, evidência, topologia, endpoints, segredos)
python tools\spec_check.py

# inventário FASE 4.7 (Driver e Rider)
python tools\gen_features.py
python tools\gen_features_rider.py

# contrato: descoberto (universo) vs implementado (subconjunto)
python tools\split_endpoints.py

# ledger de obrigações, verify e cobertura
python tools\gen_rea_evidence.py

# cobertura a partir das capturas reais
python tools\gen_coverage.py

# backend
cd BACKEND
.\.venv\Scripts\python -m pytest -q tests

# app Driver
cd ..\ANDOIRD\DRIVER\RECRIACAO
$env:JAVA_HOME = "C:\Program Files\Eclipse Adoptium\jdk-21.0.12.101-hotspot"
.\gradlew.bat assembleDebug testDebugUnitTest

# app Rider
cd ..\..\USER_LITE\RECRIACAO
.\gradlew.bat assembleDebug testDebugUnitTest
```

## Regras que não se quebram

- Original intacto; cópias renomeadas são instrumento, não produto.
- `newapp_*` nunca é spec; `repack_suspect` nunca é promovido sem confirmação.
- Um escritor por agregado; o backoffice intervém por transições auditadas.
- Uma app nunca chama outra.
- Nada é publicado no Hetzner sem aprovação.
- O telemóvel é partilhado: confirmar `topResumedActivity` antes de cada toque.
