# Plano: recriar a app User (passageiro) a partir da **Uber Lite** pelo `PROMPT_SPEC_UIUX.md`

> **Atualização 2026-10-25:** o programa passou a ser o
> [`PROMPT_CLONE_MEGA.md`](PROMPT_CLONE_MEGA.md). A Rider tem agora um contrato
> `designed` em [`ANDOIRD/USER_LITE/endpoints.json`](ANDOIRD/USER_LITE/endpoints.json)
> e no backend (`BACKEND/apps/userlite.py`, 5 testes). O próximo passo é a recriação da
> app, ecrã a ecrã, com o [`PROMPT_CLONE_BUILD.md`](PROMPT_CLONE_BUILD.md). A cobertura
> do ecossistema está em [`coverage.md`](coverage.md).

Mesmo processo que na Driver (`PLANO_SPEC_UIUX_DRIVER.md`), aplicado à app de passageiro. O original **não é modificado**; a recriação é limpa, na mesma stack
(Kotlin, Views com Compose só onde a original é Compose, Navigation, ViewModel/StateFlow, Retrofit), com o nosso backend (Rider, porta 8090).

## Referência escolhida: Uber Lite
A app de referência é a **Uber Lite** (`com.ubercab.uberlite`, versão **1.248.10001**, instalada a 16-10 no PTP-N49), mais leve e simples que a Uber completa. Os APKs instalados foram copiados do telemóvel
(leitura) para `ANDOIRD/USER_LITE/spec_src/apk_instalado/`. A recriação fica em `ANDOIRD/USER_LITE/RECRIACAO/` (pacote próprio, não substitui a `com.qolari.rider`).
Risco a medir na P4: a Lite pode falar uma API diferente da Rider completa (`BACKEND/apps/rider.py` foi feito a partir da 4.650); o `endpoints.json` da Lite diz o que
se reaproveita, o que se estende e o que se descarta. O resto desta página (Uber 4.653 e `com.qolari.rider`) fica como material de comparação.

## O que já existe (reaproveitar)
| Ativo | Onde | Uso |
|---|---|---|
| Backend Rider (27 handlers, testes) | `BACKEND/apps/rider.py`, `BACKEND/tests/` | contrato e dados reais; só se estende o que faltar |
| Contratos extraídos do APK | `BACKEND/contracts/rider_endpoints.json`, `rider_models.json`, `ANDOIRD/USER/backend_spec/` | base do `endpoints.json` da User |
| APK rebrand e splits | `ANDOIRD/USER/final_apks_server/` (`com.qolari.rider`, base Uber 4.650.10003) | laboratório (via do servidor) para ver estados de viagem |
| Pedido de viagem já mapeado | `PROMPT_RIDER_PEDIDO.md` | contrato do pedido, `get-blockers`, estado `active order` |
| Ferramentas e padrões da Driver | `ANDOIRD/DRIVER/spec_tools/`, `RECRIACAO/` (config única, `LoadViewModel`, mapeadores com testes) | copiar a estrutura e a disciplina |
| Original instalado | `com.ubercab.uberlite` 1.248.10001 (referência) e `com.ubercab` 4.653.10004 (comparação) | referência viva |

## Regras (as mesmas da Driver, mais duas)
1. Só leitura na Uber original (a conta é tua): não alterar definições, não aceitar termos, não mexer em pagamentos.
2. **Nunca confirmar um pedido de viagem real** na Uber (gera cobrança e um motorista real). Os ecrãs depois do pedido vêm do laboratório (backend nosso + `com.qolari.rider`), marcados `[inf]` onde não houver original.
3. Login: fazes tu na Uber original (eu não escrevo credenciais). Antes, capturo-a em logout.
4. Cada alteração no telemóvel (rede, definições) avisa-se antes e repõe-se no fim. Verificar a bateria antes (`dumpsys battery`).
5. Nada é publicado no Hetzner sem aprovação.

## Fases, modelo e esforço
| Fase | Conteúdo | Modelo | Esforço |
|---|---|---|---|
| P0 | Baseline: versão, packages, o que já está feito e o que falta | Haiku | low |
| P1 | Captura da Uber original (logout e login, com scroll, offline/erro): pesquisa, destino, categorias, tarifa, "Confirmar recolha" (parar aqui), histórico, conta, pagamentos, ajuda | Sonnet + Haiku (ciclos) | high / low |
| P2 | Extração: decode do APK da Lite 1.248, layouts, tokens, strings, toolkit por ecrã, correlação capturas ↔ layouts | Sonnet + Haiku | medium / low |
| P3 | `ux_behavior.md` da User (grafo, gestos, animações, back, estados) | Sonnet | medium |
| P4 | `endpoints.json` da User (rebuild/substituir/descartar, ecrãs ligados) | Opus | high |
| P5 | App nova em `ANDOIRD/USER/RECRIACAO/` por lotes | Sonnet | high |
| P6 | Lacunas do backend Rider (handlers em falta vistos nos logs e nos lotes) com testes | Sonnet | medium |
| P7 | Validação ecrã a ecrã (`VALIDACAO.md`) | Opus (+ Haiku) | medium / low |
| P8 | Documentação e memória | Haiku | low |

## Lotes previstos da P5 (a confirmar com as capturas)
0. Andaime + login por telefone + sessão + banner sem rede. 1. Início (mapa, "Para onde?", sugestões). 2. Pesquisa de morada, destino no mapa, confirmar ponto de recolha.
3. Categorias, tarifa estimada, código promocional, pagamento. 4. Pedido e estados da viagem (à procura, motorista a caminho, PIN, em viagem, fim, avaliação, recibo). 5. Atividade (histórico), Conta, Pagamentos, Ajuda, Segurança.

## Decisões que preciso de ti
1. **Logout/login na Uber Lite**: queres começar em logout (como na Driver) e eu aviso quando precisares de fazer login?
2. **Telemóvel**: PTP-N49 (como na Driver), com a Uber Lite, a Uber `com.ubercab` e a `com.qolari.rider` já instaladas.
3. **Estados da viagem**: via laboratório (backend nosso, passageiras `+351910000001..3`), como combinado na Driver.
