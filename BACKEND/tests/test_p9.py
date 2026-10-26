# -*- coding: utf-8 -*-
"""Correcoes pedidas depois do lote 5: documentos, horas online, semana por data, acentos, rota e notificacoes."""
import datetime as dt
import time

from apps import driver as drv
from apps import routing
from tests.conftest import login

CARLOS = "+351920000001"
INES = "+351920000006"    # por aprovar, documentos pendentes
ROSSIO = {"latitude": 38.7139, "longitude": -9.1394, "address": "Rossio"}
AEROPORTO = {"latitude": 38.7742, "longitude": -9.1342, "address": "Aeroporto"}


def test_documents_lists_driver_and_vehicle_documents(client):
    d = login(client, "driver", CARLOS).post("/rt/drivers/v2/documents").json()
    kinds = {x["kind"] for x in d["driverDocuments"]}
    assert {"carta_conducao", "cartao_cidadao", "certificado_tvde", "registo_criminal"} <= kinds
    assert {x["kind"] for x in d["vehicleDocuments"]} == {"dua", "seguro", "inspecao"}
    carta = next(x for x in d["driverDocuments"] if x["kind"] == "carta_conducao")
    assert carta["status"] == "approved" and carta["expiresOn"] == "2029-12-31" and carta["title"] == "Carta de condução"


def test_pending_driver_sees_pending_documents(client):
    d = login(client, "driver", INES).post("/rt/drivers/v2/documents").json()
    assert {x["status"] for x in d["driverDocuments"]} == {"pending"}


def test_week_bounds_use_calendar_days_even_across_dst():
    # 2026-10-25 (domingo) e a semana da mudanca de hora na Europa: a semana seguinte comeca a segunda 26.
    ts = int(time.mktime((2026, 10, 24, 12, 0, 0, 0, 0, -1)))
    start, end = drv.week_bounds(ts)
    s, e = dt.datetime.fromtimestamp(start), dt.datetime.fromtimestamp(end)
    assert (s.weekday(), s.hour, s.minute) == (0, 0, 0) and (e.weekday(), e.hour, e.minute) == (0, 0, 0)
    assert (e.date() - s.date()).days == 7


def test_online_seconds_counts_open_and_closed_sessions(client):
    from core.db import session_scope
    from domain import trips
    from domain.models import Driver, DriverSession, now
    with session_scope() as db:
        d = db.query(Driver).filter_by(phone="+351920000003").first()   # Joao, offline no seed
        db.query(DriverSession).filter_by(driver_id=d.id).delete()
        t = now()
        db.add(DriverSession(driver_id=d.id, started_at=t - 7200, ended_at=t - 3600))   # 1 h fechada
        db.add(DriverSession(driver_id=d.id, started_at=t - 600))                        # 10 min em curso
        db.flush()
        assert trips.online_seconds(db, d.id, t - 86400, t + 60) in range(4200, 4300)    # 3600 + ~600 (+- 1 min)
        assert trips.online_seconds(db, d.id, t - 1800, t + 60) in range(600, 700)       # so a aberta
        db.query(DriverSession).filter_by(driver_id=d.id).delete()


def test_go_online_and_offline_open_and_close_a_session(client, admin):
    from core.db import session_scope
    from domain.models import DriverSession
    driver = login(client, "driver", "+351920000002")      # Marta
    driver.post("/rt/drivers/v2/go-offline")
    driver.post("/rt/drivers/v2/go-online", {"positionEvent": {"location": {"latitude": 38.73, "longitude": -9.14}}})
    with session_scope() as db:
        from domain.models import Driver
        d = db.query(Driver).filter_by(phone="+351920000002").first()
        assert db.query(DriverSession).filter_by(driver_id=d.id, ended_at=None).count() == 1
    driver.post("/rt/drivers/v2/go-offline")
    with session_scope() as db:
        assert db.query(DriverSession).filter_by(driver_id=d.id, ended_at=None).count() == 0
    # o resumo semanal traz as horas online
    weekly = driver.post("/rt/earnings/get-weekly-earnings-view").json()
    assert "onlineSeconds" in weekly and weekly["onlineSeconds"] >= 0


def test_new_ledger_notes_are_capitalized_with_accents(client, admin):
    from core.db import session_scope
    from domain.models import Rider
    with session_scope() as db:       # passageiro novo: os do seed podem ter viagens ativas de outros testes
        if not db.query(Rider).filter_by(phone="+351910000099").first():
            db.add(Rider(first_name="Teste", last_name="P9", phone="+351910000099"))
    rider = login(client, "rider", "+351910000099")
    driver = login(client, "driver", "+351920000001")
    for dd in client.get("/api/drivers", headers=admin).json():
        if dd["availability"] == "online":
            client.post(f"/api/drivers/{dd['id']}/offline", headers=admin)
    driver.post("/rt/drivers/v2/go-online", {"positionEvent": {"location": {"latitude": 38.715, "longitude": -9.14}}})
    est = rider.post("/rt/riders/me/fare-estimate", {"pickupLocation": ROSSIO, "destination": AEROPORTO}).json()
    p = rider.post("/rt/riders/me/v2/pickup", {"pickupRequest": {
        "requestPickupLocation": {"targetLocation": ROSSIO}, "requestDestinationLocation": {"targetLocation": AEROPORTO},
        "vehicleViewId": est["packageVariants"][0]["vehicleViewId"]}})
    assert "trip" in p.json(), p.text
    uuid = p.json()["trip"]["uuid"]
    offer = driver.post("/rt/drivers/unified-offers-v3").json()["data"]["offers"][0]["offerUUIDs"][0]
    driver.post("/rt/drivers/accept-offers", {"offerUUIDs": [offer]})
    driver.post("/rt/trips/v2/start-waiting", {"uuid": uuid})
    driver.post("/rt/trips/v2/begin", {"uuid": uuid})
    driver.post("/rt/trips/v2/end", {"uuid": uuid})
    notes = [b["description"] for b in driver.post("/rt/earnings/get-trip", {"uuid": uuid}).json()["trip"]["breakdown"]]
    assert "Tarifa" in notes and any(n.startswith("Comissão") for n in notes)
    inbox = driver.post("/rt/inbox/notifications").json()
    assert any(n["title"] == "Viagem concluída" for n in inbox["notifications"]) and inbox["unreadCount"] >= 1
    driver.post("/rt/inbox/mark-read", {})
    assert driver.post("/rt/inbox/notifications").json()["unreadCount"] == 0


def test_inbox_has_the_welcome_notification_from_the_seed(client):
    inbox = login(client, "driver", INES).post("/rt/inbox/notifications").json()
    assert any(n["title"] == "Bem-vindo à Qolari" for n in inbox["notifications"])


def test_route_straight_line_fallback():
    r = routing.route((38.7139, -9.1394), (38.7742, -9.1342))
    assert r["source"] == "straight_line" and 6500 < r["distanceMeters"] < 7000
    assert r["durationSeconds"] > 0 and len(r["polyline"]) == 2


def test_route_endpoint_reads_origin_and_destination(client):
    d = login(client, "driver", CARLOS)
    r = d.post("/rt/navigation/v3/route", {"origin": {"latitude": 38.7139, "longitude": -9.1394},
                                           "destination": {"latitude": 38.7742, "longitude": -9.1342}}).json()
    assert r["distanceMeters"] > 0 and r["polyline"][0]["latitude"] == 38.7139
    assert d.post("/rt/navigation/v3/route", {}).json() == {}


def test_route_falls_back_when_osrm_fails(monkeypatch):
    monkeypatch.setenv("ROUTING_URL", "http://127.0.0.1:1")
    assert routing.route((38.7, -9.1), (38.8, -9.2))["source"] == "straight_line"


def test_old_ledger_notes_are_prettified():
    assert drv._pretty_note("comissao 20%") == "Comissão 20%"
    assert drv._pretty_note("tarifa") == "Tarifa"
    assert drv._pretty_note("frota Frota Tejo, Lda.") == "Frota Frota Tejo, Lda."
    assert drv._pretty_note("Comissão 20%") == "Comissão 20%"
