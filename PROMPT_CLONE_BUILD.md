# PROMPT — Recriar UM ecrã (execução num agente de código)

Um prompt por ecrã. Não coles vários ecrãs no mesmo pedido. Não peças o projeto
todo — pedes um componente, verificas, avanças.

**Regra dura:** um ecrã só fecha quando todas as ações visíveis têm efeito real.

Substitui `<ECRÃ>`, `<STACK_UI>`, `<FICHEIRO_DESTINO>`.

**Anexa sempre:** o PNG do ecrã. **Anexa se existir:** o layout XML/hierarquia,
as cores/dimens/fonts do `ui_spec/`, a entrada do `ux_behavior.md`, o DTO do
ecrã.

---

## 0. REGRA DE ARRANQUE

Se não tiveres o PNG de `<ECRÃ>`, **para e pede**. Não inventes um ecrã a partir
do nome.

Se faltar o DTO, usa fixture realista e marca `// presumed` no campo.
Se faltar o layout, mede tudo a partir do PNG.
Se faltar o comportamento, implementa o efeito mínimo **real** e registra em
`capabilities.md`/`backlog.md`; não inventes um toast nem desactives o botão
para passar.

Se o ecrã tiver uma ação sem endpoint/estado, **não avances com placeholder**:
abre a FASE 4/7, cria o contrato e implementa o efeito real. Um botão que só
mostra "fora do âmbito" ou "em breve" não é uma entrega.

---

## 1. MEDIR ANTES DE ESCREVER CÓDIGO

Primeira saída, obrigatória: **tabela de medição**. Sem ela, não avances.

1. Define o espaço de design a partir da largura do PNG (ex.: 360dp) e o fator
   de escala para o dispositivo.
2. Extrai a grelha: margens laterais, gutters, alturas de linha, ritmo vertical.
3. Lista os tokens: cores hex, tamanhos de texto, pesos, line-heights, raios,
   elevações, opacidades.

Formato da tabela:

```
elemento | x | y | w | h | cor | fontSize | weight | lineHeight | raio
```

Mede na imagem. **Não estimes a olho.** Cruza com `ui_spec/` e, se divergirem,
diz qual seguiste e porquê. Se tiveres o artefacto descodificado
(`decode_android_resources`), os valores de `values/` são a fonte dos tokens —
mas quem decide é a medição no PNG: se divergirem, ganha o PNG e a divergência
entra na lista de assunções.

Se já existir `tokens.md` (ou o teu ficheiro de tema), usa-o e acrescenta-lhe o
que falta — no fim, escreve lá os valores novos. Ecrãs medidos isoladamente
divergem nas cores e nos espaços; o ficheiro de tokens é o que os mantém iguais.

---

## 2. FORMA — a parte que separa clone de "parecido"

- Extrai a geometria REAL dos elementos gráficos (ilustrações, blobs, ícones,
  logos): traça os contornos a partir da imagem e converte-os em paths
  vetoriais (SVG / vector drawable / Path conforme a stack).
- **NÃO uses caixas + corner radius quando a forma é orgânica ou irregular.**
  Um blob não é um retângulo arredondado.
- Ícones: redesenha-os. Nunca exportes nem reutilizes ficheiros do original.
- Elementos cortados pelas bordas desenham-se completos, continuando offscreen.
- Imagens e ilustrações: placeholders teus, com as mesmas dimensões e o mesmo
  peso visual.

---

## 3. TIPOGRAFIA E COR

- Usa os valores exatos da tabela: hex, fontSize, peso, line-height, alinhamento.
- Se existir font em `res/font`, usa-a; se não, a mais próxima e diz qual.
- Verifica contraste AA nos textos sobre cor.
- Nada de `#333` genérico quando mediste `#2E2E33`.

---

## 4. LAYOUT

- Hierarquia de containers explícita.
- **Scroll vertical e horizontal, os dois, quando o original os tem.** Listas e
  formulários rolam na vertical; carrosséis, chips, separadores e galerias rolam
  na horizontal. Card cortado na margem direita é sinal de scroll horizontal —
  implementa-o e reproduz o snap/pager.
- **Scroll encaixado** (linha horizontal dentro de lista vertical): mantém o
  comportamento do original — o eixo do gesto decide quem rola.
- Indicadores, sombras de borda e overscroll iguais aos do original.
- Scroll só onde o conteúdo excede; nada de scroll decorativo.
- Safe areas e insets corretos; nada encostado à status bar por acidente.
- Teclado: o conteúdo não pode ficar escondido.
- Responsivo por **escala uniforme** do espaço de design. Não inventes reflow
  que o original não tem.

---

## 5. ESTADOS — todos, não só o bonito

Implementa os cinco, mesmo que o PNG só mostre um:

1. default (com dados)
2. loading (skeleton com a forma real do conteúdo)
3. empty (mensagem + ação)
4. error (mensagem + retry)
5. offline (se aplicável)

Se não tiveres captura de um estado, implementa o mínimo coerente e lista-o em
"assunções". Um ecrã sem empty state não está pronto. Um estado sem ação real
também não.

---

## 6. COMPORTAMENTO

- Gestos: swipe, long-press, pull-to-refresh, pinch — os que `ux_behavior.md`
  documenta para este ecrã.
- Transições com duração e easing de `res/anim` / `interpolator` — ou medidos
  nos frames do vídeo de captura, nunca por achismo.
- Back: reproduz o comportamento documentado (pop / sobe / confirma / sai).
- Formulários: validação no momento certo (on-blur vs submit), máscaras, foco,
  teclado, mensagens de erro por campo.
- Cada elemento interativo recebe uma prop de ação (`onOpenX`, `onSubmit`).
  Nada de navegação hardcoded dentro do componente.
- **Cada ação tem efeito real.** Se não há endpoint/estado, o ecrã não está
  pronto: implementa o endpoint/estado ou remove a entrada. Proibido toast
  "fora do âmbito", `TODO`, `em breve`, `onClick` vazio.

---

## 7. DADOS

- O componente **nunca** chama HTTP. Recebe dados por props/estado.
- Recebe handlers de mutação (`onSubmit`, `onUpload`, `onSend`, `onDelete`) que
  chamam o `Repository`; um handler que só mostra toast não é um handler.
- Mapeia os campos do DTO 1:1 para os elementos do ecrã.
- Fixtures realistas e **densas** — nomes longos, valores grandes, listas cheias.
  Dados escassos escondem bugs de layout.
- Campos sem contrato: fixture + `// presumed`.
- Cada mutação tem idle/loading/success/error/retry e reflete-se na UI/lista.

---

## 7.5 AÇÃO REAL — REGRA DURA

Preenche esta tabela para cada elemento interativo:

```
elemento | ação | endpoint/estado | teste | status
```

- `status` só pode ser `ok` ou `gap`. Um `gap` impede a entrega do ecrã.
- Sem endpoint/estado = `gap`; não é "fora do âmbito".
- Ação local (abrir sheet, mudar tab, expandir) tem estado local testável.
- Se a ação depende de terceiro que não podes usar, implementa equivalente
  próprio funcional ou remove a entrada. Nunca um botão que avisa que não faz.
- A tabela entra em `capabilities.md` (projeto) e no fim da entrega.

**Não há terceira opção.** Ou o botão funciona, ou não existe. "Em breve",
"fora do âmbito", `TODO`, toast e `disabled` sem razão não são estados válidos.

A evidência do ecrã (`live`/`served`/`static`) não muda esta regra: `served` ou
`static` é confiança da captura, não permissão para placeholder.

---

## 8. ESTRUTURA DE PRODUÇÃO

- Um componente autocontido em `<FICHEIRO_DESTINO>`.
- Props tipadas na linguagem da stack.
- Camadas decorativas sem captura de toques; overflow escondido no root.
- Elementos interativos com `accessibilityRole`/equivalente e label.
- Links com handler próprio.
- **NÃO desenhes réplicas da status bar nem do indicador de gestos** — usa
  StatusBar translúcido e safe-area-insets.
- Dependências mínimas: só as equivalentes às já presentes em `stack.md`.

---

## 9. CRITÉRIO DE ACEITAÇÃO (verifica antes de entregar)

- [ ] Tabela de medição entregue, com todos os elementos
- [ ] Cores hex iguais às medidas (sem aproximação)
- [ ] Tipografia igual: size, weight, line-height, cor
- [ ] Formas orgânicas em path vetorial, não em caixas arredondadas
- [ ] Elementos cortados completos offscreen
- [ ] Scroll vertical e horizontal onde o original os tem, com o mesmo snap
- [ ] Cinco estados implementados (offline quando aplicável) e testados
- [ ] Zero botões mortos: todo o elemento interativo tem efeito real e teste
- [ ] Zero `fora do âmbito`/`em breve`/`TODO`/`FIXME`/`not implemented` no ecrã
- [ ] Cada mutação testada: happy, empty, error, offline
- [ ] `capabilities.md` atualizado com `elemento | ação | endpoint/estado | teste | status`
- [ ] Nenhuma ação crítica sem endpoint/estado; se faltar, o ecrã não está pronto
- [ ] Sem HTTP dentro do componente
- [ ] Zero assets copiados do original
- [ ] A11y: roles e labels nos interativos
- [ ] Sem réplica de status bar / gesture indicator
- [ ] Build/compila sem erros
- [ ] Lista de assunções no fim (curta e explícita)
- [ ] Assunções apenas visuais; nenhuma assunção substitui uma ação em falta

Se algum item falhar, corrige antes de dizer que está pronto.

---

## 10. O QUE NÃO FAZER

- Não copiar assets, ícones, fontes ou ilustrações do original
- Não usar retângulos arredondados para formas orgânicas
- Não estimar medidas a olho
- Não inventar ecrãs, rotas ou fluxos que não estão no pedido
- Não replicar a UI do sistema operativo
- Não adicionar dependências "para facilitar"
- Não entregar só o estado bonito
- Não dizer "aproximadamente" quando podias medir
- Não criar toast "fora do âmbito", "em breve" ou "TODO"
- Não desactivar um botão para esconder falta de backend
- Não declarar fora de âmbito para passar o checklist
- Não pedir ao utilizador para listar o que falta
- Não entregar um ecrã com uma ação sem efeito

---

## 11. ENTREGA

Responde com:

1. Tabela de medição
2. O código do componente em `<FICHEIRO_DESTINO>`
3. Assunções (se houver)
4. Checklist do §9 marcado item a item
5. Tabela de ações (§7.5) e atualização de `capabilities.md`/`backlog.md`

Se houver um `gap`, não digas que está pronto.

---

## 12. AUTO-AUDITORIA (antes de dizer "pronto")

Corre no diretório do ecrã:

```bash
grep -RniE "fora do [âa]mbito|em breve|TODO|FIXME|not implemented|coming soon" <FICHEIRO_DESTINO>
```

Se houver um resultado, não entregues: implementa ou remove a entrada. Verifica
também que todos os `onClick`/handlers têm destino/efeito e que a tabela §7.5
está completa. O utilizador não deve ter de descobrir o que falta.
