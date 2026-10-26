# -*- coding: utf-8 -*-
"""Analytics/monitorizacao das apps por gRPC (uber.uflurry.v2.protos.UflurryV2/PublishMessages).

A Driver manda por aqui os eventos e os registos internos (wk6/monitoring), que nao vao ao logcat. Guardamos o
corpo protobuf em data/uflurry/<app>-<ms>.bin (os ultimos KEEP) para diagnostico, e respondemos com a
mensagem vazia (sucesso). Ler: `python -c "import re,sys;print(re.findall(rb'[ -~]{6,}', open(f,'rb').read()))"`.
"""
import time

import config
from apps.grpc import grpc_handles

DIR = config.DATA_DIR / "uflurry"
KEEP = 300


@grpc_handles(("driver", "rider", "fleet"), "/uber.uflurry.v2.protos.UflurryV2/PublishMessages")
def publish_messages(app, fields, raw):
    try:
        DIR.mkdir(parents=True, exist_ok=True)
        (DIR / f"{app}-{int(time.time() * 1000)}.bin").write_bytes(raw or b"")
        files = sorted(DIR.glob("*.bin"))
        for f in files[:-KEEP]:
            f.unlink(missing_ok=True)
    except OSError:
        pass
    return b""
