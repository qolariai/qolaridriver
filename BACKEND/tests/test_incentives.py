# -*- coding: utf-8 -*-
"""Missoes, pontos e referral do motorista."""
from tests.conftest import login


def test_incentives_claim_and_referral(client):
    d = login(client, "driver", "+351920000001")
    x = d.get("/rt/drivers/v2/incentives")
    assert x.status_code == 200, x.text
    body = x.json()
    assert body["points"] > 0
    assert body["quests"]
    assert body["referral"]["code"].startswith("QOL-")

    claimable = [q for q in body["quests"] if q["canClaim"]]
    assert claimable, "o seed deve dar pelo menos uma missao concluida"
    q = claimable[0]
    before = float(d.post("/rt/earnings/get-balance-summary").json()["balanceAmount"])
    c = d.post(f"/rt/drivers/v2/quests/{q['uuid']}/claim")
    assert c.status_code == 200, c.text
    after = float(c.json() and d.post("/rt/earnings/get-balance-summary").json()["balanceAmount"])
    assert abs(after - (before + q["rewardCents"] / 100.0)) < 0.01
    assert d.post(f"/rt/drivers/v2/quests/{q['uuid']}/claim").status_code == 409

    r = d.post("/rt/drivers/v2/referrals", {"phone": "+351999999999"})
    assert r.status_code == 200, r.text
    assert r.json()["referral"]["invited"] >= 1
