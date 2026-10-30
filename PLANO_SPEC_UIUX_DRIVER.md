# PLANO — Recriação da Driver pela spec (versão alinhada ao spec)

> **Atualização 2026-10-25:** este plano (P0–P8) é histórico. O programa de trabalho
> passou a ser o [`PROMPT_CLONE_MEGA.md`](PROMPT_CLONE_MEGA.md), com os artefactos
> [`plan.md`](plan.md), [`access_plan.md`](access_plan.md), [`coverage.md`](coverage.md),
> [`topology.md`](topology.md) e [`endpoints.json`](endpoints.json). A execução por ecrã
> usa o [`PROMPT_CLONE_BUILD.md`](PROMPT_CLONE_BUILD.md). As fases P0–P8 continuam
> válidas como registo do que foi feito; a numeração nova está no MEGA.

Base: [PROMPT_SPEC_UIUX.md](PROMPT_SPEC_UIUX.md). Âmbito: **Driver**. Rider e Fleet ficam como fase opcional.

**O que mudou em relação à versão anterior:** a captura vem antes da extração (como o spec pede), a referência é a app original instalada e não modificada, e as exceções ficam registadas e aprovadas.

---

## 1. Quadro de fases (editável)

Para alterar um modelo ou um esforço, muda a linha da fase nesta tabela e diz-me. As fases em Sonnet e Opus correm num subagente com o modelo e o esforço indicados. As fases em Haiku podem correr na sessão atual.

| Fase | Nome (equivalente no spec) | Modelo | Esforço | Estado |
|---|---|---|---|---|
| P0 | Baseline (spec: FASE 0) | Haiku | low | ✅ Feita |
| P1 | Captura viva (spec: FASE 0.5) | Sonnet (travessia) + Haiku (loops) | high / low | ✅ Fechada na Uber original (172 capturas, 4 vídeos, `travessia.csv`, `versoes.csv`). Faltam viagem, PIN e ganhos (via do laboratório) e o `ux_behavior.md` (P3) |
| P2 | Extração (spec: FASE 1) | Sonnet (ferramenta) + Haiku (correr) | medium / low | ✅ Feita com a 4.600.10000: `ui_spec/`, `stack.md`, `ux_capture/correlacao_layouts.csv` (ver `ui_spec/README.md`) |
| P3 | Comportamento consolidado (`ux_behavior.md`) | Sonnet (+ Haiku para o grafo) | high / low | ✅ Feita (`ux_capture/ux_behavior.md`, com lacunas listadas na secção 8) |
| P4 | Contrato e rede (`endpoints.json`) | Opus (+ Haiku para o esqueleto) | high / low | ✅ Feita (`ANDOIRD/DRIVER/endpoints.json` + `ENDPOINTS.md`: 129 hosts e 1.104 endpoints classificados, 103 essenciais, afinado com o tráfego real do servidor: 17 lacunas do backend) |
| P5 | App nova (spec: FASE 4) | Sonnet | high | 🔶 Stack decidida (`ANDOIRD/DRIVER/STACK_DECISAO.md`): Views + Compose por evidência, com 7 desvios registados. **Lote 0 feito** (`ANDOIRD/DRIVER/RECRIACAO/`: compila, instalada e comparada no PTP-N49 em `captures/COMPARACAO_LOTE0.md`). **Lote 1 feito** (Menu, Definições, Acessibilidade, Audição, Comunicação, Navegação, Sons e Voz, Sobre, Ajuda; Compose só onde a original é Compose; fundo da barra corrigido; 7 testes a passar; comparação em `RECRIACAO/COMPARACAO_LOTE1.md`). **Lote 2 feito** (Início painel e mapa, login nativo por telefone, sessão, janela Erro, arranque sem servidor; 22 testes; `RECRIACAO/COMPARACAO_LOTE2.md`; banner sem rede validado no telemóvel). **Lote 3 feito** (Descobrir, Rendimentos com dados reais, Caixa de entrada em Compose, contadores da barra; 35 testes; validado no telemóvel; `RECRIACAO/COMPARACAO_LOTE3.md`). **Lote 4 feito** (proposta, aceitar, recolha, PIN, em viagem, fim, ganhos e avaliação; posição enviada; 58 testes; validado no telemóvel com viagens reais do backend local; `RECRIACAO/COMPARACAO_LOTE4.md`; estados da viagem sem original capturada, marcados `[inf]`). **Lote 5 feito** (Segurança, Veículos e Documentos com dados reais, páginas informativas; Comfort e envio de documentos fora de âmbito; 67 testes; `RECRIACAO/COMPARACAO_LOTE5.md`). Próximo: P7 validação ecrã a ecrã |
| P6 | Backend e contrato (spec: FASE 4) | Sonnet | medium | 🔶 Lacunas tratadas: 17 handlers novos (`apps/driver.py`, `identity.py`, `common.py`) com 20 testes (`tests/test_lacunas.py`), 37 testes a passar. Falta publicar no servidor e validar no telemóvel |
| P7 | Validação ecrã a ecrã | Opus (+ Haiku para os pares de imagens) | medium / low | ✅ `RECRIACAO/VALIDACAO.md` (textos 61/65, divergências por lote, back, estados); capturas do lote 5 completas |
| P8 | Documentação e memória | Haiku | low | ✅ `RECRIACAO/README.md` reescrito, memória do projeto atualizada (`recriacao-driver-state`) |

**Modelos:**
- **Haiku:** tarefas mecânicas com critério de saída objetivo (correr, copiar, contar, renomear, gerar índices).
- **Sonnet:** escrever código e interpretar capturas e comportamento.
- **Opus:** decisões que afetam o contrato ou a aceitação.

**Esforço:** `low`, `medium`, `high`, `xhigh`. Em P4, subir para `xhigh` só se a classificação ficar ambígua.

---

## 2. Ponto de partida (verificado)

| Item | Estado |
|---|---|
| Telemóvel de trabalho: **PTP-N49** (`AQCK024C17020494`) | Tem `com.ubercab.driver` 4.600.10000 (original), `com.qolari.driver` 4.599.10004 (renomeado) e apps de outros projetos |
| Outro telemóvel ligado (`18a959c4`, Mi 9T Pro) | Não usado. Não é tocado sem confirmação |
| Original instalado | `com.ubercab.driver` 4.600.10000 (versionCode 313129) |
| `source-original.apk` | Pacote `com.ubercab.driver` (verificado no manifest). Versão provável 4.599.10004, não confirmada |
| `decoded/` | Renomeado (`com.qolari.driver`), versão 4.599.10004. **Não serve como fonte limpa** |
| **Versão instalada ≠ `decoded/`** | 4.600.10000 contra 4.599.10004. Por isso a extração deve usar o APK instalado (ver decisão 2) |
| `BACKEND` | `pytest`: 17 testes a passar |
| `TESTE/ui_spec_android/` | Extração parcial: manifest, values, design tokens, 2.697 layouts, 4.486 drawables XML, `api.json` (1.054 paths, 107 implementados), `models.json`, `contract_main_flow.md` |
| `TESTE/app/` | App Kotlin + Compose com 4 ecrãs. `ApiClient`, `SessionStore`, `Controls` e `QolariMap` são reutilizáveis |
| `TESTE/tools/ui_tap.sh` | Dump + toque por texto |
| `TESTE/*.png` (47) | Baseline de captura, sem demo mode e sem correlação com layouts |
| App em primeiro plano no PTP-N49 | `pt.minhaimobiliaria.app`, de outro projeto. **Pára a captura até ser confirmado** |

---

## 3. Regras de execução

- **Captura antes de extração** (spec, linhas 20–21).
- **O original não é modificado** (spec, linha 6). Qualquer exceção tem de estar aprovada e registada (ver decisão 1).
- **Sem passwords nem códigos de login nos ficheiros** (regra da equipa). O código é pedido na hora.
- **Antes de cada toque:** confirmar que `topResumedActivity` é a app em teste. Se for outra, parar e avisar.
- **Demo mode:** ativar antes da captura e repor (`exit`) no fim.

---

## 4. Fases em detalhe

### P0 — Baseline ✅
- **Modelo:** Haiku · **Esforço:** low
- **Feito:** `pytest` do BACKEND (17 a passar). Dispositivos identificados. Pacotes inspecionados sem alterar nada.
- **Não feito:** build da `TESTE/app`. Passa para P5.

### P1 — Captura viva (sobre o original, sem modificar)
- **Modelo:** Sonnet (travessia) + Haiku (loops) · **Esforço:** high / low
- **Entradas:** `com.ubercab.driver` no PTP-N49, `ui_tap.sh`, roteiro de [PROMPT_PROXIMO_CHAT.md](PROMPT_PROXIMO_CHAT.md) §2, 47 PNG existentes (reclassificar, não apagar)
- **Passos:**
  - **P1a — demo mode e login** (Sonnet, medium): ativar o demo mode. Login com o código pedido na hora. Sem gravar código.
  - **P1b — travessia em largura** (Sonnet, high): script que faz dump, lista os nós clicáveis não visitados, toca e regista em `ux_capture/travessia.csv` (origem, ação, destino, PNG). Haiku (low) corre os ciclos. Sonnet revê o CSV no fim de cada bloco.
  - **P1c — estados sem backend** (Sonnet, medium): offline, erro, lista vazia, permissões, dialogs.
  - **P1d — screenrecord** (Haiku, low): fluxos que o original consegue mostrar.
- **Saída:** `ux_capture/` com PNG nomeados, `travessia.csv` com fila de nós por visitar a zero, e rascunho de `ux_behavior.md`.
- **Limite conhecido:** sem backend, o original não chega a oferta, viagem, PIN nem ganhos. Ver decisão 1.

### P2 — Extração do original
- **Modelo:** Sonnet (ferramenta) + Haiku (correr) · **Esforço:** medium / low
- **Entradas:** APK instalado (decisão 2), `TESTE/tools/extract_spec.py`, `ui_spec_android/`
- **Passos:**
  - **P2a — obter o APK exato** (Haiku, low): `adb shell pm path com.ubercab.driver` e `adb pull`. É a versão que está a ser capturada.
  - **P2b — decodificar** (Haiku, low): apktool para `spec_src/`.
  - **P2c — estender o extractor** (Sonnet, medium): PNG e WebP (291 em falta), `anim`, `animator`, `interpolator`, `color`, `color-night`, `color-v31`, `styles.xml`, `themes.xml`, lista de `font` (a Uber Move fica de fora), raízes parametrizáveis.
  - **P2d — `stack.md`** (Sonnet, low): contar pacotes no smali (Retrofit, Gson, RxJava, Room, Firebase messaging, Maps, Braintree, Twilio).
  - **P2e — correlação PNG ↔ layout** (Sonnet, medium): cada PNG com o layout correspondente, ou "sem layout".
- **Saída:** `ui_spec/` completo, `stack.md`, correlação completa.

### P3 — Comportamento consolidado (`ux_behavior.md`)
- **Modelo:** Sonnet (+ Haiku para o grafo) · **Esforço:** high / low
- **Entradas:** `travessia.csv` (P1), vídeos (P1d), `anim` e `interpolator` (P2), `contract_main_flow.md`
- **Passos:**
  - Haiku (low): grafo de navegação a partir do CSV.
  - Sonnet (high): gestos, animações com duração e easing, feedback, back e formulários.
- **Critério:** cada ação do CSV tem entrada no `ux_behavior.md`, e cada transição animada tem duração e easing.

### P4 — Contrato e rede (`endpoints.json`)
- **Modelo:** Opus (+ Haiku para o esqueleto) · **Esforço:** high / low
- **Entradas:** `api.json`, `models.json`, `BACKEND/contracts/driver_*`, `base_urls_original`, `contract_main_flow.md`, e logs do backend se a decisão 1 for aprovada
- **Passos:**
  - Haiku (low): esqueleto com uma entrada por path (método, path, implementado sim ou não, origem no smali).
  - Opus (high): classificar cada host e endpoint como `rebuild`, `substituir` ou `descartar`. Ligar cada um a `screens`. Decidir auth, realtime (FCM), uploads, config remota, terceiros e schema Room.
- **Critério:** zero entradas sem classificação, e zero `screens` vazios nos endpoints implementados.

### P5 — App nova (ajustar `TESTE/app` à spec)
- **Modelo:** Sonnet · **Esforço:** high
- **Entradas:** `TESTE/app`, `DriverApi.kt`, `Models.kt`, `mock_server.py`
- **Passos:**
  - Um único ficheiro de config (base URL, ambiente, keys). Hoje o default está em `SessionStore.kt:15`.
  - Ecrãs que faltam, um a um, com o template do APÊNDICE da spec.
  - Durações e estados (vazio, erro, loading).
  - Manter Compose. MVVM + coroutines fica registado como equivalente de RIBs + RxJava.
  - Build da `TESTE/app`.
- **Critério:** cada ecrã do CSV tem um Composable, o build passa, e o mock cobre o fluxo principal.

### P6 — Backend e contrato
- **Modelo:** Sonnet · **Esforço:** medium
- **Entradas:** `BACKEND/apps/driver.py`, `BACKEND/tests/test_flow.py`, `mock_server.py`
- **Passos:** gerar `endpoints.json` a partir de P4 e validar que `driver.py` implementa o subconjunto marcado. Documentar o estágio LAN (XAMPP na porta 80).
- **Critério:** `pytest` passa, e nenhum endpoint marcado como implementado fica sem handler.

### P7 — Validação ecrã a ecrã
- **Modelo:** Opus (+ Haiku) · **Esforço:** medium / low
- **Passos:**
  - Haiku (low): pares lado a lado (PNG original × PNG nova).
  - Opus (medium): comparar geometria, cores, textos, estados, gestos, back e navegação. Divergências em `VALIDACAO.md`.
- **Critério:** lista de divergências fechada, ou aceite por ti.

### P8 — Documentação e memória
- **Modelo:** Haiku · **Esforço:** low
- **Passos:** atualizar READMEs e a memória do projeto. Alinhar nomes com o spec.

### Opcional — Rider e Fleet
- Só depois da Driver e da decisão. Repetir P2 a P7 com a mesma atribuição de modelos.

---

## 5. Decisões pendentes

1. **Estados de viagem (oferta, viagem, PIN, ganhos).** O original sem backend não os mostra.
   - (a) Só o original. Estes ecrãs ficam de fora, registados como lacuna.
   - (b) Cópia do original com o URL trocado, usada só para ver estes estados e gerar tráfego para o nosso backend. É uma exceção à regra "o original não é modificado", e a cópia nunca substitui o original.
   - **Recomendo (b)**, registado como exceção aprovada.
2. **Versão de referência.** Usar o APK instalado (4.600.10000) para captura e extração (**recomendado**), ou o `source-original.apk`, se for a 4.599.10004.
3. **Telemóvel.** PTP-N49 (`AQCK024C17020494`). O outro telemóvel não é tocado.
4. **Login.** O código é pedido na hora da captura, como acordado.

---

## 6. Estado atual

- **P0 feita.**
- **P1 parada.** A app em primeiro plano no PTP-N49 é `pt.minhaimobiliaria.app`, de outro projeto. Não toco até essa app sair ou tu confirmares.
