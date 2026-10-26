# -*- coding: utf-8 -*-
"""Perfil empresarial, familia/teens e Uber One."""
from tests.conftest import login

PICKUP = {"latitude": 38.7139, "longitude": -9.1394, "address": "Rossio"}
DROPOFF = {"latitude": 38.7742, "longitude": -9.1342, "address": "Aeroporto"}


def test_account_extras_business_family_uber_one(client):
    r = login(client, "rider", "+351910000002")

    b = r.post("/rt/lite/account/business", {"companyName": "ACME", "vat": "500000000", "email": "a@acme.pt"})
    assert b.status_code == 200, b.text
    assert b.json()["business"]["active"] is True and b.json()["business"]["companyName"] == "ACME"

    f = r.post("/rt/lite/account/family", {"name": "Rita", "phone": "+351910000099", "teen": True})
    assert f.status_code == 200, f.text
    assert f.json()["family"]["members"][0]["teen"] is True
    assert f.json()["family"]["code"].startswith("FAM-")

    u = r.post("/rt/lite/account/uber-one", {"action": "subscribe"})
    assert u.status_code == 200, u.text
    assert u.json()["uberOne"]["active"] is True

    q = r.post("/rt/lite/quote", {"pickup": PICKUP, "dropoff": DROPOFF})
    assert q.status_code == 200, q.text
    assert q.json()["promo"] and q.json()["promo"]["code"] == "UBERONE"

    x = r.get("/rt/lite/account/extras").json()
    assert x["business"]["companyName"] == "ACME"
    assert x["family"]["members"][0]["name"] == "Rita"
    assert x["uberOne"]["active"] is True

    rem = r.post("/rt/lite/account/family", {"phone": "+351910000099", "action": "remove"})
    assert rem.json()["family"]["members"] == []

    c = r.post("/rt/lite/account/uber-one", {"action": "cancel"})
    assert c.json()["uberOne"]["active"] is False
