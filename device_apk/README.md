# device_apk/ — origem dos artefactos (ponteiro, não duplicação)

O MEGA pede uma cópia intocada do artefacto em `device_apk/`. Neste projeto os
originais já vivem em pastas próprias e somam ~400 MB; duplicá-los aqui não acrescenta
integridade. O que garante a integridade é o **hash** e o facto de os ficheiros não
serem editados.

| App | Ficheiro real | SHA-256 |
|---|---|---|
| Driver | `ANDOIRD/DRIVER/source-original.apk` | `E13AFC35B3497B6AAECD939BCF63E14A8D23E138039FE3C4F1C257286103FD82` |
| Rider Lite (base) | `ANDOIRD/USER_LITE/spec_src/apk_instalado/lite_base.apk` | `B77A621177C065FEE63B99F81BBEAED1708642C38A2CC255ED8BE85244B597BE` |
| Rider Lite (split arm64) | `ANDOIRD/USER_LITE/spec_src/apk_instalado/lite_split_config.arm64_v8a.apk` | `5C99ECFBF1B5FD6C97AE748558AD8EF79CE99E6909CFDE57A42F2A63D3C7EA04` |
| Rider Lite (split mdpi) | `ANDOIRD/USER_LITE/spec_src/apk_instalado/lite_split_config.mdpi.apk` | `CB4749E7326DA271E7F0C161FC14B9244F99F48C0170ACB7B26DDE45488BC68B` |
| Fleet | `ANDOIRD/FLEET/original.apk` | `4F8DE80AC79BD2DDE7D5C1BEB598B3526FD34620048A61FA386AAAAEF49647D1` |

**Regras:** estes ficheiros são read-only; as cópias de trabalho (`qolari-*.apk`) não
substituem o original e os seus pixels são `repack_suspect`. Ver `access_plan.md` §5.
