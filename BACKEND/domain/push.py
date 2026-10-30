# -*- coding: utf-8 -*-
"""Fila de mensagens para as apps (o que o servidor Uber empurra pelo canal 'ramen').

O dominio chama send() em cada mudanca relevante (proposta nova ao motorista, estado da viagem ao
passageiro, motorista online/offline a frota). As apps levam-nas em /ramen/... (apps/realtime.py);
a consola mostra-as na pagina Integracao.
"""
from core.db import touch
from domain.models import PushMessage, jget, jset, now


def send(db, app: str, subject_uuid: str | None, topic: str, payload: dict) -> None:
    if not subject_uuid:
        return
    db.add(PushMessage(app=app, subject_uuid=subject_uuid, topic=topic, payload=jset(payload)))
    touch(db, f"push:{subject_uuid}")


def pending(db, subject_uuid: str, mark: bool = True, limit: int = 50) -> list[dict]:
    rows = (db.query(PushMessage)
            .filter(PushMessage.subject_uuid == subject_uuid, PushMessage.delivered_at.is_(None))
            .order_by(PushMessage.id).limit(limit).all())
    out = [{"id": r.id, "topic": r.topic, "payload": jget(r.payload, {}), "created_at": r.created_at}
           for r in rows]
    if mark:
        t = now()
        for r in rows:
            r.delivered_at = t
    return out
