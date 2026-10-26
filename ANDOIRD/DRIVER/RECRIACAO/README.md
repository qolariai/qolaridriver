# RECRIACAO — Qolari Driver (recriação limpa, via spec)

App nova escrita de raiz a partir de `../ui_spec/`, `../ux_capture/`, `../endpoints.json` e `../STACK_DECISAO.md`. **Não contém código nem assets da app original**: os ficheiros de `ui_spec/` são só referência de fidelidade.

**Evidência (MEGA):** esta pasta é a `app_nova`. As capturas em `captures/` são da app
nova (equivalente a `newapp_*`; novas capturas usam esse prefixo) e **nunca** entram na
spec. A referência é
`../ux_capture/` (`live`, `clean`) + `../ui_spec/` (`static`). A cobertura e os gaps
estão em [`../../../coverage.md`](../../../coverage.md); a topologia e a
orquestração em [`../../../topology.md`](../../../topology.md). Os ecrãs de
viagem sem captura original têm forma `static` dos layouts e dados `served` do nosso
backend — não são `live`.

Stack decidida: Kotlin, Views (XML + ViewBinding) com Compose só nos ecrãs que a original faz em Compose, Navigation Component, ViewModel e StateFlow, Retrofit + OkHttp + Gson, Coroutines, DataStore. A `../TESTE/app` (Compose-only) mantém-se como protótipo do contrato; daqui reaproveita-se a camada `net/` e `data/`.

## Estado

Lotes 0 a 5 feitos e validados no telemóvel PTP-N49; P7 fechada (`VALIDACAO.md`). 74 testes de unidade a passar (backend: 48). Ver também `CORRECOES_POS_LOTE5.md`.

| Lote | Conteúdo | Nota |
|---|---|---|
| 0 | Andaime, 5 separadores, config única, tema | `captures/COMPARACAO_LOTE0.md` |
| 1 | Menu e Definições (Compose só onde a original é Compose) | `COMPARACAO_LOTE1.md` |
| 2 | Início (painel e mapa), login por telefone, sessão, banner sem rede, janela Erro | `COMPARACAO_LOTE2.md` |
| 3 | Descobrir, Rendimentos (dados reais), Caixa de entrada (Compose) | `COMPARACAO_LOTE3.md` |
| 4 | Proposta, aceitar, recolha, PIN, em viagem, fim com ganhos, avaliação | `COMPARACAO_LOTE4.md` (estados da viagem sem original capturada, `[inf]`) |
| 5 | Segurança, Veículos e Documentos (dados reais), páginas informativas | `COMPARACAO_LOTE5.md` |

Fora de âmbito (D7): Comfort, envio de documentos por foto, 112 e gravação de viagem. Dependem de backend ou do SDK de mapas: mapa real, rota,
navegação passo a passo, horas online e pontos, notificações e documentos com datas (ver `VALIDACAO.md`, divergências **B**).

## Camadas

- `config/` ambiente único; `net/` Retrofit + modelos (`endpoints.json`); `data/` sessão (DataStore), rede, `DriverRepository` (único ponto de acesso à API).
- `ui/home`, `ui/earnings`, `ui/discover`, `ui/inbox`, `ui/login`, `ui/manage` (segurança, veículos, documentos), `ui/settings`, `ui/tabs` (Menu).
- `drive/` proposta e viagem: `DriveViewModel` (sondagem a 4 s, o estado vem das `DriverTasks`), `DriveParser`, folhas do PIN e da avaliação, `SlideToConfirmView`.
- Regra: a lógica vive em ViewModels/mapeadores puros com testes; os Fragments só mostram o estado.

## Validar no telemóvel com o backend local

1. `BACKEND\.venv\Scripts\python server.py` (portas 8090/8091/8300; código de login `0000`).
2. `adb reverse tcp:8091 tcp:8091` e `AppConfig.environment = USB` (valor atual para os testes locais).
3. Contas do seed: motoristas `+351920000001` a `...006` (a `...006` tem documentos pendentes), passageiras `+351910000001` a `...003`.
4. No fim: parar o servidor e `adb reverse --remove tcp:8091`.
5. Trocar para `SERVER` antes de usar o servidor (`https://driver.qolari.com`); os 17 handlers do P6 ainda **não estão publicados** lá.

Testes que usam respostas reais do backend: `app/src/test/resources/drive/*.json`, geradas por `tools/gen_drive_fixtures.py` (BD temporária, não toca em nenhum servidor).

## Compilar

```bash
cd ANDOIRD/DRIVER/RECRIACAO
# Gradle 9 pede JDK 17+; o JAVA_HOME do sistema aponta para um JRE 11
JAVA_HOME="C:\Program Files\Eclipse Adoptium\jdk-21.0.12.101-hotspot" ./gradlew.bat assembleDebug testDebugUnitTest
```

APK: `app/build/outputs/apk/debug/app-debug.apk`. O SDK vem de `local.properties` (`sdk.dir`). A chave do Google Maps (`MAPS_API_KEY`, lote 2) também vai aí, nunca no código.

## Configuração única (spec FASE 4)

Tudo o que muda entre estágios está em `app/src/main/java/com/qolari/drivereplica/config/AppConfig.kt`:

| Ambiente | URL | Estágio do spec |
|---|---|---|
| `MOCK` | `http://10.0.2.2:8091` (emulador → `TESTE/backend/mock_server.py`) | 1. mock local |
| `USB` | `http://127.0.0.1:8091` (com `adb reverse`) | backend local no PC |
| `LAN` | `http://192.168.1.204` | 2. backend real em LAN |
| `SERVER` | `https://driver.qolari.com` | 3. servidor |

Para trocar de estágio, muda-se **uma linha**: `AppConfig.environment`. O teste `ConfigTest` falha se aparecer um host fora desse ficheiro.

## Ficheiros gerados (não editar à mão)

- `app/src/main/res/values/colors_core.xml` ← `../spec_tools/gen_theme.py` a partir de `../ui_spec/design_tokens.json`.

## Ferramentas (`tools/`)

- `gen_icons.py`: ícones vetoriais próprios (traço de 2dp). `gen_tabs.py`: ícones dos separadores (contorno/preenchido). `gen_drive_fixtures.py`: respostas reais do backend para os testes.
