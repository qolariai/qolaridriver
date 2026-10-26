#!/usr/bin/env bash
# Fecha uma APK reapontada para o servidor (depois de repoint_server.py apply + apktool b incremental):
#   finish_apk.sh <apk-atual> <apk-saida> <porta> <host> <keystore> [classesN.dex=<ficheiro> ...]
# 1) patch_apk_host: troca os dex dados + "http://127.0.0.1:PORTA" -> "https://HOST" nos recursos/assets
# 2) patch_apk_host: "127.0.0.1:PORTA" -> "HOST" (hosts sem esquema)   3) zipalign + apksigner   4) scan
set -euo pipefail
IN=$1; OUT=$2; PORT=$3; HOST=$4; KS=$5; shift 5
T=$(cd "$(dirname "$0")" && pwd)
BT="$T/../../ANDOIRD/USER/tools/build-tools/android-14"
TMP=$(mktemp -d)
python "$T/patch_apk_host.py" "$IN" "$TMP/p1.apk" "http://127.0.0.1:$PORT" "https://$HOST" "$@"
python "$T/patch_apk_host.py" "$TMP/p1.apk" "$TMP/p2.apk" "127.0.0.1:$PORT" "$HOST"
"$BT/zipalign.exe" -p -f 4 "$TMP/p2.apk" "$TMP/al.apk"
java -jar "$BT/lib/apksigner.jar" sign --ks "$KS" --ks-key-alias qolari --ks-pass pass:qolari123 \
    --v4-signing-enabled false --out "$OUT" "$TMP/al.apk"
java -jar "$BT/lib/apksigner.jar" verify "$OUT"
rm -rf "$TMP"
echo "== restos de 127.0.0.1:$PORT em $OUT:"
python "$T/scan_host.py" "$OUT" "127.0.0.1:$PORT" | tail -8
