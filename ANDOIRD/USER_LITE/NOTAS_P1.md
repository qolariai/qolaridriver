# P1 Uber Lite - estado da captura (versão 1.248.10001)

> **Contrato da app nova:** [`endpoints.json`](endpoints.json) — desenhado a partir de
> `BACKEND/apps/userlite.py`, com evidência `designed`. Não é o protocolo da Uber.
> A cobertura do ecossistema está em [`../../coverage.md`](../../coverage.md) e a
> topologia em [`../../topology.md`](../../topology.md).

Capturado até agora (só leitura, sem pedir viagens): `000` boas-vindas, `001` telefone/e-mail (número pré-preenchido ocultado), `002` seletor de país,
`003` depois de fechar, `010_inicio` (+ `_s1` com scroll) página inicial com sessão. A morada do utilizador aparece na `010`/`011`: **dado pessoal**, não vai para a recriação.

## Achados que mudam o plano
1. **A Lite desenha quase tudo numa WebView** (`android.webkit.WebView`). Não há layouts nativos nem ids de recursos para o conteúdo: a spec vem das capturas e da árvore de acessibilidade
   (só aparece 1-3 s depois de o ecrã carregar; a ferramenta `spec_tools_cap.py` já espera e repete o dump).
   Consequência: P2 (extração de layouts/tokens do APK) rende pouco na User; as cores e tipos medem-se nas capturas, como se fez nas medições da Driver.
2. Deslizar sobre o mapa desloca o mapa; para fazer scroll da página começa-se abaixo do mapa (a ferramenta já o faz).
3. A API da Lite é do conteúdo web (servidor da Uber); o contrato a reutilizar do nosso backend tem de ser confirmado na P4 pelo tráfego do telemóvel, não pelos APKs.

## Incidente
Durante a captura da barra de menu, a app **Biscate** (`com.qolari.biscate`) passou a primeiro plano sem eu a abrir (outra sessão ou uso do telemóvel). Parei, apaguei a captura `012` e não toquei em mais nada.
O último toque meu (1175,240) pode ter caído no cabeçalho da Biscate: sem efeito visível.

## Falta capturar
Menu (hambúrguer), "Para onde?" (pesquisa, sem escrever nem escolher destino), separadores Viajar/Entrega/Reserva, sugestões, atividade, conta, pagamentos, ajuda e estados offline/erro (precisa de cortar a rede).

## Atualização (captura retomada)
- Menu da Lite (hambúrguer): perfil, Ajuda, Wallet, Atividade, Uber Cash, Gerir conta, Promoções, Legal, Encerrar sessão (nunca tocado). Capturas: `011_inicio_retomada` (nome e foto ocultados),
  `021_wallet` (saldo e conta bancária ocultados; `_s1` anulada), `022_atividade` (sem viagens), `012_ajuda` (estado de carregamento, modo escuro).
- Incidentes: o Voltar do sistema na Lite saiu para a app anterior da pilha (Idealista), por isso passou a voltar-se só pela seta da app (`menu_loop.py`);
  a captura `023_gerir_conta` mostrou o Idealista e foi apagada. Nenhum toque meu foi dado noutras apps, só teclas Voltar.
- Em falta: Ajuda completa, Promoções, Legal, Gerir conta (abre fora da app), e o fluxo principal "Para onde?" até à estimativa de preços, **sem confirmar viagem**.

## Fluxo principal capturado (sem pedir viagem)
`031_pesquisa_aberta` (Planeie a sua viagem: recolha agora, para mim, destino, sugestões, "Definir localização no mapa", "Locais guardados") e
`032_apos_escolher_destino` (+ `_s1`): "Escolher uma viagem" com mapa, rota e categorias com preço e hora (UberX, Electric, UberXL, Comfort, Black, Comfort Electric,
Espere e poupe, UberXXL, Prioridade, Uber Pet), "Adicionar forma de pagamento" e o botão "Pedir UberX". **Não foi tocado nenhum botão "Pedir"**; o ecrã ficou aberto.
A morada do utilizador foi ocultada nas imagens e nos dumps. Cuidado a reter: o botão "Pedir" ocupa a zona inferior (y ≈ 2500-2660 px); nunca iniciar gestos aí.

## Estado ao parar
O Idealista voltou a ficar em primeiro plano (não fui eu) e a ferramenta recusou continuar. A Lite pode ter ficado em "Escolher uma viagem"; basta voltar com a seta da app (nada foi pedido).
Capturas feitas: arranque e login (logout), início, menu, Wallet, Atividade, pesquisa de destino, categorias e preços. Em falta: Promoções, Legal, Ajuda completa, "Definir localização no mapa", estados offline/erro.

## Capturas retomadas (fecho da P1 na Lite)
Feitas em leitura: `024_promocoes` (código promocional), `025_legal` (Direitos de autor, Termos, Privacidade, Fornecedores de dados, Localização, Contacto, Outro),
`020_ajuda_completa` (tópicos de ajuda, modo escuro), e os estados offline `050/051/052` (banner vermelho "Sem conexão de rede" na pesquisa; o início mantém-se, sem banner).
Offline: Wi-Fi e dados cortados cerca de 1 min por `offline_cap.py` e **repostos** (verificado: Wi-Fi e dados a 1).
Dados pessoais (morada, nome, e-mail, saldo, conta bancária) ocultados nas imagens e dumps. Ferramentas: `spec_tools_cap.py` (recusa tocar se a Lite não estiver à frente), `menu_loop*.py`, `offline_cap.py`.
Não capturado de propósito: Gerir conta (mostra dados pessoais), Atividade com viagens (a conta não tem), qualquer ecrã depois de "Pedir" (regra: nunca pedir viagem real).
