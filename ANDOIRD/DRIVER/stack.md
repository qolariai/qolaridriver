# stack.md (gerado por stack_report.py)

Fonte: `C:\xampp\htdocs\QOLARI\PROJETOS OFICIAIS\QOLARI DRIVER\ANDOIRD\DRIVER\spec_src\decoded_4600` (apktool, read-only). Ficheiros smali: 249158 em 28 pastas.

## Toolkit de UI

- Compose: presente (1422 classes em `androidx/compose`).
- Layouts XML: 2693 (Views), menus: 40.
- Conclusao: a app mistura Views XML e Compose; ver contagens acima antes de escolher a stack da recriacao.

## Bibliotecas detetadas (pacote em smali)

| Biblioteca | Pacote | Classes | Presente em |
|---|---|---|---|
| Compose (UI) | `androidx/compose` | 1422 | smali, smali_classes4 |
| ConstraintLayout | `androidx/constraintlayout` | 173 | smali, smali_classes4 |
| Material Components | `com/google/android/material` | 569 | smali, smali_classes21, smali_classes5 |
| Navigation (AndroidX) | `androidx/navigation` | 35 | smali_classes4 |
| Retrofit | `retrofit2` | 145 | smali_classes20, smali_classes23, smali_classes4 |
| OkHttp | `okhttp3` | 43 | smali_classes22, smali_classes23, smali_classes4 |
| Gson | `com/google/gson` | 119 | smali, smali_classes11, smali_classes22, smali_classes5 |
| Moshi | `com/squareup/moshi` | 69 | smali, smali_classes23, smali_classes5 |
| RxJava | `io/reactivex` | 1172 | smali_classes13, smali_classes21, smali_classes22, smali_classes3, smali_classes4, smali_classes8 |
| Coroutines | `kotlinx/coroutines` | 84 | smali_classes17, smali_classes22, smali_classes4 |
| Dagger | `dagger` | 3 | smali_classes3 |
| Hilt | `dagger/hilt` | 0 | - |
| RIBs (Uber) | `com/uber/rib` | 137 | smali_classes12, smali_classes15, smali_classes18, smali_classes19, smali_classes3, smali_classes8, smali_classes9 |
| Room | `androidx/room` | 49 | smali, smali_classes5 |
| DataStore | `androidx/datastore` | 0 | - |
| WorkManager | `androidx/work` | 106 | smali, smali_classes21, smali_classes5 |
| Glide | `com/bumptech/glide` | 248 | smali_classes5 |
| Coil | `coil` | 143 | smali, smali_classes13, smali_classes18, smali_classes22, smali_classes5 |
| Picasso | `com/squareup/picasso` | 63 | smali, smali_classes22, smali_classes5 |
| Lottie | `com/airbnb/lottie` | 100 | smali_classes5 |
| ExoPlayer | `com/google/android/exoplayer2` | 0 | - |
| Media3 | `androidx/media3` | 762 | smali_classes4 |
| Protobuf | `com/google/protobuf` | 523 | smali, smali_classes5 |
| gRPC | `io/grpc` | 475 | smali_classes20, smali_classes22, smali_classes3 |
| Google Maps SDK | `com/google/android/gms/maps` | 86 | smali_classes18, smali_classes5 |
| Play Services Location | `com/google/android/gms/location` | 44 | smali, smali_classes22, smali_classes5 |
| Firebase Messaging (push) | `com/google/firebase/messaging` | 20 | smali, smali_classes5, smali_classes6 |
| Firebase Crashlytics | `com/google/firebase/crashlytics` | 0 | - |
| Firebase (geral) | `com/google/firebase` | 155 | smali, smali_classes5, smali_classes6 |
| Braintree | `com/braintreepayments` | 71 | smali_classes19, smali_classes22, smali_classes5, smali_classes6 |
| Twilio | `com/twilio` | 231 | smali_classes17, smali_classes22, smali_classes5, smali_classes9 |
| Facebook SDK | `com/facebook` | 7 | smali_classes5 |
| AppsFlyer | `com/appsflyer` | 0 | - |
| Adjust | `com/adjust` | 0 | - |
| Sentry | `io/sentry` | 0 | - |
| Adyen | `com/adyen` | 88 | smali_classes15, smali_classes21, smali_classes23, smali_classes5 |
| Stripe | `com/stripe` | 0 | - |
| Google Pay | `com/google/android/gms/wallet` | 0 | - |

## Padrao arquitetural (sufixos de nomes de classe)

| Sufixo | Classes |
|---|---|
| ViewModel | 692 |
| Presenter | 925 |
| Interactor | 862 |
| Router | 1773 |
| Repository | 17 |
| Activity | 138 |
| Fragment | 4 |
| Worker | 112 |

Nota: nomes ofuscados reduzem estas contagens; servem so como indicio.
