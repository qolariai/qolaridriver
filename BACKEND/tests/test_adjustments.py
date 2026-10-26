# -*- coding: utf-8 -*-
"""Ajustes (portagens/tarifa manual), faturas e impostos."""
from tests.conftest import login

PHONE = "+351920000004"


def test_adjustment_request_and_console_approval(client, admin):
    d = login(client, "driver", PHONE)
    before = float(d.post("/rt/earnings/get-balance-summary").json()["balanceAmount"])

    r = d.post("/rt/earnings/request-adjustment", {
        "kind": "tolls", "amountCents": 350, "note": "Portagem A1",
    })
    assert r.status_code == 200, r.text
    uuid = r.json()["adjustment"]["uuid"]

    pending = client.get("/api/adjustments?status=pending", headers=admin).json()["items"]
    assert any(x["uuid"] == uuid for x in pending)

    a = client.patch(f"/api/adjustments/{uuid}", json={"status": "approved"}, headers=admin)
    assert a.status_code == 200, a.text
    assert a.json()["status"] == "approved"
    after = float(d.post("/rt/earnings/get-balance-summary").json()["balanceAmount"])
    assert abs(after - (before + 3.5)) < 0.01

    inv = d.post("/rt/earnings/get-invoices").json()["invoices"]
    assert len(inv) == 12 and all("tax" in x for x in inv)
    tax = d.post("/rt/earnings/get-tax-info").json()
    assert tax["year"] >= 2026 and "gross" in tax and "tax" in tax
