# Qolari Mobility — consola (backoffice)

React 19 + Vite + TypeScript + Leaflet. O build (`dist/`) é servido pelo backend em <http://127.0.0.1:8300>.

```bat
npm install
npm run build        :: depois de mexer no código
npm run dev          :: desenvolvimento em http://127.0.0.1:5174 (a /api vai para o backend na 8300)
```

| Secção | O que faz |
|---|---|
| Painel | Indicadores do dia, mapa ao vivo dos motoristas e viagens, 14 dias, top motoristas |
| Viagens | Lista com filtros; ficha com mapa, tarifa, cronologia, propostas e movimentos; ações (propor, avançar, cancelar, forçar estado) |
| Simulador | Pedir viagens clicando no mapa, pôr motoristas online/offline, movê-los e avançar viagens — sem telemóveis |
| Motoristas / Passageiros / Frotas / Veículos | Fichas, aprovação, suspensão/bloqueio, veículo atribuído, acessos à app Fleet, sessões e dispositivos |
| Documentos | Fila de verificação (carta, CC, TVDE, DUA, seguro…), envio de ficheiro, aprovar/recusar |
| Categorias e tarifas | Base, km, minuto, mínimo, taxas, dinâmica, ano mínimo do veículo, exemplo de preço |
| Promoções | Códigos % ou valor fixo, limites e validade |
| Finanças | Comissão, taxas de frota, dinheiro, saldos, pagamentos (pendente → pago), acertos, movimentos |
| Integração das apps | Por app: porta, cobertura do contrato da APK, tráfego ao vivo, endpoints por mapear com o modelo esperado |
| Definições | Parâmetros da plataforma, administradores (papéis), sessões, dispositivos, mensagens, registo de ações |

Tempo real: `/api/changes` (long-polling) recarrega as páginas quando a base de dados muda.
