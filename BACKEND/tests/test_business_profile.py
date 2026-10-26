# -*- coding: utf-8 -*-
"""Perfil empresarial/delegado do motorista."""
from tests.conftest import login


def test_business_profile_and_delegates(client):
    d = login(client, "driver", "+351920000006")
    b = d.post("/rt/drivers/v2/business-profile", {
        "action": "save", "active": True, "companyName": "Transfers Lda",
        "vat": "500111222", "email": "ops@transfers.pt",
    })
    assert b.status_code == 200, b.text
    assert b.json()["business"]["active"] is True

    a = d.post("/rt/drivers/v2/business-profile", {
        "action": "add_delegate", "delegateName": "Rui", "delegatePhone": "+351910000088",
    })
    assert a.status_code == 200, a.text
    assert a.json()["business"]["delegates"][0]["name"] == "Rui"

    g = d.get("/rt/drivers/v2/business-profile").json()["business"]
    assert g["companyName"] == "Transfers Lda" and g["delegates"]

    r = d.post("/rt/drivers/v2/business-profile", {
        "action": "remove_delegate", "delegatePhone": "+351910000088",
    })
    assert r.json()["business"]["delegates"] == []
