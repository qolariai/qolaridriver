# -*- coding: utf-8 -*-
"""Modo Destino (lupa do mapa, video/print de 2026-10-31).

O motorista marca para onde quer ir e so recebe viagens cujo DESTINO fica a menos de
`destination_mode_radius_km` (7 km) desse ponto. Tem `destination_mode_daily_filters`
(2) filtros por dia.
"""
from tests.conftest import login
import pytest

POMBAL = {"latitude": 38.7255, "longitude": -9.1500, "address": "Praca Marques de Pombal"}
BAIXA = {"latitude": 38.7106, "longitude": -9.1422, "address": "Baixa-Chiado"}
LIBERDADE = {"latitude": 38.7197, "longitude": -9.1450, "address": "Avenida da Liberdade"}
CASCAIS = {"latitude": 38.6979, "longitude": -9.4215, "address": "Cascais"}


@pytest.fixture(autouse=True)
def _clear_destination_mode(client, admin):
    """A BD e partilhada pela sessao de testes. Um destino deixado ligado filtraria as
    viagens dos testes seguintes, por isso desliga-se em TODOS os motoristas e cancelam-se
    as viagens que os testes deste modulo deixaram pendentes."""
    from core.db import Session
    from domain.models import Driver, Trip, Offer, now as _now

    def limpa():
        client.post("/api/drivers/reset-destination-filters", headers=admin)
        # A fila push e da sessao de testes inteira. Este modulo gera propostas que ficam
        # pendentes (o motorista nunca as aceita); os testes seguintes leem a 1.a mensagem
        # e apanhariam uma vazia. Drena-se a fila do motorista no fim.
        try:
            drv = login(client, "driver", "+351920000001")
            drv.get("/ramen/sessions/s1/messages")
        except Exception:
            pass
        db = Session()
        try:
            for d in db.query(Driver).all():
                d.dest_lat = d.dest_lng = None
                d.dest_label = ""
                # Os testes deste modulo poem so UM motorista online (para o destino ser
                # previsivel). A BD e da sessao toda, por isso repoe-se o estado de origem:
                # online o 0001 e offline os restantes, que e como o seed os deixa.
                d.availability = "online" if d.phone == "+351920000001" else "offline"
                d.paused = False
            for t in db.query(Trip).filter(
                Trip.state.in_(("requested", "accepted", "arrived", "in_progress"))
            ).all():
                t.state = "cancelled"
                t.cancelled_at = _now()
                t.cancelled_by = "system"
                t.cancel_reason = "teste"
            for o in db.query(Offer).filter(Offer.state == "pending").all():
                o.state = "withdrawn"
                o.responded_at = _now()
            db.commit()
        finally:
            db.close()

    limpa()
    yield
    limpa()


def _only_this_driver_online(client, admin, phone):
    for d in client.get("/api/drivers", headers=admin).json():
        if d["availability"] == "online":
            client.post(f"/api/drivers/{d['id']}/offline", headers=admin)
    for d in client.get("/api/drivers", headers=admin).json():
        if d["phone"] == phone:
            client.post(f"/api/drivers/{d['id']}/online", headers=admin)
            return d["id"]
    raise AssertionError("motorista nao encontrado")


def _trip(client, rider, destination):
    p = rider.post("/rt/riders/me/pickup",
                   {"requestPickupLocation": POMBAL, "requestDestinationLocation": destination})
    return p.json()["trip"]["uuid"]


def _offers(driver):
    r = driver.post("/rt/drivers/unified-offers-v3", {})
    return r.json()["data"]["offers"]


def test_destination_mode_blocks_trips_outside_the_radius(client, admin):
    driver = login(client, "driver", "+351920000001")
    rider = login(client, "rider", "+351910000001")
    _only_this_driver_online(client, admin, "+351920000001")
    driver.post("/rt/drivers/v2/go-online",
                {"positionEvent": {"location": {"latitude": 38.714, "longitude": -9.14}}})

    # Sem modo destino, a viagem para Cascais (24 km) chega na mesma.
    uuid_longe = _trip(client, rider, CASCAIS)
    assert _offers(driver), "sem Modo Destino qualquer viagem e proposta"
    client.post(f"/api/trips/{uuid_longe}/action", json={"action": "cancel"}, headers=admin)

    # Ligar o destino na Baixa-Chiado: Cascais fica fora dos 7 km -> nao chega.
    r = driver.post("/rt/drivers/v2/destination-mode",
                    {"latitude": BAIXA["latitude"], "longitude": BAIXA["longitude"],
                     "label": BAIXA["address"]})
    assert r.status_code == 200, r.text
    assert r.json()["destinationMode"]["enabled"] is True

    uuid_longe = _trip(client, rider, CASCAIS)
    assert _offers(driver) == [], "destino fora do raio nao pode ser proposto"
    client.post(f"/api/trips/{uuid_longe}/action", json={"action": "cancel"}, headers=admin)

    # A Av. da Liberdade fica a ~2,9 km -> dentro do raio, chega.
    uuid_perto = _trip(client, rider, LIBERDADE)
    assert _offers(driver), "destino dentro do raio tem de ser proposto"
    client.post(f"/api/trips/{uuid_perto}/action", json={"action": "cancel"}, headers=admin)


def test_destination_mode_has_two_filters_a_day(client, admin):
    driver = login(client, "driver", "+351920000001")
    _only_this_driver_online(client, admin, "+351920000001")
    driver.post("/rt/drivers/v2/go-online",
                {"positionEvent": {"location": {"latitude": 38.714, "longitude": -9.14}}})

    # Zera a contagem do dia para o teste nao depender do que ja foi usado.
    client.post("/api/drivers/reset-destination-filters", headers=admin)

    r1 = driver.post("/rt/drivers/v2/destination-mode",
                     {"latitude": BAIXA["latitude"], "longitude": BAIXA["longitude"]})
    assert r1.json()["destinationMode"]["filtersLeft"] == 1

    r2 = driver.post("/rt/drivers/v2/destination-mode",
                     {"latitude": BAIXA["latitude"], "longitude": BAIXA["longitude"]})
    assert r2.json()["destinationMode"]["filtersLeft"] == 0

    # O terceiro tem de ser recusado.
    r3 = driver.post("/rt/drivers/v2/destination-mode",
                     {"latitude": BAIXA["latitude"], "longitude": BAIXA["longitude"]})
    assert r3.status_code >= 400, "o 3.o filtro do dia tem de falhar"
    assert "no_filters_left" in r3.text


def test_turning_destination_mode_off_does_not_spend_filters(client, admin):
    driver = login(client, "driver", "+351920000001")
    _only_this_driver_online(client, admin, "+351920000001")
    driver.post("/rt/drivers/v2/go-online",
                {"positionEvent": {"location": {"latitude": 38.714, "longitude": -9.14}}})
    client.post("/api/drivers/reset-destination-filters", headers=admin)

    driver.post("/rt/drivers/v2/destination-mode",
                {"latitude": BAIXA["latitude"], "longitude": BAIXA["longitude"]})
    r = driver.post("/rt/drivers/v2/destination-mode", {"enabled": False})
    assert r.status_code == 200, r.text
    state = r.json()["destinationMode"]
    assert state["enabled"] is False
    assert state["filtersLeft"] == 1, "desligar nao devolve nem gasta filtros"
