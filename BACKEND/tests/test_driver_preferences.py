# -*- coding: utf-8 -*-
"""Preferencias de despacho: modo destino, area, auto-aceitacao e pausa."""
from tests.conftest import login


def test_driver_preferences_and_break(client):
    d = login(client, "driver", "+351920000004")

    p = d.get("/rt/drivers/v2/preferences").json()["preferences"]
    assert p["destinationMode"] is False and p["autoAccept"] is False

    r = d.post("/rt/drivers/v2/preferences", {
        "destinationMode": True,
        "destinationAddress": "Aeroporto de Lisboa",
        "destinationLat": 38.7742,
        "destinationLng": -9.1342,
        "areaMode": True,
        "areaLabel": "Lisboa",
        "areaLat": 38.7139,
        "areaLng": -9.1394,
        "areaRadiusKm": 12,
        "autoAccept": True,
    })
    assert r.status_code == 200, r.text
    p = r.json()["preferences"]
    assert p["destinationMode"] and p["areaMode"] and p["autoAccept"]
    assert p["areaRadiusKm"] == 12

    b = d.post("/rt/drivers/v2/break", {"minutes": 15})
    assert b.status_code == 200, b.text
    assert b.json()["preferences"]["breakActive"] is True

    b = d.post("/rt/drivers/v2/break", {"resume": True})
    assert b.json()["preferences"]["breakActive"] is False

    # limpeza: desligar preferencias para nao afetar os outros testes
    d.post("/rt/drivers/v2/preferences", {"destinationMode": False, "areaMode": False, "autoAccept": False})
