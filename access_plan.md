# access_plan.md — Decisão de acesso por app e role

**Data:** 2026-10-25 · **Método:** sonda antes de prometer cobertura (MEGA §3).
**Regra:** sem credenciais não é sem plano; a falta de conta muda o modo, não cancela o
projeto.

## 1. Resumo

| App | Role | Modo | Credenciais | Cobertura prometida | Integridade |
|---|---|---|---|---|---|
| Driver | motorista | `REAL` + `VIVA` | conta própria do utilizador (Uber) + seed `0000` (laboratório) | 109 ecrãs base + variantes + online | `clean` no original |
| Rider | passageiro | `REAL` + `VIVA` | conta própria do utilizador (Uber Lite) + seed `0000` | 32 capturas; pré-auth e escolha de viagem | `clean` no original |
| Fleet | frota | `ESTÁTICA+` | seed `+351930000001` | contrato e operação; sem paridade visual | `static` |
| Backoffice | ops/suporte/financeiro | `designed` | seed local | máquina de estados coberta | `designed` |

## 2. Escada de acesso usada

| N | Via | Usada? | O que deu |
|---|---|---|---|
| N0 | Registo público / conta própria | **sim** | conta real da Uber no telemóvel; captura `live` |
| N1 | Captura pré-auth | **sim** | onboarding, login, escolha de país, offline |
| N2 | Cópia repointada + stub | **sim, como instrumento** | `qolari-drive-server-v3.apk` contra o nosso backend; validou o contrato da viagem |
| N3 | Conta própria + sandbox | **sim** | home, menu, definições, online, oferta |
| N4 | `ESTÁTICA+` | **sim** | layouts, strings, drawables, anim para os ecrãs sem execução |
| N5 | Conta comprada / identidade falsa | **nunca** | proibido |

**Ordem real:** N1 → N0/N3 → N2 (só para o contrato) → N4. A conta é do utilizador; o
login foi feito por ele. Nenhuma password ou código de login está escrita em ficheiros.

## 3. Gates por app

### Driver

| Gate | Estado | Evidência |
|---|---|---|
| Transporte | aberto | app original 4.600/4.601, sem patch, no PTP-N49 |
| Autenticação | aberto | sessão da conta do utilizador; home e menu capturados |
| Estado de conta | aberto | motorista aprovado; ofertas reais recebidas (13 capturas `100_online_*`) |
| Identidade | aberto no laboratório | seed com motoristas aprovados/pendentes |
| Peer | parcial | oferta real observada; aceitar/viagem exigiu o laboratório (Rider + Driver) |
| Geo | parcial | GPS real nas capturas; simulação no backend |
| Terceiros | Maps SDK sem chave; FCM não configurado | mapa por desenhar; push do sistema não capturável |
| Marca | não se transplanta | Qolari |

### Rider (Uber Lite)

| Gate | Estado | Evidência |
|---|---|---|
| Transporte | aberto | Lite 1.248.10001, sem patch |
| Autenticação | aberto | conta do utilizador; capturas de logout e login |
| Estado de conta | aberto | conta ativa; sem viagens no histórico |
| Peer | **bloqueado por regra** | nunca se confirmou um pedido real (geraria cobrança e motorista real) |
| Geo | aberto | localização real; moradas ocultadas nas imagens |
| Terceiros | WebView da Uber | o conteúdo é web; sem layouts nativos |
| Marca | não se transplanta | Qolari |

### Fleet

| Gate | Estado | Evidência |
|---|---|---|
| Transporte | aberto | APK 1.4.10000 + cópia de laboratório |
| Autenticação | aberto | seed `+351930000001` |
| Estado de conta | aberto | frota com motoristas e veículos |
| Peer | aberto | backend próprio |
| Geo | aberto | posições simuladas/real |
| Terceiros | nenhum relevante | — |
| Marca | não se transplanta | Qolari |

### Backoffice

Não existe no original. É `designed`. O acesso é local (e-mail + palavra-passe do seed),
com RBAC `admin` / `operator` / `finance` e registo de ações.

## 4. Superfícies de terceiros (checklist MEGA §3.5)

Aplicado a qualquer captura de build modificado (`repack_suspect`):

- [x] **Mapas** — o SDK exige chave; no laboratório o mapa é desenhado. Não se confunde
      mapa em branco com design.
- [x] **WebViews** — a moldura é spec; o conteúdo de terceiros não. As páginas web do
      original não entram no entregável.
- [x] **Push/FCM** — não configurado; o canal `ramen` é o tempo real do laboratório.
      Estados de notificação do sistema não são capturáveis.
- [x] **Login social / SSO** — ausente por decisão; o login é nativo por telefone.
- [x] **IAP / pagamentos** — não se usam. O laboratório tem liquidação interna.
- [x] **Ads** — não existem no âmbito.
- [x] **Fontes e ícones** — a Uber Move é proprietária; usa-se a fonte do sistema e
      ícones próprios. Sem icon fonts de terceiros.

## 5. O que foi capturado e com que integridade

| Origem | O que | Integridade | Uso |
|---|---|---|---|
| `com.ubercab.driver` 4.600/4.601 | 172 PNG, 172 dumps, 4 vídeos, CSVs | `clean` | spec visual e comportamental |
| `com.ubercab.uberlite` 1.248 | 32 PNG, `travessia.csv` | `clean` | spec da Rider (parcial) |
| `com.qolari.driver` (repoint) | tráfego, estados de viagem | `repack_suspect` | **só** contrato e validação; não é spec visual |
| `com.qolari.drivereplica` (app nova) | `RECRIACAO/captures/` | `newapp` | comparação; **nunca** spec |
| Backoffice | ecrãs próprios | `designed` | operação |

**Regra de promoção:** um pixel de `repack_suspect` só passa a `clean` se for confirmado
contra `ui_spec/` do binário original. O que não se confirmar fica marcado para sempre.

## 6. Cobertura prometida e tolerância

- **Driver:** paridade visual exigida nos 109 ecrãs base; comportamento de
  `ux_behavior.md`; estados vazio/erro/loading/offline onde capturados.
- **Rider:** paridade visual na pré-auth e escolha de viagem; pós-pedido com tolerância
  (não se confirmou um pedido real).
- **Fleet:** cobertura funcional; sem paridade visual.
- **Backoffice:** cobertura da máquina de estados; sem paridade visual.
- **Tolerância:** mapa, FCM, login social, páginas web, fonte, iOS, versão 4.600 vs 4.601.

## 7. O que nunca se faz

- Comprar conta, usar conta de terceiros sem consentimento ou fabricar identidade para
  aceder ao serviço real.
- Instalar build modificado num dispositivo que não é do projeto.
- Distribuir a APK patchada.
- Apresentar `served`/`presumed` como `live`.
- Copiar assets, marca, nome ou ícone para o entregável.
- Publicar algo reconhecivelmente da marca de outro.

## 8. Riscos abertos

1. **Mapa real:** falta `MAPS_API_KEY`. Sem ela, o mapa é um desenho.
2. **Rota real:** OSRM opcional; sem ele a rota é uma linha reta.
3. **Fleet:** sem captura, a paridade visual não é mensurável.
4. **Rider pós-pedido:** a regra de não confirmar viagem real mantém estes ecrãs em
   `served`, não `live`.
5. **Telemóvel partilhado:** outra app pode passar à frente; a captura para e avisa.
