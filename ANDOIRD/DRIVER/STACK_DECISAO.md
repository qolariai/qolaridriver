# STACK_DECISAO.md — stack da recriação da Driver (P5)

Decisão pedida na P5: com que stack se recria a app, dado o spec (FASE 4: "obrigatoriamente na stack da original ... não trocar XML por Compose porque é mais moderno") e o que já existe na `TESTE/app` (Kotlin + Compose, MVVM). Esta decisão é **reversível ecrã a ecrã** (ver §6) e baseia-se em medições, não em preferência.

## 1. Decisão

**Kotlin + Views (XML + ViewBinding) como base, com Compose apenas nos ecrãs que a original também faz em Compose.**
Arquitetura de ecrã único (uma Activity), Navigation Component, ViewModel + StateFlow, Kotlin Coroutines/Flow, Retrofit + OkHttp + Gson, Coil, Google Maps SDK, Firebase Messaging, DataStore. DI manual (sem Dagger/Hilt).

A `TESTE/app` (Compose-only) **não é apagada**: fica como protótipo validado do contrato. Reaproveita-se a camada de dados (§5) e reescreve-se a camada de UI.

## 2. Evidência (todas as medições vêm de `ux_capture/` e `ui_spec/`)

| Medição | Resultado |
|---|---|
| Layouts XML da original | 2.693. Só **10** contêm uma `ComposeView` |
| Capturas distintas classificadas (sem variantes de scroll) | 108 |
| &nbsp;&nbsp;Views (XML) | **55** (51%) |
| &nbsp;&nbsp;Views com ilhas de Compose | **25** (23%) |
| &nbsp;&nbsp;Só Compose | **10** (9%) |
| &nbsp;&nbsp;Página web dentro da app | **18** (17%) |
| Capturas com pelo menos 3 ids de Views específicos | 144 de 171 (correlação forte com um layout) |
| Hospedagem do Compose nos dumps | `UberComposeView` (raiz Compose dos RIBs) em 57 capturas; `ComposeView` em 23 |
| Bibliotecas (`stack.md`) | Views, Material, ConstraintLayout, Compose, RIBs, RxJava, Retrofit, OkHttp, Gson, Moshi, Coroutines, Coil/Glide/Picasso, Maps, FCM, gRPC |

**Leitura:** a original é **Views primeiro** (74% dos ecrãs são Views, com ou sem ilhas). O Compose aparece em superfícies mais recentes, entre elas: Caixa de entrada, Definições (lista e submenus), Verificação do PIN e Sobre. A classificação por captura está em `ux_capture/toolkit_por_ecra.csv`.

## 3. Opções avaliadas

| Opção | Cumpre o spec? | Reaproveita layouts de referência? | Custo | Veredicto |
|---|---|---|---|---|
| **A. Compose-only** (a TESTE atual) | Não: troca Views por Compose, o que o spec proíbe | Não (Compose não tem XML) | Menor | Rejeitada |
| **B. Views-only** | Parcial: erra nos 9% que são Compose | Sim | Médio | Rejeitada: obriga a desenhar à mão ecrãs que a original faz em Compose |
| **C. Views + Compose por evidência** | **Sim**, ecrã a ecrã | Sim, para os 74% em Views | Maior | **Escolhida** |

Porque a C: o valor do spec é a paridade reproduzível. Em Views, `ui_spec/layouts` dá a hierarquia exata de cada ecrã (como referência, nunca copiada). Onde a original usa Compose, a recriação usa Compose, e a referência é o PNG mais o `ux_behavior.md`.

## 4. Stack camada a camada

| Camada | Original (`stack.md`) | Decisão | Classificação |
|---|---|---|---|
| Linguagem | Kotlin/Java | Kotlin | igual |
| UI | Views XML + Compose (ilhas) | Views XML + ViewBinding; Compose só onde o toolkit do ecrã é `compose` | igual (por evidência) |
| Arquitetura | RIBs (Router, Interactor, Builder) | Ecrã único + Navigation Component + ViewModel/StateFlow | **desvio justificado** (D1) |
| Assíncrono | RxJava (1.172 classes) + Coroutines | Coroutines + Flow | equivalente direto (D2) |
| Rede | Retrofit + OkHttp | Retrofit + OkHttp | igual |
| JSON | Gson (e Moshi em parte) | Gson (`@SerializedName`, como os modelos da original) | igual |
| Imagens | Coil, Glide e Picasso | Coil | equivalente (D3) |
| Mapas | Google Maps SDK | Google Maps SDK (chave própria) | igual |
| Push | Firebase Messaging | Firebase Messaging, projeto próprio | substituir |
| Tempo real | gRPC Ramen + `/ramen/sessions/{id}/messages` | Polling HTTP do canal Ramen (contrato em `endpoints.json`) | equivalente |
| Persistência | WorkManager (Room só interno); sem esquema próprio | DataStore para sessão e preferências | equivalente |
| DI | Dagger (3 classes) | Manual | desvio mínimo (D5) |
| Fonte | Uber Move (proprietária) | Fonte do sistema | desvio justificado (D4) |
| Páginas web | Ajuda, Documentos, Privacidade, etc. | `WebView` com conteúdo próprio, simples | substituir |

## 5. Reaproveitar da `TESTE/app` e reescrever

| Reaproveita | Reescreve |
|---|---|
| `net/` (ApiClient, DriverApi, Models, a ajustar ao `endpoints.json`) | `ui/screens/*` (4 ecrãs em Compose) |
| `data/` (SessionStore, DriverRepository, DriveState) | `ui/components/Controls.kt` (slide-to-confirm) e `QolariMap.kt` (versão Views) |
| `DriveViewModel.kt` (se for independente de Compose) | Tema Compose → temas XML a partir de `ui_spec/design_tokens.json` |
| `backend/mock_server.py` | — |

## 6. Registo de desvios justificados

| # | Desvio | Justificação |
|---|---|---|
| D1 | RIBs → MVVM + Navigation | RIBs é a framework interna da Uber; "equivalente direto" não existe. A estrutura em árvore de ecrãs mantém-se com Navigation. |
| D2 | RxJava → Coroutines/Flow | As Coroutines já existem na original (84 classes). |
| D3 | 3 bibliotecas de imagem → Coil | Uma só chega; "dependências mínimas" (APÊNDICE). |
| D4 | Fonte Uber Move → fonte do sistema | A fonte é proprietária e não se copia. |
| D5 | Dagger → DI manual | A original quase não usa Dagger; a app é pequena. |
| D6 | Login: página web → ecrã nativo com o mesmo layout | O login original é uma página com reCAPTCHA. A recriação replica o aspeto. |
| D7 | 18 páginas web → conteúdo próprio | O conteúdo da Uber não se replica. |

A troca de toolkit de um ecrã (Views ↔ Compose) é uma alteração à linha correspondente de `ux_capture/toolkit_por_ecra.csv` e à tabela do lote.

## 7. P5 em lotes (cada ecrã segue o template do APÊNDICE do spec)

**Entrada de cada ecrã:** PNG, layout candidato em `ux_capture/correlacao_layouts.csv` (só nos de Views), secção do `ux_behavior.md`, e campos do `endpoints.json`. **Saída:** ecrã com os estados vazio, erro e loading, e o teste de ViewModel.

| Lote | Conteúdo | Toolkit (da evidência) | Capturas |
|---|---|---|---|
| **0 — andaime** | Projeto Gradle novo (`ANDOIRD/DRIVER/RECRIACAO/`), ViewBinding, Navigation, barra de 5 separadores, ficheiro de config único, temas a partir de `design_tokens.json`, `ApiClient` reaproveitado | Views | — |
| **1 — Menu e Definições** (sem dados de rede) | Menu, Definições (lista), Acessibilidade, Audição, Comunicação, Navegação, Sons e voz, Sobre, categorias de Ajuda | Menu, Comunicação, Navegação e Ajuda em Views; Definições, Acessibilidade, Audição, Sons e voz, Sobre em Compose | 013, 042–049, 064, 077, 090 |
| **2 — Início e offline** | Painel, mapa, banner "sem rede", janela de erro, arranque a frio, login nativo e token | Views + ilhas | 000, 031–033, 060, 110, 115, 117, 120–126 |
| **3 — Descobrir, Rendimentos, Caixa de entrada** | Cartões, filtros, dias; resumo e detalhes; lista de notificações | Descobrir e Rendimentos em Views; Caixa em Compose | 010–012, 036, 061–063, 080–081 |
| **4 — Oferta e viagem** | Cartão de oferta, aceitar, recolher, PIN, iniciar, terminar, ganhos | por apurar com capturas novas | 100_online + via do laboratório |
| **5 — Segurança, Documentos, Veículos, Comfort** | Ferramentas de segurança, Centro de segurança, documentos, veículos | Views e Compose | 014–030, 070–089 |

**Fora do âmbito inicial:** as 18 páginas web (D7).

**Primeiro passo:** o lote 0, e o lote 1 como o primeiro ecrã a validar com o utilizador (não depende de rede, e tem a maior densidade de capturas).

## 8. Riscos

- **Dois toolkits** aumentam o trabalho de tema e de componentes partilhados. Mitigação: os tokens saem de `design_tokens.json` para os dois.
- **As capturas 031+ são da 4.601** e os layouts da 4.600. Ecrãs que mudaram entre versões têm de ser conferidos no lote correspondente.
- **A classificação de toolkit é por heurística** (ids, classes). Ecrã a ecrã pode estar errada, por isso o CSV é editável.
- **Os handlers do backend estão só em testes** (não publicados nem validados no telemóvel): o lote 4 depende disso.
