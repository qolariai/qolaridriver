# -*- coding: utf-8 -*-
"""Gravacao de audio associada a viagem."""
import base64

from core.db import session_scope
from domain.models import Trip
from tests.conftest import login


def test_audio_recording_start_stop(client):
    with session_scope() as db:
        t = (db.query(Trip).filter(Trip.state == "completed", Trip.driver_id.isnot(None))
             .order_by(Trip.id.desc()).first())
        assert t is not None
        uuid, phone = t.uuid, t.driver.phone

    d = login(client, "driver", phone)
    start = d.post("/rt/safety/recording/start", {"tripUuid": uuid, "kind": "audio"})
    assert start.status_code == 200, start.text
    rec = start.json()["recording"]["uuid"]

    stop = d.post(f"/rt/safety/recording/{rec}/stop",
                  {"contentBase64": base64.b64encode(b"fake-audio").decode()})
    assert stop.status_code == 200, stop.text
    assert stop.json()["recording"]["hasFile"] is True
    assert stop.json()["recording"]["durationS"] >= 0


def test_video_recording_start_stop(client):
    with session_scope() as db:
        t = (db.query(Trip).filter(Trip.state == "completed", Trip.driver_id.isnot(None))
             .order_by(Trip.id.desc()).first())
        uuid, phone = t.uuid, t.driver.phone

    d = login(client, "driver", phone)
    start = d.post("/rt/safety/recording/start", {"tripUuid": uuid, "kind": "video"})
    assert start.status_code == 200, start.text
    rec = start.json()["recording"]["uuid"]

    stop = d.post(f"/rt/safety/recording/{rec}/stop",
                  {"contentBase64": base64.b64encode(b"\x00\x00\x00\x18ftypmp42").decode()})
    assert stop.status_code == 200, stop.text
    assert stop.json()["recording"]["kind"] == "video"
    assert stop.json()["recording"]["hasFile"] is True
