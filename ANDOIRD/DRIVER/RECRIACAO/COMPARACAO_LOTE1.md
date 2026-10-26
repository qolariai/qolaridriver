# Lote 1 - Menu e Definições: recriação vs. original

Dispositivo PTP-N49, pacote `com.qolari.drivereplica`. Capturas em `captures/lote1/` (PNG + dump XML);
folhas lado a lado (original à esquerda, recriação à direita): `cmp_A.png` a `cmp_D.png` (1ª passagem), `cmp_final.png` (final).

## Ecrãs feitos (toolkit igual ao da original, `ux_capture/toolkit_por_ecra.csv`)
| Ecrã | Toolkit | Original | Recriação |
|---|---|---|---|
| Menu (064) | Views | 064_menu | 10_menu |
| Definições (043) | Compose | 043 | 11_definicoes |
| Acessibilidade (044) | Compose | 044 | 12_acessibilidade |
| Audição (049) | Compose | 049 | 13_audicao |
| Comunicação (045) + folha push (051) | Views | 045/051 | 14/15 |
| Navegação (046) | Views | 046 | 16 |
| Sons e Voz (047) | Compose | 047 | 17 |
| Sobre (077) | Compose | 077 | 18 |
| Ajuda (042/090) | Views | 090 | 19 |

## Erros encontrados e corrigidos
1. **Toque em Definições abria Sons e Voz.** `SettingsRow(...) { nav.navigate(..) }`: a lambda final ligava-se ao último
   parâmetro (`trailing`), por isso corria na composição e navegava por todas as linhas em cadeia. Corrigido: `onClick` passou a ser o último parâmetro.
2. **Barra inferior e cartão do perfil em #EAEAEA (em vez de #FFFFFF).** Era a sobreposição de elevação do Material (tingia o branco com `colorPrimary`,
   preto). `elevationOverlayEnabled=false` no tema resolve as duas (era o problema "por resolver" do lote 0).
3. Comunicação: rodapé com aviso a mais escondia as linhas de marketing; título de marketing com fundo cinzento; tamanhos de texto 15-25% acima.
   Medidos pelas alturas de linha nos dumps (3,5 px/dp): títulos de linha 14sp, subtítulos 12sp, secções 18sp, barra 16sp.
4. Slider de Sons e Voz: pista grossa do Material 3 substituída por fio de 2dp.

## Afinação (2ª passagem)
- Tamanhos medidos pela largura do texto nos dumps (original vs recriação): linhas 15sp (16sp nas opções de Audição), subtítulos 12sp,
  secções 18sp, título da barra 17sp, cabeçalho grande 30sp, nome no cartão do perfil 28sp; cartão 74dp de avatar e 20dp de margem interior;
  barra de topo 12dp mais curta (alinha a seta com a original).
- Separadores: cada um tem agora ícone de contorno (inativo) e preenchido (ativo), como nas capturas 000/010-013 (`tools/gen_tabs.py`; seletor por `state_checked`).
- Audição: topo com ilustração própria (`illus_hearing.xml`, formas planas, só a composição da original) e botão de voltar redondo e branco;
  opções com botão de opção à esquerda (aro cinzento; selecionado = aro e ponto pretos) em vez do visto à direita.

## Diferenças que ficam (documentadas)
- Fonte: a original usa a Uber Move (proprietária); a recriação usa a do sistema, mais larga, por isso há quebras de linha ligeiramente diferentes.
- Ícones: vetoriais próprios (gerados), não os da original (ex.: Audição/Vibração em Acessibilidade usam ícones genéricos); ilustração da Audição é própria, não a arte da original.
- Pontos e etiquetas da barra (ex. "6" na Caixa de entrada, ponto no Menu) dependem do backend, ainda não ligados.
- Cartão do perfil: dados fictícios (sem foto); ligar a `/rt/...` no lote de rede.
- "Gerir conta", "Privacidade", "Editar endereço", "Segurança": sem destino (páginas web/fluxos de conta, fora do âmbito D7).

## Verificação
`./gradlew assembleDebug testDebugUnitTest`: compila e os 7 testes passam. Navegação percorrida no telemóvel: Menu -> Ajuda, Definições ->
Acessibilidade -> Audição, Comunicação (+ folha push), Navegação, Sons e Voz, Menu -> Sobre; todas com o texto esperado.
