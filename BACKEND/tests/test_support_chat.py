# -*- coding: utf-8 -*-
"""Chat de apoio in-app."""
import base64

from tests.conftest import login

PNG = base64.b64encode(b"\x89PNG\r\n\x1a\n" + b"0" * 64).decode()


def test_driver_support_chat_roundtrip(client):
    d = login(client, "driver", "+351920000001")
    r = d.post("/rt/support/threads", {"category": "viagem", "message": "Preciso de ajuda"})
    assert r.status_code == 200
    uuid = r.json()["thread"]["uuid"]
    assert d.get("/rt/support/threads").json()["threads"]
    detail = d.get(f"/rt/support/threads/{uuid}").json()
    assert detail["messages"][0]["body"] == "Preciso de ajuda"
    assert d.post(f"/rt/support/threads/{uuid}/messages", {"message": "Mais detalhes"}).status_code == 200
    assert d.post(f"/rt/support/threads/{uuid}/read").status_code == 200


def test_support_attachment_and_console_download(client, admin):
    d = login(client, "driver", "+351920000003")
    r = d.post("/rt/support/threads", {
        "category": "bug", "message": "Ecrã partido",
        "fileName": "bug.png", "contentBase64": PNG,
    })
    assert r.status_code == 200, r.text
    uuid = r.json()["thread"]["uuid"]

    detail = d.get(f"/rt/support/threads/{uuid}").json()
    assert detail["messages"][0]["hasFile"] is True
    name = detail["messages"][0]["fileName"]
    assert name.startswith("support-")

    convo = client.get(f"/api/support/{uuid}", headers=admin).json()
    assert convo["messages"][0]["hasFile"] is True

    f = client.get(f"/api/support/attachment/{name}", headers=admin)
    assert f.status_code == 200 and f.content.startswith(b"\x89PNG")


def test_screen_share_roundtrip(client, admin):
    d = login(client, "rider", "+351910000001")
    thread = d.post("/rt/support/threads", {"category": "bug", "message": "Partilha de ecrã"})
    uuid = thread.json()["thread"]["uuid"]

    start = d.post(f"/rt/support/threads/{uuid}/screen-share/start")
    assert start.status_code == 200, start.text
    share = start.json()["share"]["uuid"]

    frame = d.post(f"/rt/support/threads/{uuid}/screen-share/{share}/frame",
                   {"contentBase64": base64.b64encode(b"fake-jpeg").decode()})
    assert frame.status_code == 200, frame.text

    meta = client.get(f"/api/support/{uuid}/screen-share", headers=admin).json()
    assert meta["active"] is True and meta["has_frame"] is True and meta["uuid"] == share

    img = client.get(f"/api/support/screen-share/{share}/frame", headers=admin)
    assert img.status_code == 200 and img.content == b"fake-jpeg"

    stop = d.post(f"/rt/support/threads/{uuid}/screen-share/{share}/stop")
    assert stop.json()["share"]["active"] is False

