# Lote 5 - Segurança, Veículos, Documentos e informação: recriação vs. original

PTP-N49, backend local por USB. Capturas em `captures/lote5/` (`cmp_B.png` documentos e menu). Originais: 014-024, 070-089.

## O que foi feito
| Ecrã | Original | Recriação | Dados |
|---|---|---|---|
| Conjunto de Ferramentas de Segurança (folha; abre do Menu e do escudo do Início) | 014 | 70 | conteúdo próprio |
| Centro de segurança (secções e linhas) | 017, 018, 024 | 71 | conteúdo próprio |
| Veículo e "Os seus veículos" | 080, 082 | 72, 73 | **reais** (`/rt/drivers/v2/vehicles`) |
| Documentos (estado de cada requisito) | 083 | 74 | **reais** (pendentes vêm de `fetch-online-blockers`) |
| Seguro, Formas de pagamento, Informações fiscais | 072, 075, 074 | página informativa de texto | próprio |

Toolkit: tudo em Views (a original usa Views no Centro/Fiscais/Pagamentos e páginas web nos Veículos/Documentos/Seguro, D7).

## Testes: 9 novos (`Lote5Test`), suite total 67
Título do veículo (ano, marca, modelo), lista vazia, documento pendente por bloqueio, vários pendentes, conteúdo de segurança, carregamento e falha (mantém dados).

## Fora de âmbito (decidido, D7: conteúdo da Uber não se replica)
- **Comfort** (025-030: passos, lições, vídeo, normas) e **hub Informações**: conteúdo e vídeo proprietários do programa Uber Comfort; sem equivalente no nosso backend.
- **Envio de documentos por fotografia** (084-089), **Adicionar veículo** (081) e **assistência 112, gravação de viagem, partilha de viagem, comprovativo**: precisam de câmara, telefone ou serviços próprios. As linhas abrem uma página de texto, sem fingir a função.
- Mapa de veículos (carro em 3D da captura 080) e cartão verde de "oportunidades de veículos": imagens/conteúdo da Uber.

## Diferenças e limitações
- Documentos: o backend só indica os pendentes (em bloqueios), por isso só se vê "Concluído" ou "Por enviar"; não há datas de validade. **Sugestão:** endpoint de documentos do motorista.
- Subtítulo do veículo no Menu ainda é de exemplo (`Fixtures`); ligar ao mesmo pedido.
- Depois de carregar o aparelho, capturaram-se Documentos com pendentes ("Por enviar", motorista Inês) e Pagamentos (`cmp_C.png`).
- Estado ao fechar: backend local parado e `adb reverse` removido.
