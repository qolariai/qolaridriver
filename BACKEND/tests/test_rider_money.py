# -*- coding: utf-8 -*-
"""Gorjeta, recibo, top-up e contestacao no Rider."""
from core.db import session_scope
from domain.models import Trip
from tests.conftest import login


def _completed_trip():
    with session_scope() as db:
        t = (db.query(Trip)
             .filter(Trip.state == "completed", Trip.tip_cents == 0, Trip.fare.isnot(None))
             .order_by(Trip.id.desc()).first())
        assert t is not None, "o seed deve ter viagens concluidas"
        return t.uuid, t.rider.phone, t.fare


def test_tip_receipt_dispute_and_topup(client, admin):
    uuid, phone, fare = _completed_trip()
    r = login(client, "rider", phone)

    before = r.get(f"/rt/lite/trips/{uuid}/receipt").json()["receipt"]
    assert before["totalCents"] == fare
    assert before["lines"][0]["amountCents"] == fare

    t = r.post(f"/rt/lite/trips/{uuid}/tip", {"amountCents": 200})
    assert t.status_code == 200, t.text
    assert t.json()["trip"]["tipCents"] == 200
    assert t.json()["trip"]["canTip"] is False

    after = r.get(f"/rt/lite/trips/{uuid}/receipt").json()["receipt"]
    assert after["totalCents"] == fare + 200
    assert any(x["label"] == "Gorjeta" for x in after["lines"])

    d = r.post(f"/rt/lite/trips/{uuid}/dispute", {"reason": "valor cobrado errado"})
    assert d.status_code == 200, d.text
    thread_uuid = d.json()["thread"]["uuid"]
    threads = client.get("/api/support?status=open", headers=admin).json()["items"]
    assert any(x["uuid"] == thread_uuid for x in threads)

    w = r.get("/rt/lite/wallet").json()
    before_cash = w["cash"]["cents"]
    up = r.post("/rt/lite/wallet/topup", {"amountCents": 1000})
    assert up.status_code == 200, up.text
    assert up.json()["cash"]["cents"] == before_cash + 1000
    assert r.get("/rt/lite/wallet").json()["cash"]["cents"] == before_cash + 1000
