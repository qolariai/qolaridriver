# Data Safety — checklist para a Play Console

Preencher na Play Console > App content > Data safety. Modelo, não substitui a revisão
da política de privacidade nem a validação legal.

| Tipo de dado | Recolhido | Partilhado | Finalidade | Obrigatório | Eliminável |
|---|---|---|---|---|---|
| Nome | sim | não | conta, viagem | sim | sim |
| Telefone | sim | com o outro lado da viagem | conta, segurança | sim | sim |
| E-mail | sim | não | conta, suporte | opcional | sim |
| Localização aproximada/exata | sim | com o outro lado durante a viagem | mapa, rotas, dispatch | sim | sim |
| Histórico de viagens | sim | não | serviço, financeiro | sim | sim |
| Documentos/fotos (motorista) | sim | não | verificação/KYC | sim | sim |
| Informação financeira (método) | sim | processador `<...>` | pagamento | sim | sim |
| Identificadores do dispositivo | sim | não | sessão, push | sim | sim |
| Diagnóstico/crash | `<sim/não>` | `<...>` | estabilidade | não | sim |

## Segurança

- [ ] Dados cifrados em trânsito (HTTPS em produção).
- [ ] Dados cifrados em repouso (backups/DB) `<...>`.
- [ ] Pedido de eliminação de conta documentado e testado.
- [ ] Acesso por role e auditoria no backoffice.
- [ ] Retenção definida e implementada (job de limpeza).
- [ ] Subprocessadores listados (Google Maps/Places, hosting, pagamentos).
- [ ] Política de privacidade pública com URL.
- [ ] Sem ads/analytics não declarados.

## Bloqueios antes de submeter

- Conta de developer Play Console e keystore de release.
- Revisão legal da política e dos termos.
- Testes internos/fechados e conteúdo de classificação.
- FCM (se as notificações forem declaradas) — ver `PUSH_FCM.md`.
