# PROMPT — Auditoria da app USER (Qolari User Lite / passageiro)

**Data:** 2026-10-31 · **App:** `com.qolari.userlite` · **Telemóvel:** Mi 9T Pro `18a959c4`

---

## 0. O que te pedem

**Não é para implementar nada.** É para **auditar** a app do passageiro de ponta a ponta:
percorrer todos os ecrãs, carregar em todos os botões e escrever um relatório do que não
funciona, do que não faz nada, do que faz a coisa errada e do que está visualmente fora do
sítio.

No fim entregas `AUDITORIA_USER_2026-10-31.md` e **mostras ao cliente**. Não corriges nada
sem autorização.

---

## 1. Contexto

Estamos a recriar a **Uber** para a marca **Qolari**. Há três apps:

| App | Pacote | Estado |
|---|---|---|
| **Driver** | `com.qolari.drivereplica` | Fase 2 fechada (blocos A-D), auditada em separado |
| **User (passageiro)** | `com.qolari.userlite` | ⬅ **o teu alvo** — fluxo até ao pedido funciona |
| Fleet | `com.qolari.fleet` | não é teu âmbito |

O backend é o mesmo para as duas: **8090 = Rider/User**, **8091 = Driver**.

### O que já se sabe que funciona (não percas tempo a redescobrir)

Segundo o `PROMPT_RIDER_PEDIDO.md`, o fluxo até ao pedido está fechado:

```
home → "Para onde?" → "Defina a localização no mapa" → arrastar o pino
→ "Confirmar destino" → categorias → "Escolher <produto>"
→ "Confirme o ponto de recolha" → "Confirmar recolha"
→ POST /rt/riders/{uuid}/v2/pickup → viagem criada
```

**O que NÃO se sabe:** tudo o resto. É aí que está o valor desta auditoria.

---

## 2. Montar o ambiente

```powershell
# base
cd "C:\xampp\htdocs\QOLARI\PROJETOS OFICIAIS\QOLARI DRIVER"

# backend (8090 = User, 8091 = Driver)
cd BACKEND
Start-Process .\.venv\Scripts\python.exe -ArgumentList "server.py" -WindowStyle Hidden

# build e instalar a app User
$env:JAVA_HOME="C:\Program Files\Android\Android Studio\jbr"
cd ..\ANDOIRD\USER_LITE\RECRIACAO
.\gradlew.bat assembleDebug --offline
adb -s 18a959c4 install -r --no-streaming app\build\outputs\apk\debug\app-debug.apk

# reverses — caem MUITO, repor sempre
adb -s 18a959c4 reverse tcp:8090 tcp:8090
adb -s 18a959c4 reverse tcp:8091 tcp:8091

# captura (o redirect directo do PowerShell corrompe o PNG)
cmd /c "adb -s 18a959c4 exec-out screencap -p > C:\Users\Miglo\AppData\Local\Temp\opencode\user.png"
```

**Telemóvel:** só o **Mi 9T Pro** (`18a959c4`), 1080×2340, density 440 (escala 2.75).
O Honor `AQCK024C17020494` é de outra sessão — **não mexer**.

### Login

- Backend em `Environment.USB` → `http://127.0.0.1:8090` (já é o default em
  `config/AppConfig.kt`).
- **Código OTP:** `0000` (ver `BACKEND/config.py`, `OTP_CODE`).
- **Passageiros do seed** (`BACKEND/domain/seed.py`):

| Nome | Telefone | Notas |
|---|---|---|
| Ana Pereira | `+351910000001` | tem histórico |
| Bruno Santos | `+351910000002` | cartão como pagamento por omissão |
| Carla Nunes | `+351910000003` | |

Para testar **viagem com motorista a aceitar**, corre o script do Driver em paralelo:
`C:\Users\Miglo\AppData\Local\Temp\opencode\teste_final_mi.ps1` (cria viagem no Rider e
aceita no Driver). **Não uses o mesmo telemóvel para as duas apps ao mesmo tempo** — usa o
script por API e observa o User no ecrã.

---

## 3. Ecrãs a percorrer

Estão todos em
`ANDOIRD/USER_LITE/RECRIACAO/app/src/main/java/com/qolari/userlite/ui/`:

| Ecrã | Ficheiro | O que testar |
|---|---|---|
| **Welcome** | `welcome/WelcomeFragment.kt` | Botão "Começar" → login |
| **Login telefone** | `login/LoginPhoneFragment.kt` | Teclado, prefixo, erros, número inválido |
| **Login código** | `login/LoginCodeFragment.kt` | `0000` certo, código errado, reenvio |
| **Home** | `home/HomeFragment.kt` | Barra "Para onde?", menu, zoom +/-, localizar, promoções, mapa |
| **Search** | `search/SearchFragment.kt` | Pesquisa de destino, sugestões, pino |
| **Ride options** | `ride/RideOptionsFragment.kt` | Categorias, preços, pagamento, "Confirmar recolha" |
| **Active trip** | `ride/ActiveTripFragment.kt` | Estado da viagem, PIN, contacto, cancelar |
| **Menu** | `menu/MenuFragment.kt` | 6 atalhos + "Terminar sessão" |
| **Wallet** | `wallet/WalletFragment.kt` | Saldo, adicionar pagamento, levantar |
| **Activity** | `activity/ActivityFragment.kt` | Histórico, detalhe de viagem |
| **Promotions** | `promotions/PromotionsFragment.kt` | Códigos promo, aplicar |
| **Help** | `help/HelpFragment.kt` + `HelpTopicFragment` | Categorias, tópicos |
| **Legal** | `legal/LegalFragment.kt` + `LegalTopicFragment` | Documentos |
| **Account** | `account/AccountFragment.kt` | Editar dados |

---

## 4. Checklist de falhas

Procura activamente por:

1. **Botões mortos** — carregas e não acontece nada.
2. **Botões que fazem a coisa errada** — abrem outro ecrã, navegam mal.
3. **Botões tapados** — outro elemento por cima.
4. **Texto a `null` / vazio** — campos sem dados, "null", "0,00 €".
5. **Texto cortado** — reticências, sobreposição de linhas.
6. **Ecrãs que não voltam** — o retroceder fecha a app.
7. **Estados presos** — spinner infinito, ecrã que não actualiza.
8. **Cores/formas fora do sítio** — algo que destoa.
9. **Dados inventados** — números que o servidor não mandou.
10. **Crashs** — `adb -s 18a959c4 logcat -d | Select-String "FATAL|AndroidRuntime"`

### Pontos de atenção específicos desta app

- **Polling:** `TRIP_POLL_INTERVAL_MS = 2_000` — a viagem actualiza de 2 em 2 s? Fica a
  martelar o servidor quando a app está em segundo plano?
- **Offline:** existe um `offlineBanner` no `activity_main.xml`. Aparece e desaparece bem
  quando se desliga a rede? (`adb shell svc wifi disable` / `enable`)
- **Cancelamento de viagem:** há botão? Funciona? O servidor fica consistente?
- **PIN:** o `ActiveTripFragment` mostra o PIN ao passageiro? O motorista consegue validá-lo?
  (Testa a dois tempos com o script do Driver.)
- **Histórico:** o Activity mostra viagens antigas com valores certos?
- **Wallet:** o saldo que mostra corresponde ao servidor?
- **Sign out:** limpa a sessão mesmo? Ao voltar a abrir pede login?

---

## 5. Regras do projecto (não negociáveis)

- **Nunca inventar dados.** Google Maps + Directions. Nada de ruas ou rotas desenhadas à mão.
- **Não inventar ecrãs nem botões.** Se não está no original, perguntar.
- **UI em português de Portugal**, tom Uber.
- **Não apagar trabalho do utilizador** nem APKs sem confirmar.
- **Backend não se mexe** nesta auditoria — só reportar.
- **Não enviar para o GitHub** sem o cliente aprovar.
- `ConfigTest` impõe **zero hosts hardcoded fora do `AppConfig`**. Se encontrares um, é falha.

---

## 6. Formato do relatório

Cria `AUDITORIA_USER_2026-10-31.md` na raiz do projecto:

```markdown
# Auditoria — QOLARI User
Data · Telemóvel · Commit

## Resumo
- N ecrãs percorridos · N botões testados
- N falhas (X críticas, Y médias, Z cosméticas)

## Fluxo testado
<diagrama curto do que conseguiste percorrer>

## Falhas

### F-01 · <título curto>
- **Onde:** <ecrã> → <botão>
- **Esperado:** …
- **Observado:** …
- **Passos:** 1. … 2. … 3. …
- **Gravidade:** crítica / média / cosmética
- **Prova:** <caminho da captura>
- **Suspeita:** <ficheiro:linha, se souberes>

### F-02 · …

## Botões que funcionam
<lista, para se saber o que já está validado>

## Não foi possível testar
<o que ficou por testar e porquê>
```

**Uma falha por entrada.** Sem juntar problemas.

---

## 7. Ordem sugerida

1. Ler este prompt e o `PROMPT_RIDER_PEDIDO.md`.
2. Subir backend, confirmar reverses.
3. **Login** com `+351910000001` / `0000` — se falhar, pára e reporta (bloqueia tudo).
4. Percorrer **todos os ecrãs do Menu** (wallet, activity, promoções, ajuda, legal, conta).
5. Voltar ao home → **fluxo completo de pedido** até "Confirmar recolha".
6. Com a viagem criada, correr o script do Driver para o motorista aceitar e observar o
   **Active trip** do lado do passageiro.
7. Testar **cancelamento** e **fim de viagem**.
8. Testar **offline** (desligar wifi/dados).
9. Escrever o relatório **enquanto testas**.

---

## 8. Estado dos testes (baseline)

```
User (unit) ...... 9 testes (ContractTest 7 + MapCameraTest 2)
Backend .......... 92 passed
```

Se algum número estiver diferente, **pára e investiga**.

---

## 9. Ficheiros-chave

| Ficheiro | O que contém |
|---|---|
| `ui/home/HomeFragment.kt` | Ecrã inicial, mapa, barra de pesquisa |
| `ui/search/SearchFragment.kt` | Destino, sugestões |
| `ui/ride/RideOptionsFragment.kt` | Categorias, preço, pagamento |
| `ui/ride/ActiveTripFragment.kt` | Viagem em curso, PIN, contacto |
| `ui/ride/RideViewModel.kt` | Estado do pedido |
| `ui/menu/MenuFragment.kt` | Menu com os 6 atalhos |
| `ui/wallet/WalletFragment.kt` | Carteira e pagamentos |
| `data/UserRepository.kt` | Chamadas ao servidor |
| `net/UserApi.kt` | Contrato HTTP |
| `config/AppConfig.kt` | Hosts e intervalos de polling |
| `BACKEND/apps/rider.py` | Contrato do lado do servidor |
| `BACKEND/domain/seed.py` | Passageiros, motoristas, promoções |

---

## 10. Um aviso

A app User **nunca foi auditada**. Espera encontrar mais problemas aqui do que na Driver.

Duas coisas prováveis de estar mal, para estares atento:

1. **Estados de viagem** — a Driver acabou de mudar (pausa de pedidos, novos botões). O User
   pode não reagir a essas mudanças.
2. **Polling em segundo plano** — `TRIP_POLL_INTERVAL_MS = 2_000` sem ciclo de vida pode
   estar a gastar bateria e rede mesmo com a app minimizada.

---

**Regra final:** o cliente prefere **uma falha bem descrita** a dez corrigidas à pressa.
Testa com calma e escreve com precisão.
