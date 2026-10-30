# Qolari Driver — laboratório de recriação (Driver + Rider + Fleet + backoffice)

Clone de aprendizagem da Uber, com marca e código próprios (**Qolari**). Não se
distribui nem se opera a sério. O que se estuda é UI, UX, comportamento, contrato e
topologia; não se copiam código, assets nem marca.

## Começar por aqui

| Documento | Para quê |
|---|---|
| [`PROMPT_CLONE_MEGA.md`](PROMPT_CLONE_MEGA.md) | programa de trabalho (fases, portões, evidência) |
| [`PROMPT_CLONE_BUILD.md`](PROMPT_CLONE_BUILD.md) | executar **um** ecrã, com medição e aceitação |
| [`plan.md`](plan.md) | declaração inicial: apps, credenciais, modo, cobertura, tolerância |
| [`topology.md`](topology.md) | atores, 1 backend, 1 backoffice, máquina de estados, orquestração |
| [`access_plan.md`](access_plan.md) | decisão de acesso por app/role |
| [`coverage.md`](coverage.md) | 109 ecrãs da Driver: evidência, integridade, estado, gap |
| [`endpoints.json`](endpoints.json) | contrato do ecossistema implementado (39 endpoints + 6 eventos) |
| [`ADAPTACAO_PROMPTS.md`](ADAPTACAO_PROMPTS.md) | o que mudou dos prompts antigos para os novos |
| [`VALIDACAO_MEGA.md`](VALIDACAO_MEGA.md) | relatório de fecho: testes, evidência, tolerância, gaps |
| [`capabilities.md`](capabilities.md) | matriz capacidade → ação → endpoint → teste → estado |
| [`backlog.md`](backlog.md) | gaps priorizados; zero abertos para o alvo |
| [`RELATORIO_FINAL.md`](RELATORIO_FINAL.md) | evidência, tolerância e veredicto final |

## Código

| Pasta | O quê | Estado |
|---|---|---|
| [`ANDOIRD/DRIVER/RECRIACAO/`](ANDOIRD/DRIVER/RECRIACAO/) | app Driver nova (Kotlin, Views + Compose por evidência) | lotes 0–5; 74 testes; validada no Honor |
| [`ANDOIRD/USER_LITE/RECRIACAO/`](ANDOIRD/USER_LITE/RECRIACAO/) | app Rider nova (Kotlin + Views) | 10 testes; build, login e viagem |
| [`ANDOIRD/USER_LITE/`](ANDOIRD/USER_LITE/) | captura e contrato da Rider Lite | captura parcial; contrato `designed` |
| [`ANDOIRD/FLEET/`](ANDOIRD/FLEET/) | APK e contrato da Fleet | sem recriação própria; contrato + operação |
| [`BACKEND/`](BACKEND/) | FastAPI + SQLite: 3 apps + consola | 55 testes |
| [`BACKOFFICE/`](BACKOFFICE/) | consola React | operacional, `designed` |

## Validar

```powershell
# portões do MEGA (artefactos, evidência, topologia, endpoints, segredos)
python tools\spec_check.py

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
