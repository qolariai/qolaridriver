# stack.md — Rider (User Lite)

**Decisão:** a referência Lite é uma WebView; não há uma stack nativa observável. A
recriação usa a mesma família da Driver, com Views (sem Compose), para manter o
laboratório coerente e testável.

| Camada | Escolha | Nota |
|---|---|---|
| Linguagem | Kotlin | JVM 17, AGP/Gradle do projeto |
| UI | Views + XML + ViewBinding | Navigation Component, Fragments |
| Estado | ViewModel + StateFlow | sem lógica nos Fragments |
| Rede | Retrofit + OkHttp + Gson | contrato em `endpoints.json` |
| Assíncrono | Coroutines | polling de 2 s na viagem |
| Persistência | DataStore | sessão e preferências |
| Mapas | Google Maps SDK (`play-services-maps` 20.1.0) | chave em `local.properties`; miniaturas dos cartões desenhadas |
| Tempo real | `ramen` long-poll + polling | sem FCM |
| Testes | JUnit | 11 testes (contrato, mapa, config) |

## Configuração

`app/src/main/java/com/qolari/userlite/config/AppConfig.kt` é o único lugar com hosts:

| Estágio | URL |
|---|---|
| `USB` (default) | `http://127.0.0.1:8090` com `adb reverse` |
| `LAN` | `http://192.168.1.204:8090` |
| `SERVER` | `https://rider.qolari.com` (quando publicado) |

Nenhum ecrã conhece HTTP: `UserRepository` é o único ponto de acesso à API.

## Dependências

Só as equivalentes às da Driver/laboratório: AndroidX, Material, Navigation,
Lifecycle/ViewModel, Retrofit/OkHttp/Gson, Coroutines/DataStore. Google Maps SDK,
sem FCM, sem login social.
