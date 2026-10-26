# FCM — push em background (implementado)

**Estado:** implementado para **Qolari Driver** (`com.qolari.drivereplica`) e **Qolari Rider
Lite** (`com.qolari.userlite`) no projeto Firebase `qolari-driver-prod`.

## O que está feito

- As 6 apps antigas (`com.qolari.driver/rider/fleet` Android+iOS) foram removidas do
  projeto; ficaram só as duas Android das recriações.
- `google-services.json` em:
  - `ANDOIRD/DRIVER/RECRIACAO/app/google-services.json`
  - `ANDOIRD/USER_LITE/RECRIACAO/app/google-services.json`
- Plugin `com.google.gms.google-services` + `firebase-messaging` (BOM 33.7.0) nos dois
  Gradle.
- `QolariMessagingService` nas duas apps:
  - `onNewToken` regista o token no backend (`POST /rt/devices/push-token`);
  - `onMessageReceived` mostra notificação com canal `qolari_default` e abre a app;
  - `QolariApp` cria o canal; `MainActivity` pede `POST_NOTIFICATIONS` e re-regista o
    token quando há sessão.
- Backend:
  - `apps/fcm.py` envia FCM HTTP v1 com a conta de serviço
    `firebase-adminsdk-fbsvc@qolari-driver-prod.iam.gserviceaccount.com`;
  - `domain/push.py` continua a gravar no `ramen` e, se houver token, enfileira o push;
  - token no `Device.push_token`; endpoint de registo em `apps/identity.py`.
- Chave da conta de serviço: `BACKEND/data/firebase-service-account.json` (ignorada pelo
  `.gitignore`; papel `roles/firebasecloudmessaging.admin`).
- API `fcm.googleapis.com` ativa.

## Teste realizado

- Driver e Rider receberam o token (DB `devices.push_token`), com subject correto
  (João/Ana).
- `fcm._send` devolveu OK para os dois tokens; notificação `qolari_default` apareceu no
  Honor.
- `domain.push.send` para `push_driver_unified_offers_v3` gerou notificação real.

## Configuração (produção)

```env
FCM_PROJECT_ID=qolari-driver-prod
FCM_SERVICE_ACCOUNT=/opt/qolari/BACKEND/data/firebase-service-account.json
```

O ficheiro da conta de serviço não vai para o repositório. Se a chave for rodada,
substituir o ficheiro e reiniciar o backend.

## Limites

- Sem token/Internet, o `ramen` continua a ser o fallback.
- O push é um acelerador; a fonte de verdade é o backend.
- iOS ficou fora (as apps iOS antigas foram removidas e não há recriação iOS).
