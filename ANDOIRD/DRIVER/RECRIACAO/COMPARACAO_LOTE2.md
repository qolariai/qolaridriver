# Lote 2 - Início e offline: recriação vs. original

Dispositivo PTP-N49, pacote `com.qolari.drivereplica`, backend local do laboratório por USB (`adb reverse tcp:8091 tcp:8091`).
Capturas em `captures/lote2/`; folhas lado a lado (original à esquerda): `cmp_A.png` (boas-vindas, telefone, painel), `cmp_B.png` (bloqueado, mapa, erros), `cmp_C.png` (mapa e arranque sem servidor).

## O que foi feito
| Ecrã / estado | Original | Recriação |
|---|---|---|
| Boas-vindas (`WelcomeFragment`) | 031 | 20_boas_vindas |
| Telefone (`LoginPhoneFragment`) | 032 | 21_login_telefone |
| Código de 4 dígitos + erro "Código errado" | passo seguinte ao 033 (não capturado) | 23_codigo_errado |
| Página inicial, painel (`HomeFragment`) | 000, 060, 060_s1..s3 | 24, 25, 26 |
| Painel com "Ações necessárias" (dados do servidor) | 060 | 28_inicio_bloqueado |
| Modo mapa (`MapFragment`, sem barra de separadores) | 110 | 27_modo_mapa |
| Janela "Erro" ao puxar para atualizar sem servidor | 115b, 125b | 29_refresh_sem_servidor |
| Arranque sem servidor (barra escura + "Ocorreu um erro") | 117, 120 | 30_arranque_sem_servidor |
| Banner "Nenhuma rede detetada" (todos os separadores) | 110, 115, 120 | 31_banner_sem_rede_inicio, 32_banner_sem_rede_menu; 33 = rede reposta (sem banner) |

Dados reais do backend: estado online e ações necessárias (`app-launch`, `fetch-online-blockers`), ficar online/offline (`go-online`, `go-offline`),
login por telefone + código (`/rt/identity/oauth2/token`). Sessão guardada em DataStore; o destino inicial é Boas-vindas sem sessão.
"Terminar sessão" e "Mudar de conta" (Menu) limpam a sessão e voltam às boas-vindas.

## Comportamento (ux_behavior.md §4) coberto por teste
`HomeViewModelTest` (7) e `LoginViewModelTest` (8): arranque sem rede não abre janela e mostra o estado de erro; puxar para atualizar falhado com dados já carregados abre a janela "Erro";
ficar online com ações por resolver volta a verificar em vez de avançar; a ação falhada mantém o estado; o código errado limpa o campo e mostra o erro; o telefone aceita 9 dígitos.
Total da suite: 22 testes a passar (`ConfigTest` 4, `PreferencesStoreTest` 3).

## Erros encontrados e corrigidos
1. O campo do código perdia o erro: limpar o texto disparava o `TextWatcher`, que apagava o erro. O campo agora segue o estado sem avisar o ViewModel.
2. Campo do código como `numberPassword` + autofill: o teclado engolia dígitos. Passou a `number` sem autofill.
3. Texto de erro do arranque ficava por baixo do botão "Ficar online": o mapa encolhe para 180dp nesse estado, como na original.
5. Banner sem rede não aparecia com os dados móveis desligados: `onLost` lia `activeNetwork`, que ainda devolvia a rede que acabara de cair. O `NetworkMonitor` usa agora só os argumentos das chamadas (`onCapabilitiesChanged`, `onLost`). Validado no telemóvel com os dados desligados ~15 s.
4. Pílula "Qolari Pro" do mapa estava ilegível (fundo claro): cinzento escuro.

## Diferenças que ficam (e porquê)
- **Mapa desenhado** (espaço reservado, `MapPlaceholderView`): sem SDK de mapas nem chave; entra no lote 4 (chave em `local.properties`). Os marcadores "1-4 min" e as zonas de procura são de exemplo.
- **Secções de baixo do painel** (oportunidades, tendências, voos): conteúdo de exemplo; a original recebe-o de um serviço de recomendações que o nosso backend não tem.
- **Login só por telefone** (D6): a original oferece também Google e e-mail; o backend do laboratório só tem telefone + código, por isso não há botão que não funcione. Sem reCAPTCHA.
- **Boas-vindas**: a original mostra por cima a folha "Já tem sessão iniciada" (seletor de contas); aqui não há contas guardadas em cache.
- **Banner de rede por baixo da barra de estado**, e não por trás dela (a original estende o vermelho até ao topo).
- **Botão "Ficar offline"** (estado online) e o ecrã online do mapa: sem captura da original com este estado completo (`[n/t]`), desenhados pela convenção da app.
- Fonte e ícones próprios (D4).

## Para validar ainda
- Ligar o ambiente a `https://driver.qolari.com`: trocar `AppConfig.environment` (agora `USB` para os testes do lote 2, com `adb reverse tcp:8091 tcp:8091` e `BACKEND/server.py` local). Os handlers das 17 lacunas do backend continuam por publicar.
- O banner de rede foi testado só com os dados móveis (o Wi-Fi do aparelho estava desligado); com Wi-Fi o `NetworkMonitor` comporta-se igual (mesma chamada).
