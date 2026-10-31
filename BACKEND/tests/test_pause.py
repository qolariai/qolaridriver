# -*- coding: utf-8 -*-
"""'Parar novos pedidos' (botao do planeador de viagem, print 2026-10-30).

O motorista continua ONLINE (a sessao nao fecha e as horas contam) mas fica fora do
despacho. Retomar volta a po-lo a receber propostas.
"""
from tests.conftest import login

ROSSIO = {"latitude": 38.7139, "longitude": -9.1394, "address": "Rossio"}
AEROPORTO = {"latitude": 38.7742, "longitude": -9.1342, "address": "Aeroporto"}


def _only_this_driver_online(client, admin, phone):
    for d in client.get("/api/drivers", headers=admin).json():
        if d["availability"] == "online":
            client.post(f"/api/drivers/{d['id']}/offline", headers=admin)
    for d in client.get("/api/drivers", headers=admin).json():
        if d["phone"] == phone:
            client.post(f"/api/drivers/{d['id']}/online", headers=admin)
            return d["id"]
    raise AssertionError("motorista nao encontrado")


def test_pause_keeps_the_driver_online_but_out_of_dispatch(client, admin):
    driver = login(client, "driver", "+351920000001")
    rider = login(client, "rider", "+351910000001")
    _only_this_driver_online(client, admin, "+351920000001")

    # 1) Online normal: available = true
    r = driver.post("/rt/drivers/v2/go-online",
                    {"positionEvent": {"location": {"latitude": 38.714, "longitude": -9.14}}})
    st = r.json()["driverTasks"]["driverState"]
    assert st["online"] is True and st["available"] is True

    # 2) Parar novos pedidos: continua online, deixa de estar available
    r = driver.post("/rt/drivers/v2/pause-dispatch", {"paused": True})
    assert r.status_code == 200, r.text
    st = r.json()["driverTasks"]["driverState"]
    assert st["online"] is True, "parar pedidos NAO pode ficar offline"
    assert st["available"] is False
    assert st["dispatchable"] is False

    # Com o motorista parado, um pedido novo nao lhe e proposto
    p = rider.post("/rt/riders/me/pickup",
                   {"requestPickupLocation": ROSSIO, "requestDestinationLocation": AEROPORTO})
    uuid = p.json()["trip"]["uuid"]
    t = client.get(f"/api/trips/{uuid}", headers=admin).json()
    assert t["offers"] == [], "sem propostas enquanto esta parado"

    # 3) Retomar: available volta a true
    r = driver.post("/rt/drivers/v2/pause-dispatch", {"paused": False})
    st = r.json()["driverTasks"]["driverState"]
    assert st["online"] is True and st["available"] is True

    # Limpeza: cancelar a viagem que ficou pendente
    client.post(f"/api/trips/{uuid}/action", json={"action": "cancel"}, headers=admin)


def test_pause_without_body_toggles(client, admin):
    """O botao manda o estado explicito; sem corpo o servidor alterna (compatibilidade)."""
    driver = login(client, "driver", "+351920000001")
    _only_this_driver_online(client, admin, "+351920000001")
    driver.post("/rt/drivers/v2/go-online",
                {"positionEvent": {"location": {"latitude": 38.714, "longitude": -9.14}}})

    st = driver.post("/rt/drivers/v2/pause-dispatch", {}).json()["driverTasks"]["driverState"]
    assert st["available"] is False
    st = driver.post("/rt/drivers/v2/pause-dispatch", {}).json()["driverTasks"]["driverState"]
    assert st["available"] is True


def test_going_offline_clears_the_pause(client, admin):
    driver = login(client, "driver", "+351920000001")
    _only_this_driver_online(client, admin, "+351920000001")
    driver.post("/rt/drivers/v2/go-online",
                {"positionEvent": {"location": {"latitude": 38.714, "longitude": -9.14}}})
    driver.post("/rt/drivers/v2/pause-dispatch", {"paused": True})

    driver.post("/rt/drivers/v2/go-offline")
    r = driver.post("/rt/drivers/v2/go-online",
                    {"positionEvent": {"location": {"latitude": 38.714, "longitude": -9.14}}})
    st = r.json()["driverTasks"]["driverState"]
    assert st["online"] is True and st["available"] is True, "voltar online limpa a pausa"
