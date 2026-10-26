# -*- coding: utf-8 -*-
"""Rota do mapa da Rider (contrato designed)."""
from tests.conftest import login

ANA = "+351910000001"


def test_userlite_route_returns_polyline(client):
    r = login(client, "rider", ANA).post("/rt/lite/route", {
        "origin": {"latitude": 38.753, "longitude": -9.145},
        "destination": {"latitude": 38.72553, "longitude": -9.14997},
    })
    assert r.status_code == 200
    body = r.json()
    assert len(body["polyline"]) >= 2
    assert body["polyline"][0]["latitude"] == 38.753
    assert body["distanceMeters"] > 0
    assert body["source"] in {"straight_line", "osrm"}


def test_userlite_route_without_points_is_empty(client):
    r = login(client, "rider", ANA).post("/rt/lite/route", {})
    assert r.status_code == 200 and r.json()["polyline"] == []


def test_route_cache_reuses_result(monkeypatch):
    from apps import routing
    monkeypatch.delenv("ROUTING_URL", raising=False)
    routing._cache.clear()
    a, b = (38.7139, -9.1394), (38.7742, -9.1342)
    first = routing.route(a, b)
    second = routing.route(a, b)
    assert first == second
    assert routing._cache
    assert first["source"] == "straight_line"
