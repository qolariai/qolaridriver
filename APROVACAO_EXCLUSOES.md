# APROVACAO_EXCLUSOES.md — decisão escrita do cliente

**Data:** 2026-10-30 · **Âmbito:** app Driver (`com.qolari.drivereplica`) ·
**Programa:** `PROMPT_CLONE_MEGA.md` FASE 4.7 / 7.3

O MEGA exige **aprovação escrita do cliente** para que uma funcionalidade do
original passe a `excluído`. Sem esta linha, o item continua `gap` e o projeto
não fecha. Este ficheiro é essa aprovação.

## 1. Exclusões aprovadas

Aprovadas na sessão de 2026-10-30, com a consequência declarada em cada linha.

| # | Funcionalidade (original) | Captura / evidência | Porque fica fora | UI no clone | Como fica |
|---|---|---|---|---|---|
| X-01 | Gravação de vídeo do interior do veículo | `022_gravacao_video.png`, `ub__audio_video_app_settings_screen.xml` | Depende de câmara em foreground service + armazenamento de terceiros; sem serviço de media próprio | entrada ausente | `excluído` |
| X-02 | Vídeo de boas-vindas | `026_video_boas_vindas.png`, `exo_player_view.xml` | Player de terceiros + conteúdo vídeo proprietário | entrada ausente | `excluído` |
| X-03 | Comfort — próximos passos | `027_comfort_proximos_passos.png` | Produto Comfort não existe no ecossistema Qolari | entrada ausente | `excluído` |
| X-04 | Comfort — lição 1 | `028_comfort_licao_1.png` | idem | entrada ausente | `excluído` |
| X-05 | Comfort — lição 2 | `029_comfort_licao_2.png` | idem | entrada ausente | `excluído` |
| X-06 | Comfort — normas de serviço | `030_comfort_normas_servico.png` | idem | entrada ausente | `excluído` |
| X-07 | Login por e-mail | `033_login_email.png` | Decisão de produto: login nativo por telefone (`0000` no laboratório) | entrada ausente | `excluído` |
| X-08 | Adicionar veículo (fluxo de registo) | `081_veic_adicionar.png` | Frota do laboratório tem veículos fixos no seed; registo de veículo novo exige backoffice | entrada ausente | `excluído` |

**Total:** 8 funcionalidades excluídas.

## 1.1 Âmbito de produto (X-09) — verticais a bordo do binário

Aprovado na mesma sessão de 2026-10-30.

| # | Item | Evidência | Porque fica fora | Como fica |
|---|---|---|---|---|
| X-09 | Verticais de produto que o binário transporta mas o ecossistema Qolari não tem: courier/Eats, rental, refueling, vouchers, mentorship/quests, Uber for Business, banco/UPI/Zaakpay, eKYC/selfie, vídeo/áudio, social/referrals, reservas, pontos de acesso, design system interno (Firefly/Penny) | Driver: **1 823 strings**; Rider: **1 035 strings** (§3.5 dos dois `features.md`) | São **outros produtos** no mesmo binário, não funcionalidades da app Driver. Implementá-los é construir o Uber inteiro, não clonar estas duas apps | `excluído` por âmbito; nunca foram UI do clone |

**Consequência:** as verticais saem do `features.md` §3.5 como `em falta` e passam
a `excluído` por âmbito. O `backlog.md` G-07 fecha.

**Nota de honestidade:** se o cliente mudar de ideias e quiser uma vertical
(ex.: Eats), esta exclusão caduca e a vertical entra como inventário próprio —
com os layouts, endpoints e capturas dela, não com estas 1 823 strings.

## 2. Consequências

1. As 8 linhas entram em `features.md` com `status = excluído` e a referência
   `X-0n` nesta tabela.
2. Não contam como `gap` no `backlog.md`.
3. Nenhuma delas tem botão, atalho, placeholder ou string "em breve" na app.
   O `grep` de fecho (`tools/spec_check.py`) tem de continuar vazio.
4. Se alguma voltar à UI, a exclusão caduca e a linha volta a `gap`.

## 3. O que NÃO está aprovado

Estas continuam a ser **trabalho a fazer** — não são exclusões:

| Item | Motivo |
|---|---|
| Contagem decrescente e som na oferta | É comportamento do original e a app já mostra a oferta |
| Partilha de viagem / acompanhar viagem | Depende de `ACTION_SEND` do sistema, que é implementável |
| Atalhos das "ações necessárias" para Definições do Android | `Settings.ACTION_*` é implementável |
| Menu → Seguro | Página própria informativa, sem dependência externa |
| Comprovativo de estado da viagem | Conteúdo próprio, sem dependência externa |

Estas cinco fecham por implementação, não por exclusão.

## 4. Assinatura

```
Aprovado por: cliente (sessão de 2026-10-30)
Registado por: agente
Itens: X-01 a X-08
Condição: entrada de UI removida + grep de fecho vazio
```
