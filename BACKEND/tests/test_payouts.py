# -*- coding: utf-8 -*-
"""Saldo, transferencias e extratos do motorista."""
from core.db import session_scope
from domain import finance
from domain.models import Driver
from tests.conftest import login

PHONE = "+351920000005"


def test_payouts_and_statements(client):
    with session_scope() as db:
        d = db.query(Driver).filter_by(phone=PHONE).first()
        finance.adjust(db, "driver", d.id, 5000, "credito de teste")

    w = login(client, "driver", PHONE)
    m = w.post("/rt/earnings/get-payout-methods")
    assert m.status_code == 200, m.text
    start = float(m.json()["balanceAmount"])
    assert start >= 50.0
    assert {x["id"] for x in m.json()["methods"]} == {"iban", "instant"}

    p = w.post("/rt/earnings/request-payout", {"amountCents": 2000, "method": "iban"})
    assert p.status_code == 200, p.text
    assert p.json()["payout"]["status"] == "pending"
    assert float(p.json()["balanceAmount"]) == round(start - 20.0, 2)

    i = w.post("/rt/earnings/instant-pay", {"amountCents": 1000})
    assert i.status_code == 200, i.text
    assert i.json()["payout"]["status"] == "paid"
    assert float(i.json()["balanceAmount"]) == round(start - 30.0, 2)

    h = w.post("/rt/earnings/get-payout-history").json()["payouts"]
    assert len(h) == 2 and {x["status"] for x in h} == {"pending", "paid"}

    s = w.post("/rt/earnings/get-statements").json()["statements"]
    assert len(s) == 6
    assert all("month" in x and "netCents" in x for x in s)
