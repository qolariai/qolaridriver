# -*- coding: utf-8 -*-
"""Fila do aeroporto."""
from tests.conftest import login


def test_airport_queue_join_position_and_leave(client):
    d = login(client, "driver", "+351920000001")
    d.post("/rt/drivers/v2/go-online", {"positionEvent": {"location": {"latitude": 38.7742, "longitude": -9.1342}}})

    j = d.post("/rt/drivers/v2/airport-queue", {"action": "join"})
    assert j.status_code == 200, j.text
    assert j.json()["joined"] is True
    assert j.json()["position"] >= 1
    assert j.json()["waiting"] >= 1

    other = login(client, "driver", "+351920000002")
    other.post("/rt/drivers/v2/go-online", {"positionEvent": {"location": {"latitude": 38.7742, "longitude": -9.1342}}})
    o = other.post("/rt/drivers/v2/airport-queue", {"action": "join"}).json()
    assert o["position"] == j.json()["position"] + 1

    left = other.post("/rt/drivers/v2/airport-queue", {"action": "leave"})
    assert left.json()["joined"] is False

    d.post("/rt/drivers/v2/airport-queue", {"action": "leave"})
    d.post("/rt/drivers/v2/go-offline")
    other.post("/rt/drivers/v2/go-offline")
