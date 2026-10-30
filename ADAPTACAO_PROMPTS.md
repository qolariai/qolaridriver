# Adaptação aos novos prompts — o que mudou e onde estamos

**Data:** 2026-10-25 · **Prompts de origem:** `PROMPT_CLONE_MEGA.md` e
`PROMPT_CLONE_BUILD.md` (em `..\COMPARAÇOES DE PROMPT\*.bak`).
**Prompts adaptados:** [`PROMPT_CLONE_MEGA.md`](PROMPT_CLONE_MEGA.md) e
[`PROMPT_CLONE_BUILD.md`](PROMPT_CLONE_BUILD.md), na raiz.

O trabalho antigo seguia o `PROMPT_SPEC_UIUX.md` (fases P0–P8, um ecrã por lote). O
trabalho novo mantém a spec e a recriação, mas acrescenta **evidência/integridade**,
**topologia**, **orquestração entre apps**, **backoffice `designed`** e **cobertura
fechada**. Não é um recomeço: é a mesma matéria com portões mais exigentes.

## 1. O que já estava conforme

| Requisito novo | Onde já existia | Estado |
|---|---|---|
| Artefacto original intacto + hash | `ANDOIRD/DRIVER/source-original.apk` | ✅ hash em `plan.md` |
| Captura viva (pré-auth + autenticada) | 172 PNG, 4 vídeos, dumps | ✅ `ux_capture/` |
| Spec estática (layouts, values, drawables, anim) | `ui_spec/` (2.673 layouts) | ✅ |
| Stack da original respeitada | `stack.md`, `STACK_DECISAO.md` | ✅ Views + Compose por evidência |
| Contrato extraído | `ANDOIRD/DRIVER/endpoints.json` (1.104) | ✅ |
| Recriação limpa | `ANDOIRD/DRIVER/RECRIACAO/` | ✅ lotes 0–5 |
| Backend + backoffice | `BACKEND/`, `BACKOFFICE/` | ✅ operacionais |
| Testes | backend 54, app 74 | ✅ |

## 2. O que faltava (e foi criado)

| Artefacto | Conteúdo | Fonte |
|---|---|---|
| [`plan.md`](plan.md) | declaração inicial: apps, versões, roles, tipo, topologia preliminar, credenciais, gates, modo por role, cobertura, tolerância | MEGA §0 |
| [`access_plan.md`](access_plan.md) | decisão por app/role, escada N0–N5, gates, terceiros, integridade, riscos | MEGA §3 |
| [`coverage.md`](coverage.md) | 109 ecrãs base: evidência, integridade, estado, lote, gap, versão; não capturados; Rider; Fleet; backoffice | gerado por `tools/gen_coverage.py` |
| [`topology.md`](topology.md) | classificação, atores, 1 backend, 1 backoffice, modelo de dados, tempo real, máquina de estados, um escritor por campo, intervenções auditadas, três espelhos | MEGA §4.5/§4.6 |
| [`endpoints.json`](endpoints.json) | 35 endpoints curados + 6 eventos, com owner/producer/consumers/screens/evidence; catálogo extraído referenciado | backend + contratos |
| [`tools/gen_coverage.py`](tools/gen_coverage.py) | regenera a cobertura a partir das capturas reais | — |
| [`tools/spec_check.py`](tools/spec_check.py) | valida os portões (artefactos, evidência, topologia, endpoints, segredos) | — |
| [`device_apk/README.md`](device_apk/README.md) | ponteiro para os originais + hashes (sem duplicar 400 MB) | MEGA FASE 0 |
| [`ux_reference/README.md`](ux_reference/README.md) | referências públicas (vazia por opção; regras `unverified`) | MEGA FASE 2 |
| [`ANDOIRD/USER_LITE/endpoints.json`](ANDOIRD/USER_LITE/endpoints.json) | contrato `designed` da Rider Lite (15 endpoints) | `userlite.py` |
| [`BACKEND/tests/test_espelhos.py`](BACKEND/tests/test_espelhos.py) | teste dos três espelhos (U→D/F/B→U) | MEGA §4.6.7 |

## 3. Correções feitas no código

1. **Propagação de estado para a Fleet.** O evento `driver_trip` só era emitido no
   aceite; passou a ser emitido em **todas** as transições (`_notify`), e o
   `driver_status: online` é emitido quando o motorista fica livre (`_free_driver`).
   Fecha a lacuna de orquestração da FASE 4.6.
2. **Teste dos três espelhos** acrescentado e a passar: cria em U, vê em D/F/B, move em
   D, vê em U, intervém em B, vê em U/D/F e confirma a auditoria.
3. **Isolamento dos testes.** `test_driver_arrives_by_position` deixava uma viagem
   ativa no Bruno; o teste do Lite falhava por ordem de execução. Passou a cancelar a
   viagem no fim. O teste de promoção do Lite deixou de depender do estado da Ana.
   Resultado: **54 testes a passar** (eram 48; entraram 5 do Lite + 1 dos espelhos).

## 4. O que os novos prompts mudam na prática

- **Não se cola o projeto todo no agente.** Um ecrã por prompt, com PNG + layout +
  secção do `ux_behavior.md` + DTO.
- **Cada ecrã declara evidência e integridade** antes de medir. `newapp_*` nunca é spec.
- **O fecho não é "zero ecrãs por visitar"**, é "todos classificados". Um ecrã `unverified`
  não é vergonha; um `unverified` apresentado como certo é.
- **A topologia é nossa**, não espelho da Uber. 1 backend modular, 1 backoffice com
  quatro áreas e RBAC.
- **Um escritor por campo.** `domain/trips.py` é o único que muda viagens; o backoffice
  chama as mesmas funções, com auditoria.
- **Backoffice é `designed`**, não clone. A fidelidade mede-se pela cobertura da máquina
  de estados, não por pixels.
- **O teste dos três espelhos** é o critério de aceitação da orquestração.

## 5. Estado atual por fase

| Fase | Estado | Nota |
|---|---|---|
| 0 Artefacto | ✅ | hash e decoded |
| 1 Acesso | ✅ | `access_plan.md` |
| 2 Captura | ✅ Driver; 🔶 Rider; ❌ Fleet | `coverage.md` classifica |
| 3 Stática | ✅ Driver | `ui_spec/` |
| 4 Contrato | ✅ | catálogo + `endpoints.json` |
| 4.5 Topologia | ✅ | `topology.md` |
| 4.6 Orquestração | ✅ | teste dos espelhos |
| 5 Recriação | ✅ Driver e Rider; ◻ Fleet (contrato/operação) | Driver lotes 0–5; Rider 10 testes |
| 6 Validação | ✅ | Driver e Rider validadas no Honor; 55 testes backend |

## 6. O que continua (por ordem)

1. **Rider (Lite)**: recriação feita em `ANDOIRD/USER_LITE/RECRIACAO/` (Kotlin +
   Views, 10 testes; build, login, viagem e conta). O contrato `designed` está em
   `BACKEND/apps/userlite.py` e `ANDOIRD/USER_LITE/endpoints.json`.
2. **Fleet**: sem recriação própria; o contrato e a operação estão cobertos pelo
   backend e pelo backoffice. A app usada no laboratório é a APK re-branded
   (instrumento, não entregável). Paridade visual declarada como não mensurável.
3. **Driver**: os `parcial` de `coverage.md` que dependem de decisão (mapa real,
   FCM, vídeo, Comfort) ficam assumidos no relatório final; o resto está fechado.
4. **Backoffice**: separar financeiro de suporte num deploy próprio se o projeto sair do
   laboratório; hoje é RBAC + auditoria no mesmo SPA.
5. **Publicação**: os handlers novos e as tabelas continuam por publicar no
   Hetzner; nada é publicado sem aprovação.
6. **iOS**: fora do âmbito; as IPAs existem como laboratório.
7. **Telemóvel Honor**: validação feita em 27/10 (login, oferta, PIN, fim,
   avaliação dos dois lados, offline) e registada em `VALIDACAO_MEGA.md`.

## 7. Como usar os prompts adaptados

```
1. Abre PROMPT_CLONE_MEGA.md e confirma a fase e o portão.
2. Escolhe UM ecrã de coverage.md (estado parcial ou novo).
3. Cola PROMPT_CLONE_BUILD.md, substituindo <ECRÃ>, <STACK_UI>, <FICHEIRO_DESTINO>.
4. Anexa o PNG de ux_capture/, o layout de ui_spec/ e a secção do ux_behavior.md.
5. No fim: build, testes, captura newapp_* e atualização de coverage.md.
6. Corre `python tools/spec_check.py` antes de dizer que está pronto.
```

## 8. Nota sobre trabalho concorrente

O backend ganhou, em paralelo, o contrato da **Rider Lite** (`BACKEND/apps/userlite.py`,
`BACKEND/tests/test_userlite.py`). Foi integrado como `designed` no `endpoints.json` e
na `coverage.md`; não foi tratado como clone do protocolo da Uber. Se houver mais
trabalho concorrente, a regra é a mesma: declarar a evidência e não promover níveis.

## 9. Comandos úteis

```powershell
# Backend
cd BACKEND; .\.venv\Scripts\python -m pytest -q tests

# Portões do MEGA
python tools\spec_check.py

# Cobertura (depois de novas capturas)
python tools\gen_coverage.py

# App Driver
cd ANDOIRD\DRIVER\RECRIACAO
$env:JAVA_HOME = "C:\Program Files\Eclipse Adoptium\jdk-21.0.12.101-hotspot"
.\gradlew.bat assembleDebug testDebugUnitTest
```
