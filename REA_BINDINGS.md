# REA — ANEXO DE FERRAMENTAS (v4.0)

> Versão 4.0 — descoberta de funcionalidades genérica; mesma estrutura da v3.1.

Liga o programa (`PROMPT_CLONE_MEGA.md`) e a execução (`PROMPT_CLONE_BUILD.md`)
ao servidor MCP **REA**.

Este ficheiro **não tem fases, gates nem critério de "pronto"** — essas decisões
pertencem ao MEGA. Aqui resolve-se uma coisa só:

```
capacidade → ferramenta → entrada → artefacto que fica guardado
```

Se houver conflito entre este anexo e o MEGA, ganha o MEGA. Se houver conflito
entre as instruções de workflow que o REA instala e o MEGA, ganha o MEGA: do REA
usam-se os **contratos de ferramenta**, não o método.

---

## 0. PRECEDÊNCIA

1. **Capacidade na tabela §2 → ferramenta obrigatória.** Não é sugestão.
2. **Comando cru é fallback declarado.** `adb`, `apktool`, `jadx`, `frida`,
   `mitmproxy` continuam válidos, mas a razão escreve-se no `plan.md` e o
   resultado tem de ser guardado como artefacto na mesma (§3).
3. **Ferramenta em falta não é desculpa.** Provider não configurado, alvo não
   suportado, binário ausente: regista em `plan.md` e em `coverage.md`, e usa o
   substituto que tiveres. Nunca inventes evidência para preencher a linha.
4. **Uma capacidade, uma chamada.** Não encadeies dez inspeções para "ver o que
   dá". Se três tentativas não respondem, o problema é de sonda — é a stop rule
   do MEGA.
5. **O catálogo é maior do que esta tabela.** Se precisares de uma capacidade
   que não está aqui, procura no catálogo do servidor antes de recorrer a
   comando cru. Quando descobrires uma capacidade nova, acrescenta-a aqui — o
   anexo é vivo.

---

## 1. VOCABULÁRIO DE EVIDÊNCIA

O REA devolve observações com cobertura, limites e `unknowns`. O MEGA usa seis
níveis (`live`/`served`/`static`/`unverified`/`presumed`/`designed`) e dois de
integridade (`clean`/`repack_suspect`).

**A tradução é feita uma vez, quando o facto entra na spec, e está no MEGA §2.1.**
Resumo operacional:

| Chamada | Nível máximo que autoriza |
|---|---|
| `inspect_*`, `trace_*`, `decode_*`, `search_*` | `static` |
| `capture_adb_screen` / `capture_web_screenshot` do alvo original | `live` (+ `clean`) |
| A mesma captura de build repointado/re-assinado | `served` (+ `repack_suspect`) |
| Captura de request/resposta real, ponta a ponta | `live` |
| Ecrã materializado pelo teu backend | `served` |
| Referência pública (loja, help, vídeo) | `unverified` |
| Inferência tua | `presumed` |
| Ecrã/painel que não existe no original | `designed` |

**Regra dura:** uma ferramenta nunca promove um facto. Se a evidência veio do
binário, é `static` para sempre — mesmo que pareça óbvia. E se veio de um build
re-assinado, carrega `repack_suspect` até confirmação contra o original.

Uma captura do alvo original corre na app real: é `live`/`clean`, não `static`.
Uma captura de build repointado é `served`/`repack_suspect`.

---

## 2. CAPACIDADE → FERRAMENTA → ARTEFACTO

Legenda de fase: **F0** artefacto · **F1** acesso · **F2** captura ·
**F3** spec · **F4** contrato · **F45** topologia · **F6/7** validação e fecho.

### 2.1 Android — artefacto e acesso (F0, F1)

| Capacidade | Ferramenta | Guarda em |
|---|---|---|
| Listar devices e escolher alvo | `list_adb_devices`, `inspect_adb_device` | `plan.md` (serial, build, SDK) |
| Encontrar o pacote por nome | `resolve_adb_packages` | `plan.md` |
| Listar pacotes instalados | `list_adb_packages` | `01_access/packages.json` |
| Extrair APK completo (base + splits) | `pull_adb_package` | `device_apk/` + digest |
| Classificar e inventariar o artefacto | `inspect_artifact`, `extract_artifact` | `00_artifact/inventory.json` |
| Manifest, SDK, permissões, componentes | `inspect_android_package` | `01_access/package.json` |
| Assinatura do artefacto (v1/v2/v3, rotação) | `inspect_signature` | `01_access/signature.json` |
| Grafo estático da aplicação | `project_android_application_graph` | `03_spec/app_graph.json` |
| Instalar cópia de trabalho | `install_adb_package` | `01_access/install.md` (digest + device) |
| Diagnóstico do descodificador | `inspect_apktool_client` | `plan.md` (provider e versão) |

**Nota:** `pull_adb_package` devolve **todos** os splits. Um clone que ignora os
splits de config descobre na FASE 5 que faltam recursos — e a spec fica órfã.

### 2.2 Android — captura (F2)

| Capacidade | Ferramenta | Guarda em |
|---|---|---|
| Frame do ecrã | `capture_adb_screen` | `02_capture/<ecra>_<n>.png` |
| Arranque reprodutível | `start_adb_app` | `02_capture/launch.md` |
| Logs para correlacionar erro ↔ ecrã | `read_adb_logcat` | `02_capture/<ecra>.log` |
| Diagnóstico de device (density, tamanho) | `inspect_adb_display` | `plan.md` |
| Inventário do device (features, serviços) | `list_adb_features`, `list_adb_services` | `01_access/device.json` |
| Bugreport para crash persistente | `collect_adb_bugreport` | `02_capture/bugreport/` |

**O que a ferramenta não faz:** travessia em largura, dump de UI, decisão do
próximo nó, classificação de inalcançáveis. Isso é FASE 2 do MEGA e continua a
ser teu.

### 2.3 Android — spec (F3)

| Capacidade | Ferramenta | Guarda em |
|---|---|---|
| Recursos descodificados (layout, values, drawable, anim, font) | `decode_android_resources` | `ui_spec/` + extracto em `03_spec/resources/` |
| Procurar classe por nome | `search_android_classes` | `03_spec/classes.index.md` |
| Estrutura de uma classe | `inspect_android_class` | `03_spec/classes/<id>.md` |
| Decompilar um método | `inspect_android_method` | `03_spec/methods/<id>.md` |
| Referências a uma classe/método | `trace_android_references` | `03_spec/refs/<id>.md` |
| Procurar símbolo no binário nativo | `find_xrefs_to_name` | `03_spec/refs/<id>.md` |

**Regra de uso:** por **identificador** (DTO, enum de estado, construtor de
URL), nunca "abre a classe e lê". O `inspect_android_method` exige
`overload_index` quando há sobrecargas — resolve com `inspect_android_class`
primeiro, não por tentativa.

### 2.4 Contrato e tráfego (F4)

| Capacidade | Ferramenta | Guarda em |
|---|---|---|
| Inspecionar HAR 1.2 / SAZ / mitmproxy | `inspect_web_network_capture` | `04_contract/capture.har` + shapes |
| Comparar capturas antes/depois | `compare_web_captures` | `04_contract/diff.md` |
| Comparar artefactos (versões, splits) | `compare_artifacts` | `04_contract/artifact_diff.md` |
| Trazer base de dados/ficheiro do device | `pull_adb_file` | `04_contract/local_db/` (schema e amostra) |

**Higiene obrigatória:** tokens, cookies e headers de autorização são
**redigidos** antes de o HAR entrar em `rea_evidence/`. Contrato sem segredos é
uma regra do MEGA (§4) e aplica-se ao artefacto, não só ao `endpoints.json`.

### 2.5 Outros alvos (quando não é Android)

| Alvo | Ferramentas | Fase |
|---|---|---|
| iOS / macOS | `project_apple_application_graph`, `inspect_artifact`, `extract_artifact` | F0/F3 |
| Nativo (C/C++/Go/Rust) | `inspect_binary_layout`, `procedure_info`, `find_xrefs_to_name` (+ provider Ghidra/Hopper/IDA) | F3 |
| .NET / managed | `inspect_managed_artifact`, `inspect_managed_members`, `compare_managed_members` | F3/F4 |
| Web / Electron | `inspect_web_page`, `capture_browser_scenario`, `capture_web_screenshot`, `trace_web_source_location` | F2/F3 |
| Processo em execução | `capture_process_scenario`, `compare_process_captures`, `find_changed_behavior` | F2/F6 |
| Interação com UI nativa (macOS) | `capture_native_ui_scenario` | F2 |

**Regra:** a stack do alvo decide a ferramenta, não a tua preferência. Um clone
de app Flutter não se resolve com inspeção de layouts Android.

### 2.6 Fecho (F6, F7)

| Capacidade | Ferramenta | Guarda em |
|---|---|---|
| Ledger de obrigações (fonte de verdade do "zero gaps") | `build_reconstruction_obligation_ledger` | `05_close/obligations.json` |
| Verificar spec vs Evidence bundle | `verify_reconstruction` | `05_close/verify.json` |
| Cobertura contra limite declarado | `evaluate_reconstruction_coverage` | `05_close/coverage.json` |
| Snapshot da análise | `close_binary` | `05_close/snapshot.json` |
| Pacote de evidência portátil | `export_evidence_bundle` | `05_close/bundle.json` |
| Retomar auditoria noutra sessão | `import_evidence_bundle` | `05_close/bundle.json` |

**Como entra no MEGA:** o ledger de obrigações alimenta o
`capabilities.md`/`backlog.md` da FASE 7; `verify_reconstruction` verifica a spec
contra o Evidence bundle; `evaluate_reconstruction_coverage` dá o número que vai
ao `RELATORIO_FINAL.md` (FASE 6, item 9). O MEGA decide o gate; o anexo entrega a
prova.

**Inputs:** o ledger exige Evidence bundle autenticado + obrigações revistas +
manifest de reconstrução; o verify exige a spec tipada. Se faltar input, fica
`unknown` e vai para `coverage.md`/`backlog.md` — não se inventa.

### 2.7 Descoberta de funcionalidades (F4.7)

| Capacidade | Ferramenta | Guarda em |
|---|---|---|
| Layouts, strings, values, drawables, anim, font | `decode_android_resources` | `ui_spec/` + `03_spec/resources/` |
| Manifest, SDK, permissões, componentes | `inspect_android_package` | `01_access/package.json` |
| Grafo de navegação/rotas | `project_android_application_graph` | `03_spec/app_graph.json` |
| SDKs, feature flags, classes | `search_android_classes`, `trace_android_references` | `03_spec/classes/`, `03_spec/refs/` |
| Endpoints completos | `inspect_web_network_capture` | `04_contract/` + `endpoints.discovered.json` |
| Capacidades do device | `list_adb_features`, `list_adb_services` | `01_access/device.json` |
| Fecho por feature | `build_reconstruction_obligation_ledger`, `verify_reconstruction`, `evaluate_reconstruction_coverage` | `05_close/` |

**Regra:** as ferramentas dão matéria-prima; a **taxonomia e o julgamento são do
MEGA** (`FEATURE_TAXONOMY.md`). Nenhuma ferramenta enumera "features" sozinha.
`features.md` e `endpoints.discovered.json` vivem na raiz do projeto; o
`rea_evidence/` guarda a prova que os sustenta.

---

## 3. `rea_evidence/` — ESTRUTURA E ÍNDICE

`rea_evidence/` não substitui `ui_spec/`. A spec é a versão normalizada para
humanos e para a FASE 5; `rea_evidence/` é a **prova** que sustenta cada linha.

```
rea_evidence/
  00_artifact/
    inventory.json          # inspect_artifact
    artifact.sha256
  01_access/
    packages.json           # list_adb_packages
    package.json            # inspect_android_package
    signature.json          # inspect_signature
    install.md              # install_adb_package + device/serial
    access_probe.md         # veredicto N0-N5, com ferramenta citada
  02_capture/
    <ecra>_<n>.png          # capture_adb_screen
    <ecra>.log              # read_adb_logcat
    frames.index.md
  03_spec/
    app_graph.json
    classes.index.md
    classes/<id>.md
    methods/<id>.md
    refs/<id>.md
    resources/              # extracto descodificado, não cópia integral do APK
  04_contract/
    capture.har             # redigido
    shapes.index.md
    artifact_diff.md
  05_close/
    coverage.json
    snapshot.json
    bundle.json
  INDEX.md
```

### `INDEX.md` — formato obrigatório

Uma linha por artefacto. Sem linha, o artefacto não existe para a auditoria.

```
artefacto | ferramenta | entrada | data | digest | unknown/limitação
```

Regras:

- **digest** de tudo o que é binário ou captura (sha256 curto serve).
- **unknown/limitação** copiado da resposta da ferramenta, não reescrito por ti.
- **entrada** é o alvo exato (pacote, path, device, URL) — sem isto o artefacto
  não é reproduzível.
- Artefacto que não caiba (HAR gigante, bugreport) fica referenciado por
  caminho + digest, não colado no índice.

---

## 4. COMO CHAMAR (regras práticas)

1. **Uma sessão por alvo.** O REA mantém sessão e evidência; misturar dois APKs
   na mesma sessão contamina referências e digests.
2. **Regista antes de interpretar.** Chama, guarda o resultado, escreve a linha
   no `INDEX.md`, e só depois tiras conclusões. Ao contrário, a conclusão
   escolhe a evidência.
3. **Lê a cobertura da resposta.** Toda a resposta diz o que cobriu e o que não
   cobriu. Essa parte é a que interessa para `coverage.md`.
4. **Não copies o binário para a spec.** Extracto é extracto; o original fica em
   `device_apk/` com hash.
5. **Providers são pré-requisitos, não detalhes.** Android precisa de JADX +
   JDK; recursos precisam de apktool; nativo precisa de Ghidra/Hopper/IDA; ADB
   precisa de adb. Verifica no início e escreve no `plan.md` — descobrir na
   FASE 3 que falta o provider é atraso puro.
6. **Schema compacto por omissão.** Só pedes o perfil completo de campos quando
   a validação falhar por ambiguidade — não por conforto.

---

## 5. LIMITES CONHECIDOS (não são bugs, são fronteiras)

| Limite | Consequência no MEGA |
|---|---|
| Repoint, patch, re-assinatura, stub server **não** são ferramentas do REA | FASE 1/2 continuam tuas; é o núcleo do método N2 |
| Travessia de UI e classificação de inalcançáveis **não** existem | FASE 2 continua tua; a ferramenta dá frames |
| O REA não desenha topologia, contrato, máquina de estados nem backoffice | FASE 4/4.5/4.6 são 100% MEGA |
| O REA não enumera funcionalidades nem decide taxonomia | FASE 4.7 e `FEATURE_TAXONOMY.md` são do MEGA; as ferramentas dão layouts/strings/endpoints |
| O REA não escreve app, backend nem painel | FASE 5/7 são 100% MEGA + BUILD |
| Não promove evidência nem valida fidelidade visual | FASE 6 comparação continua tua |
| Alvos com hardening forte podem ficar sem observação dinâmica | `access_plan.md` fecha em N1+N4, com gap escrito |

**Corolário:** se um dia este anexo começar a crescer com regras de processo, o
merge está a ser feito ao contrário. Processo é MEGA; ferramenta é aqui.

---

## 6. MANUTENÇÃO

- O catálogo de ferramentas muda com frequência. Quando uma chamada falhar por
  nome ou schema, procura a capacidade no catálogo antes de assumes que
  desapareceu.
- Uma ferramenta nova que substitua um comando cru entra na tabela §2 e sai do
  `plan.md` como fallback.
- Uma ferramenta removida: mantém a linha, marca `indisponível`, e escreve o
  substituto. Nunca apagues a linha — o histórico explica o gap.
- Este anexo tem de caber em leitura rápida: tabelas densas, zero prosa de
  método. Acima de ~300 linhas está a virar segundo manual — corta ou move para
  o MEGA.
