# -*- coding: utf-8 -*-
"""Fila de mensagens para as apps (o que o servidor Uber empurra pelo canal 'ramen').

O dominio chama send() em cada mudanca relevante (proposta nova ao motorista, estado da viagem ao
passageiro, motorista online/offline a frota). As apps levam-nas em /ramen/... (apps/realtime.py);
a consola mostra-as na pagina Integracao.
"""
from core.db import touch
from apps import fcm
from domain.models import Device, PushMessage, jget, jset, now


def _notification(topic: str, payload: dict) -> tuple[str, str]:
    if "offer" in topic:
        return "Nova viagem", "Tem uma nova proposta. Abra a app para ver."
    if topic == "trip_status":
        state = payload.get("state") or payload.get("tripStatus") or ""
        return "Atualização da viagem", f"Estado: {state}" if state else "Abra a app para ver o estado."
    if topic == "driver_status":
        status = payload.get("status") or payload.get("availability") or ""
        return "Estado do motorista", f"Estado: {status}" if status else "Abra a app para ver."
    return "Qolari", "Abra a app para ver."


def send(db, app: str, subject_uuid: str | None, topic: str, payload: dict) -> None:
    if not subject_uuid:
        return
    db.add(PushMessage(app=app, subject_uuid=subject_uuid, topic=topic, payload=jset(payload)))
    touch(db, f"push:{subject_uuid}")
    devices = (db.query(Device)
               .filter(Device.app == app, Device.subject_uuid == subject_uuid, Device.push_token != "")
               .all())
    if devices:
        # Um token por app/subject: o mais recente. Tokens de instalações antigas dão 400
        # (UNREGISTERED) e não devem bloquear o push atual.
        latest = max(devices, key=lambda d: d.last_seen_at or 0)
        title, body = _notification(topic, payload)
        for token in {latest.push_token}:
            fcm.queue_push(token, title, body, {"topic": topic})


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
