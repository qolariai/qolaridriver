# ux_behavior.md — Rider (User Lite)

**Evidência:** 32 PNG `live`/`clean` do fluxo pré-auth e escolha de viagem; os ecrãs
pós-pedido são `designed`/`served` (o contrato nativo foi desenhado porque a referência
Lite é WebView). Ver `coverage.md` e `VALIDACAO_MEGA.md`.

## Grafo de navegação (observado + implementado)

```
Boas-vindas → telefone → código → Início
Início → Pesquisa → Escolher viagem → Viagem ativa → Início
Início → Promoções
Início → Menu → Carteira / Atividade / Promoções / Ajuda / Legal / Gerir conta
Viagem ativa → cancelar (confirmação) → Início
Viagem ativa → fim → avaliação / saltar → Início
```

## Gestos e scroll

- Scroll vertical em Início, Pesquisa, Escolher viagem, Carteira, Atividade, Ajuda,
  Legal e Gerir conta.
- Pull-to-refresh no Início (`SwipeRefreshLayout`).
- Mapa: zoom 1.0–2.2 em passos de 1.25 e recentrar na localização.
- Teclado: formulários sobem com o `windowSoftInputMode`; o botão de ação fica visível.
- Back: pop do destino atual; nas telas terminais, “Voltar ao início” limpa a pilha.

## Animações e feedback

- Transições padrão do Navigation Component; sem animações custom capturadas.
- Snackbar para confirmação (ex.: avaliação enviada) e diálogos para cancelar viagem e
  terminar sessão.
- Banner de rede no topo (`MainActivity`) para offline; estados de erro têm retry.
- Sem FCM: o tempo real é `ramen` long-poll + polling de 2 s na viagem ativa.

## Formulários

- Telefone: prefixo `+351`, validação de dígitos; “Encontrar a minha conta”.
- Código: 4 dígitos; o botão de laboratório preenche `0000`; reenviar é uma ação real.
- Conta: nome e e-mail com `PATCH /rt/lite/account`; casa com
  `POST /rt/lite/account/home`; validação e erro por campo.
- Promoções: código com `POST /rt/lite/promotions/apply`; erro de código inválido.

## Estados por ecrã

- `default`, `loading` (skeleton/placeholder com forma), `empty` (mensagem + ação) e
  `error` (mensagem + retry). Offline é coberto pelo banner global.
- Ecrãs de captura: Início, Pesquisa, Escolher viagem, Carteira, Atividade, Menu.
- Ecrãs desenhados: viagem ativa, PIN, fim, avaliação, conta.

## Limites declarados

Mapa Google Maps (chave em `local.properties`); miniaturas decorativas desenhadas. Sem
login social/reCAPTCHA/IAP, sem FCM, sem entrega/reserva/paragens/cidade. As entradas sem
equivalente foram removidas da UI; ver `capabilities.md` §5.
