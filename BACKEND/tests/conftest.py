# -*- coding: utf-8 -*-
"""BD temporaria por sessao de testes; relogio desligado; a porta 'testserver' (80) nao e da Driver."""
import os, sys, tempfile
from pathlib import Path

import pytest

_tmp = tempfile.mkdtemp(prefix="qolari-test-")
os.environ["DB_URL"] = f"sqlite:///{Path(_tmp, 'test.db').as_posix()}"
os.environ["LOG_DIR"] = str(Path(_tmp, "logs"))
os.environ["DATA_DIR"] = _tmp
os.environ["RUN_TICKER"] = "0"
os.environ["DRIVER_PORT"] = "18080"     # TestClient usa a porta 80 no scope
os.environ["EXTRA_APP_PORTS"] = ""      # idem (por omissao a 80 e a Driver iOS)
os.environ["POLL_HOLD_S"] = "0.2"
os.environ["GOOGLE_MAPS_KEY"] = ""          # geocodificacao inversa sem rede (apps/geocode.py)
# Indice OSM local desligado por omissao nos testes: o DATA_DIR e temporario e nao tem base.
# Os testes do indice (test_osmgeo.py) apontam OSM_DB para um ficheiro sintetico.
os.environ["OSM_DB"] = str(Path(_tmp, "sem_osm.sqlite"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient  # noqa: E402

import main  # noqa: E402


@pytest.fixture(scope="session")
def client():
    with TestClient(main.app) as c:
        yield c


@pytest.fixture(scope="session")
def admin(client):
    r = client.post("/api/auth/login", json={"email": "admin@qolari.local", "password": "admin"})
    assert r.status_code == 200, r.text
    return {"Authorization": "Bearer " + r.json()["token"]}


class AppClient:
    """Fala com uma app como o telemovel (header X-Qolari-App + token x-uber-token)."""
    def __init__(self, client, app, token=None):
        self.c, self.app, self.token = client, app, token

    def headers(self):
        h = {"X-Qolari-App": self.app}
        if self.token:
            h["x-qolari-token" if self.app == "fleet" else "x-uber-token"] = self.token
        return h

    def post(self, path, body=None, **kw):
        return self.c.post(path, json=body or {}, headers=self.headers(), **kw)

    def get(self, path, **kw):
        return self.c.get(path, headers=self.headers(), **kw)

    def patch(self, path, body=None, **kw):
        return self.c.patch(path, json=body or {}, headers=self.headers(), **kw)


def login(client, app: str, phone: str) -> AppClient:
    """Tokens por grant_type=password (telefone + codigo), enquanto o login nativo da app nao esta mapeado."""
    r = client.post("/rt/identity/oauth2/token", headers={"X-Qolari-App": app},
                    json={"grant_type": "password", "username": phone, "password": "0000"})
    assert r.status_code == 200, r.text
    tok = r.json()
    assert tok["accessToken"] == tok["access_token"] and tok["tokenType"] == "Bearer"
    return AppClient(client, app, tok["accessToken"])
