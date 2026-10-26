# Lote 4 - Proposta e viagem: recriação vs. original

Dispositivo PTP-N49, pacote `com.qolari.drivereplica`, backend local por USB (`adb reverse tcp:8091 tcp:8091`), motorista João e passageiras do seed.
Capturas em `captures/lote4/`; folha `cmp_A.png` (original da proposta à esquerda; a seguir os estados da recriação).

## Fontes
- **Proposta**: capturas originais `100_online_001..013` (cartão com produto, preço "após dedução de taxa de serviço", recolha, viagem, "Aceitar"/"Correspondência", "Radar de viagens").
- **Recolha, PIN, em viagem, fim, ganhos**: **não existem capturas da original** (a conta real não aceitou viagens, e o Driver rebrand `com.qolari.driver` ficou bloqueado por não aceitar a conta Fernando/pendente,
  só dava "Estamos com problemas técnicos" ao ficar online). Estes estados seguem o contrato real do backend (`DriverTasks`) e a convenção da app, marcados `[inf]` no ux_behavior.
- Os JSON de teste (`app/src/test/resources/drive/`) são respostas reais do backend (`tools/gen_drive_fixtures.py`, BD temporária).

## O que foi feito
| Estado | Recriação |
|---|---|
| Online + "Radar de viagens" (contador) | 50 |
| Cartão da proposta, barra de tempo, ✕ recusar, "Aceitar" | 51 |
| A caminho da recolha: "Recolher <nome>", morada, tarifa, deslizar "cheguei" | 52 |
| Chegou: tempo de espera a contar, botão do PIN (só se o passageiro o pediu) | 53 |
| Folha do PIN, erro por tentativa (textos do servidor), certo = fecha | 54, 55, 56 |
| Em viagem: "Deixar <nome>", deslizar "terminar" | 57 |
| Fim: ganhos da viagem (tarifa, comissão, frota) e avaliação 1-5 / saltar | 58, 59 |
| Rendimentos com as viagens feitas (total 10,70 €, barra do dia, lista) | 67 |

- **Sondagem a 4 s** à proposta e às tarefas; a viagem em curso volta a aparecer ao reabrir a app (o estado vem do servidor).
- **Posição** do aparelho enviada ao servidor (`uploadpositions`) enquanto está online; pede a permissão de localização ao ficar online.
- **Deslizar para confirmar** em chegar, recolher e terminar (um toque sem querer teria custos para o passageiro). Abaixo de 85% do percurso volta ao início.
- O PIN compara-se localmente como na original (`PinVerificationTaskData`) e só então avisa o servidor (`confirm-pin-is-verified`); o máximo de tentativas vem do servidor.

## Testes (23 novos, suite total 58)
`DriveTest`: leitura da proposta e das tarefas contra respostas reais; ciclo proposta → aceitar → chegar → PIN → iniciar → terminar → avaliar; recusa e expiração; PIN errado e limite de tentativas;
viagem ativa prevalece sobre proposta; sondagem falhada mantém o estado; posição enviada; passar offline repõe tudo.

## Erros encontrados e corrigidos
1. Testes pendurados: a sondagem em ciclo avançava o tempo virtual sem fim. A sondagem automática desliga-se nos testes.
2. Atalhos do mapa (relâmpago, tendências, escudo) ficavam por baixo do cartão da proposta; escondem-se com proposta ou viagem.
3. Linhas dos ganhos vinham em minúsculas ("tarifa", "comissao 20%"): primeira letra em maiúscula. **Sugestão para o backend:** acentos ("comissão") e capitalização nas descrições do `earnings/get-trip`.

## Diferenças que ficam
- **Mapa desenhado**: não mostra a rota nem o percurso até à recolha como a original (a rota a preto entre recolha e destino). Entra com o SDK de mapas e a chave (`local.properties`).
- Cartão da proposta: sem o selo "Exclusivo" nem "Correspondência" (variantes da original que o backend não tem); o botão é sempre "Aceitar" (azul). Uma barra de tempo azul no topo é convenção própria `[inf]`.
- Sem som nem vibração da proposta, sem navegação passo a passo (`/rt/navigation/v3/route` não existe no backend), sem cancelar viagem pelo motorista, sem deslizar para "ligar ao passageiro".
- O tempo da proposta vem do servidor (20 s por omissão; no servidor Hetzner está a 60 s para testes).

## Estado do laboratório ao fechar
Backend local parado, `adb reverse` removido, motoristas do seed repostos online (Carlos, Marta, Diana, Paulo; João offline), permissão de notificações da `com.qolari.driver` revogada (tinha-lha dado para o diagnóstico).
No servidor Hetzner **só li** (logs e BD em modo leitura); não foi gravado nada nem criada nenhuma viagem lá. A conta Fernando (pendente) continua sem poder ficar online.
