# -*- coding: utf-8 -*-
"""Documentos do motorista: upload e verificacao de identidade."""
import base64

from tests.conftest import login

PNG = base64.b64encode(b"\x89PNG\r\n\x1a\n" + b"0" * 64).decode()
PDF = base64.b64encode(b"%PDF-1.4 teste").decode()


def test_document_upload_and_identity(client, admin):
    d = login(client, "driver", "+351920000002")

    r = d.post("/rt/drivers/v2/documents/upload", {
        "kind": "carta_conducao",
        "number": "L-123456",
        "expiresOn": "2030-01-01",
        "fileName": "carta.png",
        "contentBase64": PNG,
    })
    assert r.status_code == 200, r.text
    doc = r.json()["document"]
    assert doc["status"] == "pending" and doc["hasFile"] is True
    assert doc["expiresOn"] == "2030-01-01"

    docs = d.post("/rt/drivers/v2/documents", {}).json()["driverDocuments"]
    assert any(x["kind"] == "carta_conducao" and x["hasFile"] for x in docs)

    v = d.post("/rt/drivers/v2/verify-identity", {
        "documentNumber": "12345678",
        "expiresOn": "2031-05-05",
        "fileName": "cc.pdf",
        "contentBase64": PDF,
    })
    assert v.status_code == 200, v.text
    assert v.json()["status"] == "pending"

    bad = d.post("/rt/drivers/v2/documents/upload", {
        "kind": "carta_conducao", "fileName": "x.txt", "contentBase64": base64.b64encode(b"hello").decode(),
    })
    assert bad.status_code == 415

    items = client.get("/api/documents?status=pending", headers=admin).json()["items"]
    assert any(x["kind"] == "cartao_cidadao" and x["has_file"] for x in items)
