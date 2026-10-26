# Lote 3 - Descobrir, Rendimentos, Caixa de entrada: recriação vs. original

Dispositivo PTP-N49, pacote `com.qolari.drivereplica`, backend local por USB (`adb reverse tcp:8091 tcp:8091`).
Capturas em `captures/lote3/`; folhas lado a lado (original à esquerda): `cmp_A.png` (Descobrir, Rendimentos, Caixa) e `cmp_B.png` (Rendimentos com scroll, Apoio, sem rede).

## O que foi feito (toolkit da evidência: `ux_capture/toolkit_por_ecra.csv`)
| Separador | Toolkit | Original | Recriação |
|---|---|---|---|
| Descobrir (`DiscoverFragment`) | Views | 010, 036, 061, 080, 081 | 40, 43, 44, 45 |
| Rendimentos (`EarningsFragment`) | Views | 011, 062, 116, 122, 126 | 41, 46 (scroll), 48 (sem rede) |
| Caixa de entrada (`InboxFragment`) | Compose | 012, 063 | 42, 47 (Apoio) |

- **Rendimentos** usa dados reais do backend: total e viagens da semana (`get-weekly-earnings-view`), saldo (`get-balance-summary`).
  As barras por dia calculam-se no telemóvel a partir das viagens. Arrastar para atualizar sem rede mantém o que está no ecrã (captura 126);
  sem dados e sem rede mostra "Sem ligação de rede" (captura 122).
- **Descobrir** (conteúdo de exemplo): faixa de 14 dias fixa com o dia que acompanha o scroll, toque num dia salta para ele; filtros
  Lembretes/Promoções/Aeroportos (cinzentos desligados, pretos ligados; sem nenhum ligado vê-se tudo, ligados mostram só essas categorias);
  cartões de promoções com pontos; eventos com "Guardar".
- **Caixa de entrada** (Compose): separadores Notificações (com contador) e Apoio; lista com não lidas a negrito e ponto azul.
- **Barra de separadores**: contador na Caixa de entrada e ponto no Menu (capturas 000/060). Valores de exemplo.

## Comportamento coberto por teste (`Lote3Test`, 13 testes; suite total 35)
Formato de dinheiro, resumo por dia, destaque do dia de hoje, falha sem dados vs. com dados, filtros de Descobrir (aeroportos, promoções, lembretes, repor),
dia selecionado, datas em português ("Sexta-feira, 16/Out"), contador da Caixa de entrada.

## Erros encontrados e corrigidos
1. Rótulo da semana um dia antes na semana da mudança de hora: o servidor calcula o fim como início + 7x86400 s; o ecrã usa o último instante
   da semana (fim - 1 ms). **Sugestão para o backend:** calcular o fim da semana por data de calendário, não por segundos.
2. Barras todas à altura máxima numa semana sem valores: escala mínima de 1 e altura mínima de 3dp.
3. Títulos longos das notificações cortavam sem reticências.

## Diferenças que ficam (e porquê)
- **Rendimentos**: não há "Online" (horas) nem "Pontos" como na original: o backend não os tem (D7: sem valores inventados). "Ver detalhes" leva à lista de
  viagens da semana (a original abre o seletor "Abrir com"). As secções de baixo (desafio, nível, mais formas de ganhar) são de exemplo.
- **Descobrir**: o título e a faixa de dias ficam fixos e os filtros e as promoções fazem scroll com a lista (na original os filtros ficam entre o título e a faixa de dias, e os dias passados aparecem esbatidos). Eventos e promoções são de exemplo (a original traz-os de um serviço de recomendações). Miniaturas de mapa desenhadas.
- **Caixa de entrada**: notificações de exemplo (a original tem o seu serviço); o contador mostra os não lidos da lista. Ícone de arquivo genérico.
- Fonte e ícones próprios (D4).

## Validado no telemóvel
Todas as capturas acima foram feitas no PTP-N49 com o backend local, incluindo a correção da semana (19/10 - 25/10), o gráfico de uma semana sem valores e o estado sem servidor.
Ao fechar: backend local parado, `adb reverse` removido, o motorista de teste Carlos (seed) reposto online (um teste inicial tinha-o posto offline).
O ambiente da app continua em `USB` (`AppConfig.environment`) para os testes locais.
