# DEPLOY.md — do laboratório para produção

O alvo atual é `funcional` (local). Este documento é o caminho para `produção`, não uma
promessa de que já está tudo pronto. Os pontos marcados **bloqueado** exigem contas,
credenciais, hardware ou decisão de produto.

## 1. PostgreSQL e migrações

```bash
sudo -u postgres psql -c "create user qolari with password 'TROCAR';"
sudo -u postgres psql -c "create database qolari owner qolari;"
cd BACKEND
export DB_URL="postgresql+psycopg://qolari:TROCAR@127.0.0.1:5432/qolari"
.venv/bin/alembic upgrade head
```

`alembic` está em `BACKEND/alembic.ini` + `migrations/`. A baseline `0001_baseline` cria
o esquema atual; as próximas alterações devem ser `alembic revision --autogenerate` e
revistas à mão. O `downgrade` da baseline é no-op de propósito.

## 2. Variáveis de ambiente

Copiar `deploy/qolari.env.example` para `/etc/qolari/qolari.env`, `chmod 600`, e preencher.
Com `ENVIRONMENT=production`, o `server.py` chama `config.validate_production()` e recusa
arrancar com defaults de laboratório (SECRET, admin/admin, SQLite, STRICT_AUTH=0,
RATE_LIMIT=0, OTP 0000, localhost, sem chave Google).

Pontos de atenção:

- `BIND_HOST=127.0.0.1` — o backend fica atrás do nginx, não exposto diretamente.
- `EXTRA_APP_PORTS=""` — a 80 é do nginx, não do backend.
- `PUBLIC_HOST=driver.qolari.com` — só para apresentação na consola.
- `GOOGLE_MAPS_KEY` — geocoding/rotas; a chave das apps continua em `local.properties`.
- `ROUTING_URL` — OSRM self-host ou o demo público; com tráfego, self-host.
- `OTP_CODE` — **bloqueado**: o login real por SMS ainda não existe. Não dá para lançar
  produção só mudando este valor; a app tem de gerar/pedir um código real.

## 3. Serviço systemd

Copiar `deploy/qolari.service` para `/etc/systemd/system/qolari.service`, ajustar
`User`/`WorkingDirectory` e:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now qolari
curl -fsS http://127.0.0.1:8300/api/health | jq
```

O health devolve `ok`, `db`, `environment` e `uptime_s`. Um probe de readiness deve
falhar se `ok=false`.

## 4. nginx e TLS

Usar `deploy/nginx.conf.example` como base; certificados Let's Encrypt:

```bash
sudo certbot --nginx -d driver.qolari.com -d rider.qolari.com \
  -d fleet.qolari.com -d admin-driver.qolari.com
```

O `proxy_read_timeout` é 120 s por causa do `ramen` (long-poll). Limitar o acesso à
consola por VPN/IP allowlist se possível.

## 5. Backups

```bash
cd BACKEND
.venv/bin/python tools/backup.py --dest /var/backups/qolari --keep 14
```

SQLite usa a API de backup online; PostgreSQL usa `pg_dump`. Agendar no cron e testar
a restauração num ambiente separado. Backups fora do servidor (S3/rsync) são obrigatórios.

## 6. Release Android / loja — bloqueado

- `ANDOIRD/DRIVER/RECRIACAO` e `USER_LITE/RECRIACAO` têm configuração de assinatura
  opcional por `local.properties` (`RELEASE_STORE_FILE`, `RELEASE_STORE_PASSWORD`,
  `RELEASE_KEY_ALIAS`, `RELEASE_KEY_PASSWORD`). Sem keystore, o `assembleRelease` fica
  não assinado.
- Play Console, política de privacidade, Data Safety e revisão legal: ver
  `PRIVACIDADE.md` e `DATA_SAFETY.md`. **Bloqueado** sem conta/keystore/legal.
- A chave Google Maps deve ser restringida por pacote + SHA-1 de release (ver README).

## 7. Push em background ? implementado

Driver e Rider usam FCM no projeto `qolari-driver-prod`; a conta de servi?o fica em
`BACKEND/data/firebase-service-account.json` (ignorada). Ver `PUSH_FCM.md`.

## 8. Fleet e iOS

- **Fleet visual**: não há recriação própria; a operação está no backend/backoffice. É uma
  decisão de produto (ver `plan.md` §8).
- **iOS**: fora do âmbito; sem macOS/Xcode neste ambiente.

## 9. CI

`.github/workflows/ci.yml` corre backend, `spec_check`, backoffice e os testes unitários
das duas apps. Não corre testes instrumentados; para isso é preciso um emulador/device
com Google Play Services.

## 10. Deploy Hetzner — estado em 2026-10-26

O laboratório está publicado em:

| Endereço | O que serve |
|---|---|
| `https://driver.qolari.com` | API da app Driver; `/` redireciona para a consola |
| `https://rider.qolari.com` | API da app Rider |
| `https://admin-driver.qolari.com` | backoffice (React + `/api`) |
| `https://fleet.qolari.com` | API da Fleet |
| `https://qolari.com/pt/marketplace/qolaridriver` | página de marketplace; “Painel Admin” abre a consola |

**Serviço:** `systemd qolari-driver` → `/opt/qolari-driver/BACKEND`, env
`/etc/qolari-driver.env`, porta de consola `8300`.

**Acesso demo da consola:** `admin@qolari.com` / `QolariDriver@2026`
(criado na BD em 26/10; mudar em Conta). O login antigo `admin@qolari.local`
já não é o anunciado.

**Base de dados:** SQLite em `/opt/qolari-driver/BACKEND/data/qolari.db`;
backup antes do deploy em `/root/qolari-driver-qolari.db.bak-2026-10-26`.
Foram acrescentadas as colunas `trips.scheduled_at`, `trips.stops`,
`trips.tip_cents` e `riders.wallet_cents`; as tabelas novas são criadas pelo
`create_all` no arranque.

**APKs do marketplace:** substituídos em
`/var/www/qolari/frontend/.next/standalone/public/marketplace/qolaridriver/`
(Driver e Rider, builds de 26/10, a apontar para `https://driver.qolari.com`
e `https://rider.qolari.com`). Cópias antigas em
`/root/qolari-marketplace-apks-2026-10-26/`.

**Nota:** continua `ENVIRONMENT=lab`, OTP `0000` e SQLite. Para `produção`
ver os pontos bloqueados nas secções 1–4 acima (PostgreSQL, OTP real, TLS
restrito, backups externos).


