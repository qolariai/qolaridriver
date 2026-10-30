# Qolari Mobility — backend local (Rider + Driver + Fleet)

Um processo Python (FastAPI + SQLite) que serve as 3 APKs da família Qolari e a consola de operação.
Desenhado a partir do contrato extraído destas APKs (`contracts/`), não de outros projetos.

| App | APK | Endereço gravado na APK | Porta aqui |
|---|---|---|---|
| Qolari Driver | `../DRIVER/qolari-drive.apk` (`com.qolari.driver`) | `http://192.168.1.204` | 80 |
| Qolari Rider | `../USER/final_apks` (`com.qolari.rider`) | `http://192.168.1.204:8090` | 8090 |
| Qolari Fleet | `../FLEET/QolariFleet.apk` (`com.qolari.fleet`) | `http://192.168.1.204:3000` | 3000 |
| Consola (backoffice) | `../BACKOFFICE` (React) | — | 8300 → <http://127.0.0.1:8300> |

A app é identificada pela **porta local** onde o pedido entra (não pelo `Host`).

## Arrancar

```bat
iniciar.bat
```
ou `.venv\Scripts\python server.py`. Consola: <http://127.0.0.1:8300> — `admin@qolari.local` / `admin` (muda em Conta).
Se o Apache do XAMPP estiver ligado, a porta 80 fica ocupada: o servidor avisa e continua sem a app Driver.

Instalar de raiz:
```bat
uv venv .venv --python 3.14
uv pip install --python .venv\Scripts\python.exe -r requirements.txt
cd ..\BACKOFFICE && npm install && npm run build
```

### Ligar os telemóveis
1. O PC tem de ter o IP **192.168.1.204** na rede do telemóvel (está gravado nas APKs). No Wi-Fi de casa, reservar este IP no router; senão é preciso recompilar as APKs com o IP novo.
2. A firewall do Windows tem de aceitar ligações de entrada nestas portas. Numa PowerShell **como administrador** (só a rede local):
   ```powershell
   New-NetFirewallRule -DisplayName "Qolari backend" -Direction Inbound -Protocol TCP -LocalPort 80,3000,8090 -RemoteAddress LocalSubnet -Action Allow -Profile Any
   ```
   (Para desfazer: `Remove-NetFirewallRule -DisplayName "Qolari backend"`.)
3. Login nas apps: o telemóvel de uma conta e o código **0000** (`OTP_CODE`).

Contas de teste (seed): Rider `+351910000001` Ana · `+351910000002` Bruno · `+351910000003` Carla — Driver `+351920000001` Carlos (Frota Tejo) · `+351920000004` Diana (independente) · `+351920000006` Inês (por aprovar) — Fleet `+351930000001` Rui (Frota Tejo) · `+351930000002` Sofia (Lisboa Drive Partners). Código promocional `BEMVINDO`.

## Estrutura

| Pasta | O quê |
|---|---|
| `server.py` / `main.py` | Abre as 4 portas num só processo; encaminha por porta; relógio de 1 s (`trips.tick`) |
| `domain/` | Modelo (`models.py`), **máquina de estados + despacho + liquidação** (`trips.py`), tarifas (`pricing.py`), saldos e pagamentos (`finance.py`), parâmetros (`settings.py`), fila de mensagens para as apps (`push.py`), seed |
| `apps/rtapi.py` | Protocolo das APKs (`/rt/...`): registo `@handles(app, método, path)`, token em `x-uber-token` / `x-qolari-token` / Bearer, erros `{"code":"rtapi.x","message"}`, resposta `{}` + registo para o que não tem handler |
| `apps/identity.py` | Login web (`/v2`, a WebView das apps) → `redirect_uri?code=` → `POST /rt/identity/oauth2/token`; sessões, dispositivos |
| `apps/rider.py`, `driver.py`, `fleet.py`, `userlite.py` | Tradução domínio → modelos de cada APK (o docstring diz de onde saiu o contrato); `userlite.py` é contrato `designed` da Rider Lite |
| `apps/common.py` | Canal `ramen` (long-polling de mensagens), conta do utilizador, consentimentos |
| `apps/catalog.py` + `contracts/` | Catálogo de endpoints e modelos extraídos de cada APK (Rider 1055 endpoints/1894 modelos, Driver 1053 paths/2022 modelos, Fleet 647/527) |
| `console/` | API da consola `/api/*` (papéis admin / operator / finance, registo de ações) e página Integração |
| `tools/extract_models.py` | Extrai modelos (classe → campos) do smali: `python tools/extract_models.py <raiz smali> <saida.json> <pastas...>` |
| `tests/` | Ciclo completo pelas 3 apps + consola e teste dos três espelhos: `.venv\Scripts\python -m pytest -q tests` (54 testes) |

## Domínio

Viagem (`Trip.state`): `requested → accepted → arrived → in_progress → completed`, mais `cancelled` e `no_drivers`.
Despacho: uma proposta (`Offer`) de cada vez ao motorista aprovado, online, com veículo ativo da categoria, mais perto da recolha (dentro de `dispatch_radius_km`); recusa/expira (`offer_timeout_s`) → seguinte; sem ninguém durante `search_timeout_s` → `no_drivers`.
Liquidação na conclusão: motorista `+tarifa −comissão −taxa de frota (−dinheiro recebido)`, frota `+taxa`, plataforma `+comissão −promoção`. Saldo positivo = a plataforma deve; pagamentos na consola (Finanças).
Cancelamento do passageiro depois de `rider_free_cancel_s` com motorista atribuído paga `cancel_fee` ao motorista.

**Orquestração (MEGA §4.6):** `domain/trips.py` é o **único** escritor do estado da
viagem. O backoffice não escreve na base de dados: chama as mesmas transições
(`/api/trips/{key}/action`) e deixa auditoria. Cada transição publica `trip_status`
para Rider/Driver/Fleet e `driver_trip`/`driver_status` para a Fleet. O teste dos três
espelhos está em `tests/test_espelhos.py`. Ver `../topology.md` §8.

## Estado do contrato com as APKs (ler antes de testar no telemóvel)

Os handlers seguem os nomes de campo dos modelos das APKs, mas **ainda não foram validados com as apps reais**:
falta abrir cada app no telemóvel e ajustar. Fluxo de trabalho:

1. Abrir a app → consola **Integração → app → Ao vivo** mostra cada pedido, o handler usado e a resposta.
2. **Por mapear** = pedidos que receberam `{}`; o detalhe mostra a operação e o **modelo de resposta esperado** (campos navegáveis).
3. Escrever o handler em `apps/<app>.py` com `@handles(...)`, um teste em `tests/`, reiniciar o servidor.

Pontos mais incertos: o fluxo exato de login (parâmetros da WebView `/v2` e do `/token`), os valores de `RideStatus` do Rider (`Looking`/`Dispatching`/`WaitingForPickup`/`OnTrip`), a forma das tarefas `DriverTasks` do Driver (proposta e recolha) e o canal de tempo real `ramen`.
Algumas apps podem também recusar arrancar por verificação de integridade/assinatura — isso é da APK, não do backend.

## Configuração (variáveis de ambiente, `config.py`)

`DRIVER_PORT`, `RIDER_PORT`, `FLEET_PORT`, `EXTRA_APP_PORTS` (portas extra `porta=app`; por omissão `80=driver` para a IPA iOS, que usa `http://192.168.1.9` sem porta), `CONSOLE_PORT`, `DB_URL` (SQLite em `data/qolari.db`; MySQL do XAMPP com `mysql+pymysql://...`), `OTP_CODE`, `SECRET`, `STRICT_AUTH=1` (pedido sem token válido → 401; por omissão usa o 1.º utilizador do seed), `ADMIN_EMAIL`/`ADMIN_PASSWORD` (só com a BD vazia), `POLL_HOLD_S`, `RUN_TICKER`.
Parâmetros de negócio (comissão, raio, tempos, simulação) mudam-se na consola → Definições.
Apagar `data/qolari.db` recria tudo do seed no arranque seguinte.

Logs: `logs/<app>/AAAA-MM-DD.log` (um pedido por linha + body).
