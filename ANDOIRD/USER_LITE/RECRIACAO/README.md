# RECRIACAO — Qolari Rider (User Lite)

App nova do passageiro, escrita de raiz a partir de
`ANDOIRD/USER_LITE/ux_capture/` (32 PNG `live`/`clean`), do contrato
`ANDOIRD/USER_LITE/endpoints.json` e do backend `BACKEND/apps/userlite.py`.

Não contém código nem assets da Uber Lite. O pacote é `com.qolari.userlite`; a
marca, os ícones e as ilustrações são próprios.

## Ecrãs

| Área | Ecrãs |
|---|---|
| Entrada | boas-vindas, telefone, código, escolha de país |
| Início | painel, mapa desenhado, sugestões, promoções, localização |
| Viagem | pesquisa de destino, lugares guardados, escolha de categoria, pagamento, pedido |
| Viagem ativa | procura, motorista a caminho, PIN, em curso, fim, avaliação, cancelamento |
| Conta | menu, carteira, atividade/histórico, promoções, ajuda, legal, gerir conta |
| Gerir conta | casa, dados pessoais, segurança/sessão, privacidade, verificação |

Cada ecrã implementa `default`, `loading`, `empty` e `error`; o banner de rede
(`MainActivity`) cobre o estado offline.

## Stack

Kotlin, Views (XML + ViewBinding), Navigation Component, ViewModel + StateFlow,
Retrofit + OkHttp + Gson, Coroutines, DataStore. A referência Lite é uma WebView;
o contrato nativo é `designed` (ver `endpoints.json`).

## Configuração

`app/src/main/java/com/qolari/userlite/config/AppConfig.kt`:

| Ambiente | URL | Uso |
|---|---|---|
| `USB` | `http://127.0.0.1:8090` | backend local com `adb reverse` |
| `LAN` | `http://192.168.1.204:8090` | backend no PC pela rede |
| `SERVER` | `https://rider.qolari.com` | servidor (quando publicado) |

A app arranca em `USB` para os testes de laboratório. Nenhum ecrã conhece HTTP:
`UserRepository` é o único ponto de acesso à API.

## Compilar e testar

```powershell
$env:JAVA_HOME = "C:\Program Files\Eclipse Adoptium\jdk-21.0.12.101-hotspot"
.\gradlew.bat assembleDebug testDebugUnitTest
```

APK: `app/build/outputs/apk/debug/app-debug.apk`.

## Testar no telemóvel

1. `BACKEND\.venv\Scripts\python server.py` (porta 8090; código de login `0000`).
2. `adb reverse tcp:8090 tcp:8090`.
3. Instalar o APK; contas do seed `+351910000001` (Ana), `...002` (Bruno),
   `...003` (Carla).
4. Para a viagem completa, a Driver tem de estar online (`+351920000001`,
   Carlos) e mais perto da recolha do que os motoristas simulados.
5. No fim: parar o servidor e `adb reverse --remove tcp:8090`.

## Evidência e tolerância

- Ecrãs de captura: `live`/`clean` em `../ux_capture/` — a app nova **não** é
  spec.
- Contrato do backend: `designed`; foi materializado no telemóvel (`served`).
- Mapa: desenhado (sem SDK/chave), com zoom e recentragem reais.
- Sem FCM: o tempo real é o canal `ramen`/polling.
- Sem login social, reCAPTCHA ou IAP.
- Pagamento é simulado (dinheiro/cartão de laboratório); não há cartões reais.
- A página de conta é própria (não há captura da Lite para conta).

## Ações sem efeito

Não existem. As entradas que a Lite mostra e este âmbito não cobre (entrega,
reserva, paragens, escolha de cidade, agendamento, passageiros) foram retiradas
da UI; o que ficou abre um destino real ou muda estado no backend. A matriz está
em [`../../../capabilities.md`](../../../capabilities.md).
