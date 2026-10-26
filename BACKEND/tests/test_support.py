# -*- coding: utf-8 -*-
"""Suporte: problema de mapa comunicado pelo motorista."""
from tests.conftest import login

CARLOS = "+351920000001"


def test_map_report_is_stored_and_validated(client):
    from core.db import session_scope
    from domain.models import MapReport

    d = login(client, "driver", CARLOS)
    r = d.post("/rt/support/map-report", {
        "reason": "address",
        "note": "A rua indicada nao existe",
        "latitude": 38.7139,
        "longitude": -9.1394,
    })
    assert r.status_code == 200 and r.json()["ok"] is True
    with session_scope() as db:
        row = db.query(MapReport).filter_by(uuid=r.json()["reportUUID"]).first()
        assert row is not None
        assert row.reason == "address" and row.note.startswith("A rua")
        assert abs(row.latitude - 38.7139) < 1e-6 and row.status == "open"
    assert d.post("/rt/support/map-report", {"note": "sem motivo"}).status_code == 400
    assert d.post("/rt/support/map-report", {"reason": "nao-existe"}).status_code == 400


def test_backoffice_lists_and_resolves_map_reports(client, admin):
    d = login(client, "driver", CARLOS)
    created = d.post("/rt/support/map-report", {
        "reason": "outdated",
        "note": "Rua nova",
        "latitude": 38.72,
        "longitude": -9.14,
    }).json()
    listing = client.get("/api/map-reports?status=open&size=200", headers=admin)
    assert listing.status_code == 200
    item = next(x for x in listing.json()["items"] if x["uuid"] == created["reportUUID"])
    assert item["driver"]["phone"] == CARLOS and item["status"] == "open"
    assert item["reason"] == "outdated" and item["reason_label"] == "Mapa desatualizado"
    patched = client.patch(f"/api/map-reports/{item['id']}", headers=admin, json={"status": "resolved"})
    assert patched.status_code == 200 and patched.json()["status"] == "resolved"
    assert client.patch(f"/api/map-reports/{item['id']}", headers=admin,
                        json={"status": "invalido"}).status_code == 422
