# backlog.md — gaps priorizados (FASE 7)

**Alvo:** `funcional`. **Estado:** zero itens abertos que bloqueiem o alvo no
âmbito Driver + Rider + backend + backoffice. A validação no telemóvel Honor é
execução de teste, não um gap de produto.

| id | área | ecrã/fluxo | razão | bloqueia | esforço | dono | estado |
|---|---|---|---|---|---|---|---|
| R-01 | Rider | Início: zoom | os botões mostravam “Ampliar/Reduzir” sem mudar o mapa | demo/opera | S | app Rider | fechado — `MapCamera` + `MapCameraTest` |
| R-02 | Rider | Início: localização | o botão só mostrava um aviso | demo/opera | M | app Rider | fechado — permissão, `LocationManager`, `POST /rt/lite/location` |
| R-03 | Rider | Início: sugestões | “Entrega/Reserve/Envie” abriam “Em breve” | demo/opera | S | app Rider/backend | fechado — entradas removidas; só “Viajar” |
| R-04 | Rider | Início: promoções | um cartão abria a procura, outro o “Em breve” | demo/opera | S | app Rider | fechado — ambos abrem promoções |
| R-05 | Rider | Login: reenviar | botão só mostrava um aviso | demo/opera | S | app Rider | fechado — preenche `0000` |
| R-06 | Rider | Pesquisa: paragens/mapa/cidade/agora/pessoas | cinco entradas só mostravam avisos | demo/opera | M | app Rider | fechado — entradas removidas; ficou “casa guardada” funcional |
| R-07 | Rider | Escolher viagem: chips | “Agora/Para mim” só mostravam avisos | demo/opera | S | app Rider | fechado — removidos |
| R-08 | Rider | Carteira: adicionar pagamento | simulava um pagamento sem efeito | demo/opera | S | app Rider | fechado — escolhe entre os perfis reais |
| R-09 | Rider | Atividade: filtro | mudava o rótulo mas não filtrava | demo/opera | S | app Rider | fechado — removido (não há perfil empresa) |
| R-10 | Rider | Gerir conta | página “informativa” sem edição | demo/opera | L | app Rider/backend | fechado — casa, dados, segurança, privacidade, verificação |
| R-11 | Backend | Conta Rider | não havia escrita para casa/dados | demo/opera | M | backend | fechado — `PATCH /rt/lite/account`, `POST /rt/lite/account/home`, 2 testes |
| D-01 | Driver | Menu: Descobrir/Pro/Hub/Recomendações | linhas com seta e sem destino | demo/opera | S | app Driver | fechado — navegação para Descobrir ou página própria |
| D-02 | Driver | Strings de páginas próprias | informação em falta para as linhas novas | demo/opera | S | app Driver | fechado — `info_pro/work/referrals` |
| V-01 | Telemóvel | Driver + Rider no Honor | ciclo completo no dispositivo final | opera | M | operador | fechado — ciclo completo em 27/10 (login, oferta, PIN, fim, avaliação dos dois lados) |
| R-12 | Rider | Avaliação do motorista | Retrofit rejeitava `Map<String, *>` antes de sair do telefone | demo/opera | S | app Rider | fechado — `RateRequest` + teste no Honor |
| R-13 | Rider | Pesquisa | pickup continuava “Casa, Lisboa” depois de mudar a casa | demo/opera | S | app Rider | fechado — pickup e etiqueta vêm da casa atual |
| D-03 | Driver | Fim da viagem | a folha de avaliação voltava a abrir depois de Enviar | demo/opera | S | app Driver | fechado — `MapFragment` + `RatingSheet` fecham quando o stage sai de RATING |
| B-02 | Backend | Ganhos | “Frota Frota Tejo, Lda.” duplicado | demo/opera | S | backend | fechado — “Taxa de frota (…)”; avaliação 0 = saltar |

## Gaps abertos

Nenhum para `funcional` no âmbito declarado.

## Fora do alvo (tolerância escrita)

- UI própria da Fleet (operação coberta por backend/backoffice).
- Mapa real/OSRM, FCM, 112, foto de documentos, login social, IAP.
- iOS.

Estas linhas não são botões na UI; estão em `capabilities.md` §5 e `plan.md` §8.
