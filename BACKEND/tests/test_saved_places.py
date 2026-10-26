# -*- coding: utf-8 -*-
"""Locais guardados do Rider."""
from tests.conftest import login


def test_saved_places_crud(client):
    r = login(client, "rider", "+351910000001")
    a = r.post("/rt/lite/places/saved", {"label": "Aeroporto", "placeId": "aeroporto"})
    assert a.status_code == 200, a.text
    pid = a.json()["savedPlace"]["id"]
    assert pid

    rows = r.get("/rt/lite/places/saved").json()["places"]
    assert any(x["id"] == pid and x["name"] == "Aeroporto" for x in rows)

    assert r.c.delete(f"/rt/lite/places/saved/{pid}", headers=r.headers()).status_code == 200
    assert not any(x["id"] == pid for x in r.get("/rt/lite/places/saved").json()["places"])
