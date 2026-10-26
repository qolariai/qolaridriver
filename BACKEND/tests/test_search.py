# -*- coding: utf-8 -*-
"""Pesquisa de locais (geocoding com fallback no seed)."""
from tests.conftest import login


def test_driver_location_search_falls_back_to_seed(client):
    d = login(client, "driver", "+351920000001")
    r = d.get("/rt/location/search?q=aero")
    assert r.status_code == 200
    places = r.json()["places"]
    assert places and "Aeroporto" in places[0]["name"]
    assert places[0]["lat"] and places[0]["lng"]


def test_driver_location_search_empty_returns_seed(client):
    d = login(client, "driver", "+351920000001")
    places = d.get("/rt/location/search?q=").json()["places"]
    assert len(places) >= 5


def test_rider_places_search_keeps_contract(client):
    rider = login(client, "rider", "+351910000001")
    places = rider.get("/rt/lite/places?q=rossio").json()["places"]
    assert places and "Rossio" in places[0]["name"]
