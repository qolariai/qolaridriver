# VALIDACAO_HONOR — prova de execução no dispositivo

**Data:** 2026-10-25 · **Device:** HONOR PTP-N49, Android 16 · **Backend:** local, via
`adb reverse tcp:8090` e `tcp:8091`.

Estas capturas são da **app nova** (`newapp_*`), não da app original. Servem para provar
que o fluxo e o mapa funcionam no dispositivo; **nunca** entram em `ux_capture/` nem na
spec. A referência visual continua a ser `ANDOIRD/DRIVER/ux_capture/` (`live`/`clean`) e
`ANDOIRD/USER_LITE/ux_capture/` (`live`/`clean`).

## Ficheiros

| Ficheiro | Momento |
|---|---|
| `driver_01_home_mapa.png` | Driver: Início com mapa Google real (Amadora) |
| `driver_02_mapa.png` | Driver: mapa inteiro, radar e atalhos |
| `driver_03_pesquisa.png` | Driver: pesquisa de locais (folha própria) |
| `driver_04_reportar.png` | Driver: comunicar problema de mapa |
| `driver_05_seguranca.png` | Driver: ferramentas de segurança |
| `driver_06_definicoes.png` | Driver: Definições sem linhas inertes |
| `driver_07_privacidade.png` | Driver: Privacidade (página própria) |
| `driver_08_ajuda.png` | Driver: categoria da Ajuda (página própria) |
| `driver_09_oferta_mapa.png` | Driver: oferta com rota por estrada no mapa |
| `rider_01_home_mapa.png` | Rider: Início com mapa Google real |
| `rider_02_escolher_viagem.png` | Rider: escolher viagem com rota por estrada |
| `rider_03_motorista_a_caminho.png` | Rider: motorista a caminho, rota e marcadores |

A viagem usada nas capturas é a 75 (cancelada no fim para deixar o laboratório limpo).
As viagens 68-75 documentam o ciclo completo, as correções e os mapas em
`VALIDACAO_MEGA.md`.

## Como repetir

```powershell
# 1. backend e túneis
cd BACKEND; .\.venv\Scripts\python server.py
adb -s <SERIAL> reverse tcp:8090 tcp:8090
adb -s <SERIAL> reverse tcp:8091 tcp:8091

# 2. instalar as recriações (não as APKs renomeadas)
adb -s <SERIAL> install -r ANDOIRD\DRIVER\RECRIACAO\app\build\outputs\apk\debug\app-debug.apk
adb -s <SERIAL> install -r ANDOIRD\USER_LITE\RECRIACAO\app\build\outputs\apk\debug\app-debug.apk

# 3. chave dos mapas (uma vez em cada local.properties)
#    MAPS_API_KEY=<valor de google_maps_api_key.txt>
```

Contas do seed: Rider `+351910000001` (Ana), Driver `+351920000003` (João), código
`0000`. Para a viagem completa, deixar **apenas o motorista da app online** (o backoffice
tem “online/offline” por motorista). O PIN aparece no ecrã do Rider e é pedido no Driver.

## Limpeza

No fim:

```powershell
adb -s <SERIAL> reverse --remove tcp:8090
adb -s <SERIAL> reverse --remove tcp:8091
```

Parar o `server.py`. As capturas ficam aqui como evidência; não mover para `ux_capture/`.
