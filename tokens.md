# tokens.md — tokens de design partilhados

**BUILD §1** do `PROMPT_CLONE_BUILD.md`: «Ecrãs medidos isoladamente divergem nas
cores e nos espaços; o ficheiro de tokens é o que os mantém iguais.»

**Regra de precedência:** medição no PNG > `ui_spec/design_tokens.json` >
estimativa. Quando divergirem, **ganha o PNG** e a divergência escreve-se aqui.

**Fonte dos valores:** `ANDOIRD/DRIVER/ui_spec/design_tokens.json` (1 087 181 bytes,
valores descodificados do binário) cruzados com as capturas em `ux_capture/`.

---

## 1. Cor

### 1.1 Base

| Token | Valor | Uso | Fonte |
|---|---|---|---|
| `bg.base` | `#FFFFFF` | fundo de ecrã | `colors_light.ub__ui_core_v3_brand_white` |
| `bg.inverse` | `#000000` | painel de navegação, botão primário | medido na `060` |
| `bg.subtle` | `#F3F3F3` | separadores, chips inativos | medido na `061` |
| `border.default` | `#E2E2E2` | contorno 1dp, divisores | medido na `061` |

### 1.2 Texto

| Token | Valor | Uso |
|---|---|---|
| `text.primary` | `#000000` | títulos e corpo |
| `text.secondary` | `#6B6B6B` | legendas, subtítulos |
| `text.inverse` | `#FFFFFF` | sobre fundo preto |
| `text.disabled` | `#AFAFAF` | itens inativos |

### 1.3 Acento

| Token | Valor | Uso | Nota |
|---|---|---|---|
| `accent.primary` | `#000000` | CTA principal (Uber usa preto) | medido |
| `accent.demand` | `#D55D26` | pills de procura no mapa | **medido na `120_off2_inicio`**, não é o rosa do original |
| `accent.success` | `#006A4E` | paragem verde (recolha) | medido |
| `accent.danger` | `#C42B1C` | paragem vermelha (entrega), erro | medido |
| `accent.info` | `#0A5BC4` | barra de espera | medido |

> **Divergência registada:** o original usa um rosa de marca para as pills de
> demanda. O clone usa `#D55D26` porque foi a cor medida na captura `120_off2_inicio`
> (marca Qolari, não transplantação). O PNG ganhou ao token do binário.

---

## 2. Tipografia

| Token | size | weight | lineHeight | Uso |
|---|---|---|---|---|
| `type.display` | 40sp | regular | 44sp | título de ecrã (Descobrir, Início) |
| `type.title` | 28sp | medium | 32sp | título de secção |
| `type.headline` | 24sp | medium | 28sp | cabeçalho de sheet |
| `type.body` | 16sp | regular | 22sp | corpo, listas |
| `type.label` | 14sp | medium | 18sp | botões, tabs |
| `type.tab` | 12sp | medium | 16sp | barra inferior (com `.` entre separadores) |
| `type.caption` | 12sp | regular | 16sp | legendas, notas |
| `type.price` | 52sp | medium | 56sp | **preço no cartão de pedido** |

**Fonte:** o binário usa **Uber Move** (`res/font/uber_move_bold.otf`, 67 096 bytes).
**Não é usada** — licença proprietária. O clone usa a sans-serif do sistema
(`plan.md` §8, tolerância 1). A divergência é de forma, não de métrica: os
tamanhos acima são os medidos.

---

## 3. Espaço e forma

| Token | Valor | Uso |
|---|---|---|
| `space.xs` | 4dp | entre ícone e label |
| `space.sm` | 8dp | entre linhas de um bloco |
| `space.md` | 16dp | margem lateral de ecrã |
| `space.lg` | 24dp | entre secções |
| `space.xl` | 32dp | topo de ecrã |
| `radius.sm` | 8dp | chips, badges |
| `radius.md` | 12dp | cartões (promo, pesquisa) |
| `radius.lg` | 16dp | botões grandes, sheets |
| `radius.full` | 999dp | pills, avatar |
| `elevation.card` | 0dp | o original é flat; sombra só em sheet |
| `elevation.sheet` | 8dp | bottom sheet |

---

## 4. Componentes com medida fixa

| Componente | Medida | Onde |
|---|---|---|
| Botão primário | altura 56dp, raio 16dp, texto `type.label` | `view_offer_card`, `fragment_map` |
| Cartão de oferta | preço `type.price`, radius 16dp | `100_online_*` |
| Barra inferior | altura 56dp + inset, ícone 22dp, label `type.tab` | `activity_main` |
| Painel de manobra | 2 secções, fundo `bg.inverse` | `view_maneuver_panel` |
| Cartão de espera | barra até 300 s = 100% | `view_wait_card` |
| Linha de menu | altura 56dp, divisor 1dp | `item_menu_row` |
| Pino do motorista | elipse achatada `PIN_FLATTEN = 0.50f`, 62dp largura | `RealMapView` |

---

## 5. Mapa

| Token | Valor | Nota |
|---|---|---|
| `map.tilt.nav` | 66° | modo navegação |
| `map.zoom.nav` | 18.3 | modo navegação |
| `map.target.ahead` | 150 m | alvo à frente do veículo |
| `map.buildings` | `false` | sem 3D |
| `map.route.color` | `#000000` | traço sempre preto |
| `map.pickup` | verde + quadrado branco | recolha |
| `map.dropoff` | vermelho | entrega |

---

## 6. Movimento

| Token | Valor | Fonte |
|---|---|---|
| `motion.tab` | 0-240 ms | `ux_behavior.md` §3.1 (medido nos vídeos) |
| `motion.sheet` | 300 ms | `anim/` — duração mais comum (×11) |
| `motion.fade` | 200 ms | `anim/` (×11) |
| `motion.long` | 1000 ms | `anim/` (×8) — usada em ilustrações |

---

## 7. Como usar

1. Antes de medir um ecrã, lê este ficheiro.
2. Se o PNG mostrar outro valor, **mede outra vez**; se confirmar, atualiza o
   token aqui e escreve a divergência na secção 8.
3. Nunca uses `#333` genérico quando o token diz `#2E2E33`.

## 8. Divergências registadas

| # | Token | Original | Clone | Porquê |
|---|---|---|---|---|
| D-1 | `font.family` | Uber Move | sans-serif do sistema | licença proprietária (`plan.md` §8.1) |
| D-2 | `accent.demand` | rosa de marca | `#D55D26` | cor medida na captura `120_off2_inicio` |
| D-3 | `elevation.card` | flat | flat | sem divergência; registado para não aparecer sombra |
| D-4 | `map.route.color` | vermelho (Uber) | `#000000` | decisão do cliente: o vermelho não tem significado |

---

## 9. Nota de escopo

Este ficheiro cobre a **Driver**. A Rider usa os mesmos tokens base (é a mesma
marca), com duas diferenças próprias: `type.display` 40sp em 3 linhas no Início e
`type.price` 30sp na carteira. Ver `ANDOIRD/USER_LITE/RECRIACAO` e a nota de
fidelidade em `.qolari/notes.md`.
