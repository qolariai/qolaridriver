# Prompt para o novo agente — Qolari Driver + Qolari Lite

## 0. O teu papel

Continuas um projeto de **recriação fiel das apps Uber Driver e Uber Lite** para a Qolari. O trabalho já está avançado e validado no Honor. O utilizador vai agora explicar-te, com **capturas de vídeo da Uber/Uber Lite**, o funcionamento real de vários ecrãs e **o que cada botão faz**. A tua missão é ouvir, observar, mapear e implementar — sem inventar comportamentos.

**Regra de ouro:** não desenhes mapas, etiquetas, ruas ou rotas à mão. Usa sempre o mapa nativo do Google e a rota real do Google Directions. O utilizador já rejeitou expressamente mapas/etiquetas desenhados e linhas retas.

## 1. Missão imediata

1. Pede ao utilizador os vídeos/capturas e a explicação de cada botão.
2. Antes de mexer no código, produz uma tabela de levantamento com:
   - ecrã e estado (online, oferta, a caminho, chegou, em viagem, concluída, cancelada, sem motoristas, offline);
   - cada botão visível;
   - o que faz na Uber real (navegação, chamada, mensagem, cancelamento, PIN, avaliação, filtros, etc.);
   - o que já existe na réplica e o que falta.
3. Confirma com o utilizador os pontos ambíguos. Só depois implementas, **um bloco de cada vez**, com build, instalação no Honor, captura e comparação.
4. No fim de cada bloco, mostra a captura da réplica ao lado da referência e diz o que mudou.

## 2. Contexto do projeto

- Raiz: `C:\xampp\htdocs\QOLARI\PROJETOS OFICIAIS\QOLARI DRIVER`
- Driver: `ANDOIRD\DRIVER\RECRIACAO` — package `com.qolari.drivereplica`, back-end **8091**.
- Lite (passageiro): `ANDOIRD\USER_LITE\RECRIACAO` — package `com.qolari.userlite`, back-end **8090**.
- Back-end: `BACKEND` — arranca com `BACKEND\.venv\Scripts\python.exe server.py` (a partir da pasta `BACKEND`). Portas: 8090 (Rider), 8091 (Driver), 8300 (consola), 3000 (Fleet), 8092 (gRPC).
- Base de dados: `BACKEND\data\qolari.db`.
- Notas do projeto: `.qolari\notes.md` (lê primeiro).
- Especificações: `PLANO_SPEC_UIUX_DRIVER.md`, `PLANO_SPEC_UIUX_USER.md`, `ux_reference/`.
- Capturas reais: `ANDOIRD\DRIVER\ux_capture` e `ANDOIRD\USER_LITE\ux_capture` (Lite com backup em `ux_capture_backup_20261028`).

## 3. Estado atual (não refazer)

### Mapas
- Google Maps SDK nativo nas duas apps; sem fallback de imagem estática e sem etiquetas desenhadas.
- Driver: mapa centrado na **posição real do telemóvel** (`AppGraph.location.lastKnown()`); marcador do motorista nessa posição; etiquetas de cidade em `#6E7580`/halo branco, peso 0.6.
- Lite: pickup no **GPS atual**, com reverse geocoding; mapa do Início centrado no fix real; zoom +/− e controlos do mapa.
- Rotas: **Google Directions** (`overview=full`, polilinha descodificada) nas duas apps. O Lite guarda a rota em `roadRoute` para o polling não a substituir pela reta; marcador de destino; enquadramento com padding para o traçado não ficar sob os cartões.
- Cliente HTTP das APIs Google com DNS IPv4-only (OkHttp) por causa do IPv6 quebrado do Honor.

### Fluxo de viagem
- Lite pede, Driver recebe oferta, aceita, chega, PIN, inicia, termina; Lite vê PIN, “Em viagem”, total e avaliação.
- Oferta TTL: 60 s (`settings.offer_timeout_s`).
- PIN: o Driver só inicia com PIN verificado (`pinVerified`); a folha do PIN fecha sozinha quando verifica; o slide de recolha só aparece depois.
- Viagens concluídas: 80, 82, 84 e 85. A 85 foi a validação final no Honor: pickup GPS “R. Elias Garcia 181, 2700-708 Amadora”, destino “Av. Lusíada, Lisboa”, cotação 5,07 €, PIN 6670, total final 4,07 €, avaliações 5/5.

### Ecrãs já fechados
- Lite: Início, Pesquisa, Opções de viagem, Viagem, Menu, Wallet, Atividade, Promoções, Ajuda, Legal, **Gerir conta** (separadores Casa / Informações pessoais / Segurança / Privacidade e Dados, perfil, três cartões, “Sugestões” com “Começar a verificação” e morada de casa).
- Driver: Início, mapa online, oferta, recolha, PIN, viagem, fim/avaliação, Descobrir, Rendimentos, Caixa de entrada, Menu.
- `HomeFragment` do Lite só reabre viagens **em curso** e apenas a partir do Início; corrigido o crash `action_home_to_active cannot be found`.

### APKs
- `ANDOIRD\DRIVER\qolari-driver-final.apk`
- `ANDOIRD\USER_LITE\qolari-lite-final.apk`
- O Driver final foi regenerado depois de corrigir o pin “Recolha” que ficava no mapa após terminar a viagem.

## 4. Regras técnicas e de produto

- **Fidelidade primeiro**: tipografia, espaçamentos, cores, ícones, estados e microcopy iguais às capturas/vídeos.
- **Nada de dados inventados** quando o back-end os pode fornecer; se faltar dado, diz explicitamente.
- **Mapa real**: nunca desenhar ruas/etiquetas; usar Google Maps + Directions.
- **Português de Portugal** na UI; manter o tom da Uber.
- Não apagar trabalho do utilizador. Antes de remover ficheiros/APKs, confirma.
- Não versionar a chave Google Maps nem ficheiros `local.properties`.
- O Honor é o dispositivo principal; o Mi é secundário e instável.
- O utilizador pode estar a usar o telemóvel (ex.: app bancária com captura bloqueada). Se o ecrã não for a app, **não insistas nem faças taps às cegas**; pede para libertar o telemóvel.

## 5. Comandos úteis

```powershell
$env:JAVA_HOME="C:\Program Files\Android\Android Studio\jbr"

# Build Driver
& "C:\xampp\htdocs\QOLARI\PROJETOS OFICIAIS\QOLARI DRIVER\ANDOIRD\DRIVER\RECRIACAO\gradlew.bat" `
  -p "C:\xampp\htdocs\QOLARI\PROJETOS OFICIAIS\QOLARI DRIVER\ANDOIRD\DRIVER\RECRIACAO" assembleDebug --offline

# Build Lite
& "C:\xampp\htdocs\QOLARI\PROJETOS OFICIAIS\QOLARI DRIVER\ANDOIRD\USER_LITE\RECRIACAO\gradlew.bat" `
  -p "C:\xampp\htdocs\QOLARI\PROJETOS OFICIAIS\QOLARI DRIVER\ANDOIRD\USER_LITE\RECRIACAO" assembleDebug --offline

# Honor
adb -s AQCK024C17020494 reverse tcp:8090 tcp:8090
adb -s AQCK024C17020494 reverse tcp:8091 tcp:8091
adb -s AQCK024C17020494 install -r --no-streaming "ANDOIRD\DRIVER\RECRIACAO\app\build\outputs\apk\debug\app-debug.apk"
adb -s AQCK024C17020494 install -r --no-streaming "ANDOIRD\USER_LITE\RECRIACAO\app\build\outputs\apk\debug\app-debug.apk"

# Captura
cmd /c "adb -s AQCK024C17020494 exec-out screencap -p > .clone\capture\nome.png"
```

- Honor: `AQCK024C17020494`, 1280×2800 @560dpi, dados móveis (Wi-Fi desligado).
- Mi: `18a959c4`, 1080×2340 @440dpi (instável).
- Login demo: Lite `+351910000001`; Driver `+351920000001`; código `0000`.
- Antes de testar, repõe sempre o `adb reverse`; as ligações USB caem com frequência.
- O back-end tem de estar a ouvir 8090/8091; se não estiver, arranca-o e espera pela mensagem das portas.

## 6. O que ainda falta fazer (além do que o utilizador vai explicar)

Isto é trabalho já identificado. Não esperes que o utilizador o repita:

1. **Levantamento dos vídeos**: transformar cada vídeo numa lista ecrã → estado → botão → ação e marcar o que já está feito.
2. **Semântica de todos os botões**: pesquisa, radar, filtros, menu, perfil, wallet, atividade, ajuda, promoções, legal, conta, opções de viagem, pagamento, promo, cancelar, fechar, avaliação, caixa de entrada, rendimentos, descobrir, oportunidades.
3. **Estados em falta**: offline, sem rede, erro, sem motoristas, cancelamento pelo passageiro/motorista, oferta expirada, PIN errado, excedeu tentativas, processo morto/restaurado, voltar atrás em todos os ecrãs.
4. **Tarifa**: decidir e alinhar o modelo. Hoje o total final usa o tempo real, por isso uma viagem simulada de 72 s fica abaixo do preço upfront (ex.: 5,07 € → 4,07 €). A Uber cobra o upfront; define com o utilizador se a Qolari deve cobrar o estimado, o real, ou o mínimo.
5. **Gerir conta**: decidir se fica a foto real da captura ou o avatar com inicial; os dados atuais são demo (ANA PEREIRA / ana@exemplo.pt). Não misturar com a conta do vídeo sem o utilizador pedir.
6. **Validação visual completa**: comparar todos os ecrãs com as capturas/vídeos, com atenção a fontes, pesos, espaçamentos, ícones, sombras, alturas e microcopy.
7. **Driver**: validar Descobrir, Rendimentos, Caixa de entrada, Menu, perfil e notificações contra as capturas; verificar dados reais do back-end.
8. **Lite**: validar Wallet, Atividade, Promoções, Ajuda, Legal, tópicos legais e todos os separadores de Gerir conta.
9. **Robustez**: rotação, processo morto, retomar viagem, duplo toque, back stack, sem crashes; o X da viagem concluída deve voltar ao Início e ficar lá.
10. **Mi**: instalar os APKs finais e validar os mapas e o fluxo; se estiver instável, registar e não bloquear o Honor.
11. **Chave Google Maps**: restringir por package/SHA-1 antes de publicar; retirar do repositório.
12. **APKs finais**: regenerar depois de cada alteração, copiar para `qolari-driver-final.apk` / `qolari-lite-final.apk`, limpar APKs antigos e atualizar `.qolari/notes.md`.

## 7. Critérios de aceitação

- Cada botão explicado pelo utilizador tem comportamento implementado e testado.
- Cada ecrã comparado com a referência, no Honor, com captura lado a lado.
- Nenhuma rota reta ou mapa desenhado à mão.
- Fluxo completo Lite → Driver → Lite sem falhas: pedido, oferta, aceitação, chegada, PIN, início, fim, total e avaliação.
- Sem crashes ao navegar, voltar, rodar ou retomar.
- APKs finais atualizados e notas escritas.

## 8. Primeira resposta esperada de ti

Não comeces a programar ainda. Responde com:

1. a lista de ficheiros/notas que leste;
2. a tabela de levantamento dos vídeos que o utilizador fornecer;
3. as dúvidas que precisas de esclarecer;
4. a ordem proposta de implementação, do ecrã mais crítico para o menos crítico.
