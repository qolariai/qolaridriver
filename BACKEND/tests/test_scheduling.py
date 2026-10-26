# -*- coding: utf-8 -*-
"""Agendamento de viagens no Rider."""
import time

from tests.conftest import login

PICKUP = {"latitude": 38.7139, "longitude": -9.1394, "address": "Rossio"}
DROPOFF = {"latitude": 38.7742, "longitude": -9.1342, "address": "Aeroporto"}


def test_scheduled_trip_waits_and_rejects_too_soon(client):
    r = login(client, "rider", "+351910000001")
    when = int(time.time()) + 3600
    res = r.post("/rt/lite/request", {"pickup": PICKUP, "dropoff": DROPOFF, "scheduledAt": when * 1000})
    assert res.status_code == 200, res.text
    trip = res.json()["trip"]
    assert trip["state"] == "requested"
    assert trip["scheduledAt"] == when * 1000

    # ainda nao ha propostas: o despacho espera pela hora
    from core.db import session_scope
    from domain.models import Offer, Trip
    with session_scope() as db:
        t = db.query(Trip).filter_by(uuid=trip["uuid"]).first()
        assert db.query(Offer).filter_by(trip_id=t.id).count() == 0

    r.post(f"/rt/lite/trips/{trip['uuid']}/cancel", {"reason": "teste"})

    soon = int(time.time()) + 60
    bad = r.post("/rt/lite/request", {"pickup": PICKUP, "dropoff": DROPOFF, "scheduledAt": soon * 1000})
    assert bad.status_code == 400
