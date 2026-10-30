# ui_spec — especificação estática da Uber Driver 4.600.10000

Gerada por `../spec_tools/extract_spec.py` a partir de `../spec_src/decoded_4600/` (apktool sobre `../spec_src/apk_instalado/base.apk`, puxado do telemóvel PTP-N49). O `sha256` do APK e a versão estão em `meta.json`. Esta árvore substitui `TESTE/ui_spec_android/`, que partia de um decode já renomeado (`com.qolari.driver`, versão 4.599.10004).

**Tudo aqui é REFERÊNCIA de fidelidade. Nada é copiado para a app nova.**

## Conteúdo

| Pasta ou ficheiro | O que é | Quantidade |
|---|---|---|
| `meta.json` | Versão, versionCode, SDKs, sha256 do APK | — |
| `manifest.json` | Activities, serviços, receivers, providers, permissões, deep links | 123 activities, 47 permissões, 50 deep links |
| `values/*.json` | Todos os `values*` (strings, cores, dimens, arrays, plurals, styles, attrs) | 172 pastas |
| `design_tokens.json` | Cores claro/escuro, dimens e temas | — |
| `layouts/` | Layouts XML | 2.693 |
| `drawables/` | Drawables XML e raster (PNG/WebP) | 4.486 XML + 292 raster |
| `mipmaps/` | Ícones | 51 |
| `anim/`, `animator/`, `interpolator/` | Animações | 119, 48, 18 |
| `color/` | Color selectors | 364 |
| `menu/`, `xml/` | Menus e configurações XML | 40, 25 |
| `fonts.json` | Só a lista das fontes (não copiadas, proprietárias) | 9 |
| `assets_index.json` | Só a lista dos assets | 1.265 |
| `inventory.json` | Contagens por categoria | — |

Fora desta pasta: `../stack.md` (bibliotecas e padrão arquitetural) e `../ux_capture/correlacao_layouts.csv` (capturas ↔ layouts).

## Diferenças em relação à extração anterior (`TESTE/ui_spec_android/`)

- Fonte: original 4.600.10000, em vez de um decode renomeado da 4.599.10004.
- Passam a existir: raster (292), animações (185), color selectors (364), menus, `styles` e `themes`, todos os idiomas, lista de fontes e de assets.
- Layouts: 2.693 (antes 2.697). Drawables XML: 4.486 (igual).

## Limites a ter presentes

- A versão extraída (4.600.10000) corresponde às capturas 000 a 030. As capturas 031 em diante são da 4.601.10000 (a app atualizou-se às 20:49 de 16-10). Ver `../ux_capture/versoes.csv`.
- A correlação capturas ↔ layouts usa resource-id. Mostra **candidatos**, não prova que o layout seja o ecrã inteiro. Ecrãs em Compose ou em páginas web ficam sem ids.
- O APK é o `base.apk`. Recursos de densidade e de arquitetura (`split_config.*`) não foram extraídos.
