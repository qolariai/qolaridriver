# Qolari Drive — APK rebrand profundo + backend local

APK final: **`qolari-drive.apk`** (~258 MB, zipaligned, assinado v3)
Keystore: `tools/qolari.keystore` (alias `qolari`, pass `qolari123` — troca quando quiseres)

## Rename profundo (pass 2)

- **Packages Java**: `com.ubercab.*` + `com.uber.*` → `com.qolari.*` — dirs smali movidos (53 raízes) e ~260k referências atualizadas (type refs `Lcom/uber/…`, `android:name`, custom views em layouts, authorities, deeplinks, metadata Kotlin)
- **Domínios vendor → backend local**: `facebook.com/.net`, `twilio.com`, `paypal*`, `braintreegateway`, `adyen`, `crashlytics`, `app-measurement`, `google-analytics`, `doubleclick`, `appsflyer*`, `onelink/app.link`, `adjust`, `sentry`, `amplitude`, `veriff`, `jumio`, `hyperwallet`, `nauto`, `cloudfront.net` (CDNs Uber), `sng.link`, `firebase*.googleapis.com`, `firebaseio.com`…
- **Preservados** (funcionais, não-marca): `googleapis.com` genérico, `google.com`, `gstatic`, `play.google.com`, `type.googleapis.com` (proto type-URL), packages de SDKs (`com.braintreegateway.*` etc.), fonts `UberMove` (design), nomes proto `com.uber.*` em blobs serializados (wire-format — renomear partiria desserialização)
- **Nomes de produto** em strings: `UberOne`, `UberEats`, `ubereats`… → `Qolari*` (todos os locales)
- **Logos in-app**: 15 `*uber*logo*.xml` vectors → marca "Q" genérica (mesmo viewport)
- Mantidos como identificadores internos invisíveis: nomes de ficheiros `ub__*`, `uber_*` em resource names

## O que foi alterado

| Item | Original | Novo |
|---|---|---|
| Package | `com.ubercab.driver` | `com.qolari.driver` |
| Nome da app | "Uber Driver" | "Qolari Driver" |
| Ícone | logo Uber | "Q" genérico (anel branco / fundo escuro) |
| Domínios Uber (`*.uber.com`, `uberinternal.com`, failovers `cn-dc1.*`) | HTTPS Uber | `http://192.168.1.204` (porta 80) |
| Cleartext HTTP | bloqueado | permitido (`usesCleartextTraffic` + NSC) |
| API keys (Google Maps, Firebase/GCM, Facebook, Braintree, Crashlytics) | chaves Uber | placeholders válidos |
| Metadados Play (`requiredSplitTypes`, `stamp`, `vending.splits`) | presentes | removidos (instalação standalone OK) |

## Backend

O APK fala agora com `http://192.168.1.204` (IP LAN deste PC). 
**XAMPP/Apache na porta 80 serve logo** — aponta um vhost ou pasta em `htdocs` para a tua API.

- **Telemóvel físico**: mesmo Wi-Fi → funciona já.
- **Emulador**: `192.168.1.204` também funciona (o emulador sai pela rede do host). Alternativa sem IP: `10.0.2.2`.

### Trocar o IP/porta depois

```bash
# em decoded/ : substituir em todos os ficheiros de texto
grep -rl "192.168.1.204" decoded | xargs sed -i 's/192\.168\.1\.204/NOVO_HOST:PORTA/g'
java -jar tools/apktool.jar b decoded -o novo.apk -j 8
java -jar tools/apk-signer.jar --apks novo.apk --ks tools/qolari.keystore \
    --ksAlias qolari --ksPass qolari123 --ksKeyPass qolari123
```

## Endpoints mapeados

- `api_paths.txt` — **1054 caminhos** extraídos do smali (`/rt/...` = realtime API, `/api/grpc/...`, etc.)
- `endpoints_dex.txt` — 561 URLs completas extraídas dos DEX

Domínios principais originalmente usados (agora todos → teu backend):

| Domínio | Função |
|---|---|
| `cn-geo1.uber.com` | API edge principal (chamadas `/rt/*`) + conteúdo estático |
| `cn-dc1.*` (5 failovers) | failover do edge |
| `auth.uber.com` | login/OAuth (`/v2`, `/oauth/...`) |
| `bonjour.uber.com` | marketplace/webviews |
| `platform.uberinternal.com` | config interna |
| `tb-static.uber.com`, `static-maps.uber.com`, `mobile-content.uber.com` | imagens/mapas |

Endpoints essenciais para o app abrir: `/rt/silent-authentication/initiate`, `/rt/drivers/{driverUUID}/go-online`, `/rt/earner-profile/get-profile-hub`, auth em `/oauth/*` e `/v2`. O resto falha graciosamente (o app mostra UI mas sem dados).

## Avisos

- A app pode ter **signature pinning / attestation** interna — se crashar no arranque, é esperado; o design/flows continuam navegáveis na maioria dos ecrãs.
- O Google Maps não renderiza sem uma `maps_api_key` tua (placeholder em `res/values/strings.xml` → `maps_api_key`).
- A pasta `decoded/` (fonte recompilável, ~2 GB) fica para iterares. `qolari-drive-unsigned.apk` pode ser apagado.
