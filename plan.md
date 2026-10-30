# plan.md — Declaração inicial do clone Qolari

**Versão:** 1.0 · **Data:** 2026-10-25 · **Documento de trabalho:** `PROMPT_CLONE_MEGA.md`

## 1. Identificação

| Campo | Valor |
|---|---|
| Ecossistema | Qolari Mobility (laboratório de aprendizagem) |
| Apps | Driver (Android), Rider (Android), Fleet (Android); iOS opcional e fora do âmbito atual |
| Backend | `BACKEND/` — FastAPI + SQLite, um processo modular |
| Backoffice | `BACKOFFICE/` — React + Vite, servido pelo backend |
| Marca do entregável | **Qolari** (própria; não é a marca do original) |
| Distribuição | Nenhuma. Não se publica, não se opera a sério |
| Raiz | `C:\xampp\htdocs\QOLARI\PROJETOS OFICIAIS\QOLARI DRIVER\` |

### Artefactos de referência

| App | Pacote de referência | Versão | Ficheiro | SHA-256 |
|---|---|---|---|---|
| Driver | `com.ubercab.driver` | 4.600.10000 (instalada); `source-original.apk` provável 4.599.10004 | `ANDOIRD/DRIVER/source-original.apk` | `E13AFC35B3497B6AAECD939BCF63E14A8D23E138039FE3C4F1C257286103FD82` |
| Rider | `com.ubercab.uberlite` | 1.248.10001 | `ANDOIRD/USER_LITE/spec_src/apk_instalado/lite_base.apk` | `B77A621177C065FEE63B99F81BBEAED1708642C38A2CC255ED8BE85244B597BE` |
| Fleet | `com.ubercab.fleet` | 1.4.10000 | `ANDOIRD/FLEET/original.apk` | `4F8DE80AC79BD2DDE7D5C1BEB598B3526FD34620048A61FA386AAAAEF49647D1` |

**Nota de versão (Driver):** a instalação no PTP-N49 é a 4.600.10000 e foi essa que se
capturou e descodificou (`spec_src/decoded_4600/`). A 4.601.10000 aparece nas capturas a
partir de `031_` porque a app se atualizou sozinha a 16-10 às 20:49. O registo por
ficheiro está em `ANDOIRD/DRIVER/ux_capture/versoes.csv`. A diferença entre versões é uma
tolerância declarada, não um facto escondido.

## 2. Roles a cobrir

| Role | App | Como entra | O que move |
|---|---|---|---|
| Passageiro | Rider | telefone + código `0000` (laboratório) | pedido, cancelamento, avaliação |
| Motorista | Driver | telefone + código `0000` (laboratório) | online/offline, aceitar/recusar, recolha, início, fim |
| Frota | Fleet | telefone + código `0000` (laboratório) | veículos, motoristas, convites, ganhos |
| Operação | Backoffice | e-mail + palavra-passe (seed `admin@qolari.local`) | viagens, motoristas, documentos, simulador |
| Suporte/KYC | Backoffice | conta com papel `operator` | aprovação de documentos, bloqueios, contas |
| Financeiro | Backoffice | conta com papel `finance` | pagamentos, acertos, leitura de tudo |
| Sistema | backend | relógio de 1 s | expiração de propostas, despacho, simulação |

## 3. Tipo de app e topologia preliminar

**Tipo:** marketplace de dois lados (ride-hailing). **Evidência:** peer triggers
(oferta só chega com motorista online), despacho por proximidade, geo, avaliações
cruzadas, estados que só outro ator move (`requested → accepted`), liquidação com
comissão e taxa de frota. Ver `topology.md` §1.

**Topologia preliminar (a fechar na FASE 4.5):**

- **1 backend modular** — `BACKEND/`, um processo, uma base de dados. As portas
  (80/8090/3000/8300) emulam os hosts das apps; não são serviços separados.
- **1 backoffice SPA** — quatro áreas funcionais com RBAC (`admin`, `operator`,
  `finance`): Ops/Despacho, Suporte/KYC, Financeiro, Administração.
- **3 apps Android** + **1 app iOS opcional** (fora do âmbito atual).
- Justificação da não-separação em microserviços: escala de laboratório, um deploy, uma
  consistência; a separação teria custo sem retorno medido.

## 4. Credenciais

| Origem | Estado | Nota |
|---|---|---|
| Uber original (Driver/Rider) | **sim** — conta própria do utilizador | login feito pelo utilizador; nenhuma password ou código escrito em ficheiros |
| Apps do laboratório (`com.qolari.*`) | **sim** — contas do seed | código fixo `0000`; contas em `BACKEND/domain/seed.py` |
| Backoffice | **sim** — seed local | `admin@qolari.local` / `admin`; muda-se em Conta |
| Fleet | **sim** — conta do seed | `+351930000001` (Frota Tejo) |
| Terceiros (Google, Apple, bancos) | **não** | não se usam contas de terceiros |

## 5. Gates detetados

| Gate | Estado | Consequência |
|---|---|---|
| Transporte | **aberto** no original (apps não modificadas) | captura `clean` |
| Autenticação | **aberto** (conta própria) | captura autenticada `live` |
| Estado de conta | **aberto** (motorista aprovado, passageira ativa) | home/menu/online capturados |
| Identidade | **aberto** no laboratório (seed) | estados de aprovação simulados |
| Peer | **parcial** — precisa de Rider + Driver em simultâneo | estados de viagem via laboratório; `peer` declarado |
| Geo | **parcial** — GPS real + simulação no backend | mapa desenhado; sem SDK |
| Terceiros presos à assinatura | **fechado/indisponível** — Maps SDK sem chave, FCM não configurado, login social não implementado | `thirdparty`; não contamina a spec |
| Marca/legal | **não se transplanta** | marca Qolari e desenhos próprios |

## 6. Modo por role

| Role | Modo | Captura | Contrato | Declaração |
|---|---|---|---|---|
| Driver | `REAL` + `VIVA` | pré-auth e ecrãs principais `clean`; viagem via backend próprio `served` | `ANDOIRD/DRIVER/endpoints.json` + `endpoints.json` | UI alta; estados de viagem com forma `static` (layouts) e dados nossos |
| Rider | `REAL` + `VIVA` | pré-auth, pesquisa, categorias e offline `clean`; pós-pedido via laboratório `served` | `BACKEND/contracts/rider_*` + `endpoints.json` | UI alta na pré-auth; pós-pedido com tolerância |
| Fleet | `ESTÁTICA+` | sem captura própria | contrato extraído do APK + backend `served` | tolerância declarada; não se promete paridade visual |
| Backoffice | `designed` | não existe no original | `BACKEND/console/` | cobertura da máquina de estados, não paridade visual |

## 7. Cobertura prometida

- **Driver:** os 109 ecrãs base de `ux_capture/` (mais 55 variantes de scroll e 13
  capturas online) estão classificados em `coverage.md`. Todos os ecrãs implementados na
  `RECRIACAO/` têm lote; os validados no telemóvel estão em `VALIDACAO.md`; os que não
  estão, têm razão.
- **Rider:** os 32 PNG de `ANDOIRD/USER_LITE/ux_capture/` estão classificados e a
  recriação existe em `ANDOIRD/USER_LITE/RECRIACAO/` (Kotlin + Views, 10 testes). A
  captura está incompleta (Ajuda completa, Promoções, Legal, Gerir conta); os gaps estão
  declarados, não escondidos. A conta é `designed` (não há captura da Lite).
- **Fleet:** zero ecrãs capturados. A cobertura prometida é **funcional** (contrato e
  operação), não visual.
- **Backoffice:** cobertura da máquina de estados de `topology.md` §8; todos os estados
  têm um ator e um ecrã.

## 8. Tolerância declarada

Aceites e escritos no relatório final:

1. **Fonte Uber Move → fonte do sistema** (D4). Quebras de linha ligeiramente diferentes.
2. **Mapa:** real do Google quando `MAPS_API_KEY` está em `local.properties` (Rider e
   Driver); a rota é uma linha reta até haver OSRM. Sem chave, mapa desenhado próprio.
   O original usa Google Maps; a forma do mapa não é replicada.
3. **FCM/push:** não configurado; o canal `ramen` (long-poll) é o tempo real do
   laboratório. Notificações do sistema não são capturáveis.
4. **Login social / reCAPTCHA / IAP:** ausentes por decisão; o login é nativo por telefone.
5. **Páginas web** (Ajuda, Documentos, Privacidade, Comfort): conteúdo próprio, não o
   conteúdo do original. 18 páginas em `ui_spec/` ficam fora do âmbito visual.
6. **Estados de viagem sem captura original:** forma tirada dos layouts (`static`) e
   comportamento do backend; dados `served`. Não são `live`.
7. **Fleet:** sem paridade visual; só contrato e operação. A app usada no
   laboratório é a APK re-branded (`com.qolari.fleet`), instrumento e não
   entregável; a UI própria não foi recriada.
8. **Rider:** o contrato nativo é `designed` (a referência Lite é WebView). A conta
   é `designed`. Entradas sem equivalente (entrega, reserva, paragens, cidade,
   filtro pessoal) foram retiradas da UI; ver `capabilities.md`.
9. **iOS:** fora do âmbito atual.
10. **Versão 4.600 vs 4.601:** ecrãs que mudaram entre versões estão assinalados em
    `coverage.md`; a referência de layout é a 4.600.

## 9. Portões

- [x] FASE 0 — artefacto + hash
- [x] FASE 1 — `access_plan.md`
- [x] FASE 2 — captura Driver + Rider (parcial); `coverage.md`
- [x] FASE 3 — `ui_spec/` + `stack.md` + `STACK_DECISAO.md`
- [x] FASE 4 — catálogo extraído + `endpoints.json` do ecossistema
- [x] FASE 4.5 — `topology.md`
- [x] FASE 4.6 — máquina de estados + teste dos três espelhos
- [x] FASE 4.7 — **`features.md`** (Driver): 86 features, 109/109 capturas,
      72 `ok`, 8 `excluído` com aprovação escrita, 6 `em falta`
- [x] FASE 5 — Driver e Rider recriadas; Fleet coberta por contrato/operação
      (app de laboratório, sem paridade visual — declarado em §8)
- [x] FASE 6 — validação no Honor (Rider e Driver); ecossistema declarado
- [ ] FASE 7 — `capabilities.md` e `backlog.md` reindexados por F-ID; **6 gaps
      `F-platform-*` abertos** + decisão de âmbito G-07

### 9.1 Programa V4

O programa é a versão **v4** (`COMPARAÇOES DE PROMPT/PROMPTS_V4/`), que acrescenta
a FASE 4.7. O `PROMPT_CLONE_MEGA.md` desta pasta foi actualizado para v4.

A FASE 4.7 da **Rider** ainda não existe: até existir, o `capabilities.md` da
Rider não pode citar F-ID como a Driver faz. É o próximo passo de documentação.

## 10. O que não se faz

- Comprar conta, usar conta de terceiros sem consentimento ou fabricar identidade para
  aceder ao serviço real.
- Instalar builds modificados num dispositivo que não é do projeto.
- Distribuir APKs renomeadas.
- Apresentar `served`/`presumed` como `live`.
- Copiar assets, marca, nome ou ícone do original.
- Publicar no Hetzner sem aprovação.
