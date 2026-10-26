# VALIDACAO.md - P7: validação ecrã a ecrã (recriação vs. original)

Método: (1) pares lado a lado das capturas (`captures/loteN/cmp_*.png`, feitos em cada lote); (2) verificação automática dos textos
(dumps de acessibilidade original vs. recriação; só o lote 1 tem dump da recriação); (3) revisão de geometria, cores, estados,
navegação e back. Estado: **sem divergências abertas que bloqueiem**; as restantes são aceites (D1-D7 em `STACK_DECISAO.md`) ou dependem de backend/SDK.

## 1. Verificação automática de textos (lote 1)
Textos da original (sem a barra de separadores nem marcadores do mapa), com "Uber" lido como "Qolari":

| Captura original | Presentes | Ausentes |
|---|---|---|
| 043 Definições | 12/12 | - |
| 044 Acessibilidade | 9/10 | subtítulo mais longo na original |
| 049 Audição | 5/5 | - |
| 045 Comunicação | 12/13 | "E-mail" (o backend só tem chamada e chat) |
| 046 Navegação | 10/10 | - |
| 047 Sons e voz | 11/12 | texto da original com erro de HTML (`avisos de&`) |
| 077 Sobre | 2/3 | versão 4.601.10000 (a nossa é 0.1.0) |

Total: 61/65 (94%). Todas as ausências aceites.

## 2. Divergências por lote
Legenda: **A** = aceite (decisão registada), **P** = por fazer, **B** = depende de backend ou de ativo externo.

### Lote 1 - Menu e Definições
| Divergência | Estado |
|---|---|
| Fonte do sistema em vez da Uber Move (quebras de linha ligeiramente diferentes) | A (D4) |
| Ícones próprios; ilustração própria da Audição | A (D4/D7) |
| Subtítulo do veículo no Menu é de exemplo | P (ligar a `vehicles`) |
| Cartão do perfil com dados fictícios, sem foto | B (`get-profile-hub`) |
| "Gerir conta", "Privacidade", "Editar endereço" sem destino | A (D7) |

### Lote 2 - Início e offline
| Divergência | Estado |
|---|---|
| Mapa desenhado (sem SDK) | B (chave de mapas) |
| Secções do painel (oportunidades, tendências, voos) de exemplo | B (serviço de recomendações inexistente) |
| Login só por telefone, sem Google/e-mail/reCAPTCHA | A (D6) |
| Folha "Já tem sessão iniciada" (seletor de contas) ausente | A |
| Banner de rede por baixo da barra de estado (a original estende-o até ao topo) | P (menor) |

### Lote 3 - Descobrir, Rendimentos, Caixa de entrada
| Divergência | Estado |
|---|---|
| Rendimentos sem "Online" (horas) nem "Pontos" | B (backend não tem) |
| Descobrir: filtros dentro da lista (na original ficam entre o título e a faixa de dias); dias passados sem esbater | P (menor) |
| Conteúdo de Descobrir e da Caixa de entrada de exemplo | B |
| Backend: fim da semana por segundos (erro na mudança de hora) | B (sugestão registada) |

### Lote 4 - Proposta e viagem
| Divergência | Estado |
|---|---|
| Sem capturas da original para recolha, PIN, em viagem, fim e ganhos (marcado `[inf]`) | B (a Driver rebrand não ficou online com a conta pendente) |
| Mapa sem rota nem percurso | B (SDK de mapas) |
| Cartão da proposta sem "Exclusivo"/"Correspondência"; barra de tempo é convenção própria | A |
| Sem som/vibração da proposta, navegação passo a passo, cancelar viagem | B (backend sem `/rt/navigation/v3/route`) |
| Descrições dos ganhos do backend sem acentos ("comissao") | B (sugestão registada) |

### Lote 5 - Segurança, Veículos, Documentos
| Divergência | Estado |
|---|---|
| Comfort, hub Informações, vídeo | A (D7) |
| Envio de documentos por foto, adicionar veículo, 112, gravar/partilhar viagem | A (precisam de câmara/serviços) |
| Documentos só "Concluído"/"Por enviar" (sem datas) | B (sugestão: endpoint de documentos) |
| Documentos com pendentes (captura 74_documentos_pendentes) e Pagamentos (75) | feito; validado no telemóvel com a motorista Inês (`cmp_C.png`) |

## 3. Navegação e back (revisão de código e percursos no telemóvel)
- Cinco separadores com o Menu como grafo aninhado: o separador Menu fica ativo em Definições, Ajuda, Veículos, Documentos e Sobre. Verificado.
- Back: de cada sub-ecrã volta ao anterior; do modo mapa volta ao painel; boas-vindas e login sem barra e sem regresso depois de entrar. Verificado.
- Janelas (Erro, PIN, Ferramentas de Segurança) fecham-se com Voltar. A avaliação não é cancelável por convenção própria.
- Estados vazio/erro/loading: Início (erro de arranque), Rendimentos (sem rede), Veículos e Documentos (a carregar/sem rede). Descobrir e Caixa de entrada não têm estado de erro porque o conteúdo é local.

## 4. Contraste e acessibilidade
Texto principal #111111 sobre branco; secundário #727272 sobre branco = 4,8:1 (cumpre AA). Alvos de toque de 48 dp nos botões de ícone.
Não validado com leitor de ecrã.

## 5. Conclusão
Paridade de UI e comportamento nos ecrãs com original capturada, com as divergências acima. Os pontos **B** dependem de backend ou do SDK de mapas;
os **P** são menores. Capturas do lote 5 completas. **P7 fechada.**

## 6. Correções posteriores
Ver `CORRECOES_POS_LOTE5.md`: documentos, horas online, semana por data, acentos, perfil, notificações e rota passaram de **B** a feitos (em local, sem publicar). Mantêm-se **B**: SDK de mapas (chave), rota real (OSRM), pontos, envio de documentos por foto.

## 7. Evidência dos ecrãs de viagem (MEGA)
Os ecrãs de proposta/aceitar/recolha/PIN/em viagem/fim/avaliação **não têm captura
original**. A forma foi tirada dos layouts `earner_trip_native_*`,
`earnertripflow_screenlayout` e `earnings_*` (`static`, `clean` do binário); os dados
vêm do nosso backend (`served`). Não são `live`. Ver `coverage.md` e `topology.md`.
O que depender do mapa/SDK continua **B**.

