# Correções pedidas depois do lote 5 (backend e app)

Tudo feito **em local** (BACKEND do PC e telemóvel PTP-N49). **Nada foi publicado no Hetzner.**
Backend: 48 testes (11 novos em `BACKEND/tests/test_p9.py`). App: 74 testes. Patch reproduzível: `tools/patch_backend_p9.py`.

| Pedido | Backend | App | Estado |
|---|---|---|---|
| Documentos completos | `/rt/drivers/v2/documents` (motorista e veículo: tipo, estado, validade, nota) | Documentos mostra "Concluído", "Em análise" ou "Rejeitado" e "Válido até dd/mm/aaaa"; a rejeição mostra a nota | validado no telemóvel (Inês) |
| Horas online | tabela `driver_sessions`, aberta em `go_online` e fechada em `go_offline`; `onlineSeconds` no resumo semanal (inclui a sessão em curso) | linha "Online" em Rendimentos só se o servidor a envia | testes; sem captura (precisa de sessão com horas) |
| Fim da semana | `week_bounds` por data de calendário (segunda a segunda) em vez de +7x86400 s | o ecrã já tratava o fim; mantém | teste da semana da mudança de hora |
| Acentos nos ganhos | notas novas: "Tarifa", "Comissão 20%", "Frota …", "Recebido em dinheiro"; as antigas são corrigidas à saída (`_pretty_note`) | mostra o que vem | testes |
| Perfil | `get-profile-hub` já devolvia nome, avaliação, taxa de aceitação e veículo | Menu mostra o perfil real e o veículo no subtítulo | validado (Inês: 4,80 e 100 %) |
| Notificações | tabelas `notifications`, `/rt/inbox/notifications` e `/rt/inbox/mark-read`; criadas ao concluir uma viagem e no seed | Caixa de entrada e contador da barra vêm do servidor; abrir marca como lidas | testes; a BD local antiga não tem notificações (só as novas BD têm a de boas-vindas) |
| Rota | `/rt/navigation/v3/route` devolve polilinha, distância e duração: linha reta (30 km/h) ou OSRM real se `ROUTING_URL` estiver definido; nunca falha | a proposta pede a rota recolha → destino e desenha-a no mapa (círculo e quadrado) | validado (captura 83, linha reta) |

## O que continua por fazer (depende de uma decisão ou de um ativo teu)
- **Mapa real (SDK):** falta uma chave de Maps SDK para Android em `local.properties` (`MAPS_API_KEY`). O desenho do mapa mantém-se até lá.
- **Rota real:** pôr um servidor OSRM (ou outro) e definir `ROUTING_URL` no servidor. Sem isso a rota é uma linha reta.
- **Pontos e níveis (Qolari Pro):** não existe programa de pontos; só se justifica se o quiseres criar. A app já esconde "Pontos".
- **Envio de documentos por fotografia:** precisa de upload (multipart), onde guardar o ficheiro e estado "em análise" na consola.
- **Para publicar:** as tabelas novas (`driver_sessions`, `notifications`) exigem reiniciar o serviço no Hetzner (recarga a quente não chega) e ficam, com os 17 handlers do P6 e estes, num único pacote de ficheiros (`domain/models.py`, `domain/trips.py`, `domain/seed.py`, `apps/driver.py`, `apps/routing.py`).
