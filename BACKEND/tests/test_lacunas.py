# -*- coding: utf-8 -*-
"""P6: lacunas do backend vistas no trafego real do servidor (ANDOIRD/DRIVER/endpoints.json -> lacunas_backend).

Cada resposta e o minimo valido do contrato: campos obrigatorios (*) de tools/model_tree.py driver <classe>.
Nao valida o conteudo no telemovel: so que a rota existe, devolve 200 e a forma certa.
"""
import json
from pathlib import Path

import pytest

from apps import rtapi
from tests.conftest import login

CARLOS = "+351920000001"   # aprovado, Frota Tejo
INES = "+351920000006"     # por aprovar

# (verbo, path, chaves obrigatorias da resposta, valor esperado em campos escolhidos)
CASES = [
    ("POST", "/rt/offer-experience/upload-earner-experience-state", [], {}),                          # 441
    ("POST", "/rt/glide/get-earner-dashboard-sections-content", ["requestID", "sectionsContent"], {"sectionsContent": {}}),  # 20
    ("POST", "/rt/drivers/get-checklist-sdui", [], {}),                                                 # 19
    ("POST", "/rt/identity/oauth2/get-apps-not-in-device-session-group", ["appsNotInDeviceSessionGroup"], {"appsNotInDeviceSessionGroup": []}),  # 18
    ("POST", "/rt/identity/oauth2/add-sso-id", ["accountGroups", "wontAdd"], {"wontAdd": []}),         # 17
    ("POST", "/api/grpc/uberdevices.upsert-user-device/UpsertUserDevice", [], {}),                      # 16
    ("POST", "/rt/transparent-fare-breakdown/get-transparent-fare-breakdown", ["transparentFareBreakdown"], {}),  # 15
    ("POST", "/rt/navigation/v3/route", [], {}),                                                        # 10
    ("POST", "/rt/v1/driverretention/mentorship/getmentorshipstate", ["role"], {"role": "NONE"}),       # 10
    ("POST", "/rt/inbox/unread-config", ["badgeCount", "dotBadgeCount", "tabsConfig"], {"tabsConfig": []}),  # 6
    ("GET", "/rt/drivers/abc-123/v2/preferences", ["feedback", "preferences"], {"preferences": []}),  # 5
    ("GET", "/rt/health", [], {"status": "ok"}),                                                        # 5
    ("POST", "/rt/drivers/learning/fetch-mobile-alerts", ["mobileAlerts"], {"mobileAlerts": []}),       # 3
    ("POST", "/rt/earnings/session-feedback-loop/validate-session-readiness", ["sessionExpected"], {"sessionExpected": False}),  # 3
    ("POST", "/rt/mobile/recovery-action", [], {}),                                                     # 2
]


@pytest.fixture(scope="module")
def carlos(client):
    return login(client, "driver", CARLOS)


@pytest.mark.parametrize("method,path,keys,expected", CASES, ids=[c[1].rsplit("/", 1)[-1] for c in CASES])
def test_gap_handler_minimal_contract(carlos, method, path, keys, expected):
    route = rtapi.find_route("driver", method, path)
    assert route is not None, f"sem rota para {method} {path}"
    r = carlos.post(path) if method == "POST" else carlos.get(path)
    assert r.status_code == 200, r.text
    body = r.json()
    for k in keys:
        assert k in body, f"campo obrigatorio {k} em falta em {path}: {body}"
    for k, v in expected.items():
        assert body[k] == v
    assert rtapi.TRAFFIC["driver"][-1]["handler"], "o pedido ficou sem handler no registo"


def test_fare_breakdown_union_type_is_field_name(carlos):
    """Uniao Thrift: `type` e o nome do campo (decode: TransparentFareBreakdownUnionType data|notApplicable|notAvailable)."""
    b = carlos.post("/rt/transparent-fare-breakdown/get-transparent-fare-breakdown").json()["transparentFareBreakdown"]
    assert b["type"] == "notApplicable" and "notApplicable" in b


def test_preferences_feedback_has_required_fields(carlos):
    fb = carlos.get("/rt/drivers/abc/v2/preferences").json()["feedback"]
    assert {"effect", "effectText", "jobEligibilityRate", "title"} <= set(fb)
    assert fb["effect"] == "NEUTRAL"    # enum sem @SerializedName: nome Java


def test_set_default_vehicle_and_unknown_vehicle(carlos):
    vehicles = carlos.get("/rt/drivers/v2/vehicles").json()["vehicles"]
    assert vehicles, "o seed devia dar veiculos ao Carlos"
    target = vehicles[-1]["uuid"]
    r = carlos.post("/rt/vehicle/presentation/driver/vehiclesblocker/set-default-vehicle", {"vehicleUUID": target})
    assert r.status_code == 200, r.text
    after = carlos.get("/rt/drivers/v2/vehicles").json()["vehicles"]
    assert {v["uuid"]: v["isDefault"] for v in after}[target] is True
    assert sum(1 for v in after if v["isDefault"]) == 1
    bad = carlos.post("/rt/vehicle/presentation/driver/vehiclesblocker/set-default-vehicle", {"vehicleUUID": "nao-existe"})
    assert bad.status_code == 404 and bad.json()["code"] == "rtapi.not_found"
    # sem uuid: nao altera nada
    assert carlos.post("/rt/vehicle/presentation/driver/vehiclesblocker/set-default-vehicle", {}).status_code == 200
    assert {v["uuid"]: v["isDefault"] for v in carlos.get("/rt/drivers/v2/vehicles").json()["vehicles"]}[target] is True


def test_onboarding_status_follows_driver_status(client, carlos):
    assert carlos.get("/rt/onboarding/get-onboarding-status").json() == {"driverOnboardingStatus": "ONBOARDED"}
    ines = login(client, "driver", INES)
    assert ines.get("/rt/onboarding/get-onboarding-status").json() == {"driverOnboardingStatus": "ONBOARDING"}


def test_every_gap_in_endpoints_json_has_a_route():
    """Regressao spec <-> backend: o que a app chama em trafego real e o contrato marca como lacuna tem de ter handler."""
    f = Path(__file__).resolve().parents[2] / "ANDOIRD" / "DRIVER" / "endpoints.json"
    if not f.exists():
        pytest.skip("endpoints.json nao esta presente")
    gaps = json.loads(f.read_text(encoding="utf-8")).get("lacunas_backend", [])
    missing = []
    for g in gaps:
        verbs = ["GET", "POST"] if g["http"] in ("?", "gRPC") else [g["http"]]
        path = g["path"].replace("{driverUUID}", "x").replace("{id}", "x")
        if not any(rtapi.find_route("driver", v, path) for v in verbs):
            missing.append((g["http"], g["path"]))
    assert not missing, f"lacunas ainda sem rota: {missing}"
