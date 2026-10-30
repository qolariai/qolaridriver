# rea_evidence/ — índice

**Fonte:** REA_BINDINGS.md §3. Uma linha por artefacto. Sem linha, o artefacto não
existe para a auditoria.

**Aviso de origem:** o servidor MCP **REA não estava disponível** nesta sessão.
Os artefactos foram produzidos a partir dos ficheiros locais, com o mesmo formato.
A coluna `ferramenta` diz `local` onde devia dizer a ferramenta do REA — nunca se
apresenta trabalho local como trabalho do REA.

```
artefacto | ferramenta | entrada | data | digest | unknown/limitacao
```

| artefacto | ferramenta | entrada | data | digest | unknown/limitação |
|---|---|---|---|---|---|
| `00_artifact/driver.apk` | local | `ANDOIRD/DRIVER/source-original.apk` | 2026-10-30 | `e13afc35b3497b6a` | REA `inspect_artifact` indisponível |
| `00_artifact/rider.apk` | local | `ANDOIRD/USER_LITE/spec_src/apk_instalado/lite_base.apk` | 2026-10-30 | `b77a621177c065fe` | REA `inspect_artifact` indisponível |
| `00_artifact/fleet.apk` | local | `ANDOIRD/FLEET/original.apk` | 2026-10-30 | `4f8de80ac79bd2dd` | REA `inspect_artifact` indisponível |
| `01_access/package.json` | decode_android_resources | `com.ubercab.driver` | 2026-10-30 | — | manifesto extraído por apktool em sessão anterior |
| `02_capture/` | capture_adb_screen | PTP-N49 / Honor | 2026-10-30 | — | 172 PNG + 4 vídeos; o Honor já não está ligado |
| `03_spec/resources_index.json` | decode_android_resources | `ui_spec/` | 2026-10-30 | — | 2 693 layouts, 172 idiomas |
| `04_contract/shapes.index.json` | — | `endpoints.discovered.json` | 2026-10-30 | — | 22 de 39 endpoints são `designed` |
| `05_close/obligations.json` | local | `features.md` ×2 | 2026-10-30 | — | 142 obrigações, 15 abertas |
| `05_close/verify.json` | local | artefactos do projeto | 2026-10-30 | — | 9 passaram, 0 falharam |
| `05_close/coverage.json` | local | `features.md` ×2 | 2026-10-30 | — | cobertura 89.4% |

## Resumo do ledger

| Métrica | Valor |
|---|---|
| Obrigações | 142 |
| Cumpridas (`ok`) | 127 |
| Excluídas com aprovação | 0 |
| **Abertas (gap)** | **15** |
| Cobertura | **89.4%** |

## Obrigações abertas

| obrigação | app | nome | status |
|---|---|---|---|
| `driver:F-home-04` | driver | Ver o tempo de conducao | `em falta` |
| `driver:F-platform-01` | driver | Push do sistema (FCM) | `em falta` |
| `driver:F-platform-02` | driver | Deep links (50 filtros) | `em falta` |
| `driver:F-platform-03` | driver | Biometria / credenciais | `em falta` |
| `driver:F-platform-04` | driver | i18n (172 idiomas no binario) | `em falta` |
| `driver:F-platform-05` | driver | Dark mode | `em falta` |
| `driver:F-platform-06` | driver | Acessibilidade (TalkBack) | `em falta` |
| `rider:F-platform-01` | rider | Push do sistema (FCM) | `em falta` |
| `rider:F-platform-02` | rider | Deep links (21 filtros) | `em falta` |
| `rider:F-platform-03` | rider | Biometria | `em falta` |
| `rider:F-platform-04` | rider | Idiomas (values-ar/en/es/fr/hi/pt) | `em falta` |
| `rider:F-platform-05` | rider | Dark mode | `em falta` |
| `rider:F-platform-06` | rider | Contactos (partilha) | `em falta` |
| `rider:F-platform-07` | rider | Camera / fotos (chat) | `em falta` |
| `rider:F-notifications-01` | rider | Notificacoes in-app (badge) | `em falta` |

## Proveito

Este ledger alimenta `capabilities.md` e `backlog.md` (MEGA FASE 7.1) e o número
de cobertura entra no `RELATORIO_FINAL.md` (MEGA FASE 6.9). Sem ele, o ledger
fecharia sobre o vazio.

