# -*- coding: utf-8 -*-
"""Gera as respostas reais do backend para os testes do lote 4 (proposta e estados da viagem).

Corre contra uma BD temporaria (como os testes do backend), nao toca no servidor nem na BD de desenvolvimento.
Uso (na pasta BACKEND):  .venv\\Scripts\\python ..\\ANDOIRD\\DRIVER\\RECRIACAO\\tools\\gen_drive_fixtures.py <pasta de saida>
"""
import json
import os
import sys
import tempfile
from pathlib import Path

out = Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=True)

tmp = tempfile.mkdtemp(prefix="qolari-fixtures-")
os.environ.update({
    "DB_URL": f"sqlite:///{Path(tmp, 'f.db').as_posix()}", "LOG_DIR": str(Path(tmp, "logs")), "DATA_DIR": tmp,
    "RUN_TICKER": "0", "DRIVER_PORT": "18080", "EXTRA_APP_PORTS": "", "POLL_HOLD_S": "0.2", "GOOGLE_MAPS_KEY": "",
})
sys.path.insert(0, str(Path.cwd()))
sys.path.insert(0, str(Path.cwd() / "tests"))

from fastapi.testclient import TestClient  # noqa: E402

import main  # noqa: E402
from core.db import session_scope  # noqa: E402
from domain.models import Trip  # noqa: E402
from tests.conftest import login  # noqa: E402

ROSSIO = {"latitude": 38.7139, "longitude": -9.1394, "address": "Rossio"}
AEROPORTO = {"latitude": 38.7742, "longitude": -9.1342, "address": "Aeroporto"}


def save(name, data):
    (out / name).write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


def run(with_pin: bool, suffix: str):
    with TestClient(main.app) as client:
        admin = {"Authorization": "Bearer " + client.post("/api/auth/login", json={"email": "admin@qolari.local", "password": "admin"}).json()["token"]}
        rider = login(client, "rider", "+351910000001")
        driver = login(client, "driver", "+351920000001")
        for d in client.get("/api/drivers", headers=admin).json():
            if d["availability"] == "online":
                client.post(f"/api/drivers/{d['id']}/offline", headers=admin)
        driver.post("/rt/drivers/v2/go-online", {"positionEvent": {"location": {"latitude": 38.715, "longitude": -9.14}}})
        est = rider.post("/rt/riders/me/fare-estimate", {"pickupLocation": ROSSIO, "destination": AEROPORTO}).json()
        vvid = est["packageVariants"][0]["vehicleViewId"]
        p = rider.post("/rt/riders/me/v2/pickup", {"pickupRequest": {
            "requestPickupLocation": {"targetLocation": ROSSIO}, "requestDestinationLocation": {"targetLocation": AEROPORTO},
            "vehicleViewId": vvid}})
        trip_uuid = p.json()["trip"]["uuid"]
        if with_pin:
            with session_scope() as db:
                t = db.query(Trip).filter_by(uuid=trip_uuid).first()
                t.pin = "4821"
        if suffix == "":
            save("offer.json", driver.post("/rt/drivers/unified-offers-v3").json())
            save("tasks_idle.json", driver.post("/rt/drivers/v2/available").json())
        offer_uuid = driver.post("/rt/drivers/unified-offers-v3").json()["data"]["offers"][0]["offerUUIDs"][0]
        save(f"tasks_to_pickup{suffix}.json", driver.post("/rt/drivers/accept-offers", {"offerUUIDs": [offer_uuid]}).json())
        save(f"tasks_at_pickup{suffix}.json", driver.post("/rt/trips/v2/start-waiting", {"uuid": trip_uuid}).json())
        if with_pin:
            driver.post("/rt/trips/v2/confirm-pin-is-verified", {"uuid": trip_uuid})
            save("tasks_pin_verified.json", driver.post("/rt/drivers/v2/available").json())
        save(f"tasks_on_trip{suffix}.json", driver.post("/rt/trips/v2/begin", {"uuid": trip_uuid, "pin": "4821" if with_pin else ""}).json())
        driver.post("/rt/trips/v2/end", {"uuid": trip_uuid})
        save(f"earnings_trip{suffix}.json", driver.post("/rt/earnings/get-trip", {"uuid": trip_uuid}).json())
        return trip_uuid


run(False, "")
run(True, "_pin")
print("fixtures em", out)
