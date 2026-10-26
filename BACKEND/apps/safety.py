# -*- coding: utf-8 -*-
"""Seguranca: contactos de confianca, SOS e partilha de viagem."""
import base64
import binascii
import secrets

import config
from apps.rtapi import Call, RtError, handles
from domain.models import SafetyIncident, Trip, TripRecording, TripShare, TrustedContact, now

APP = ("rider", "driver", "fleet")
MAX_CONTACTS = 10
SHARE_TTL_S = 4 * 3600


def _subject(call: Call):
    s = call.subject()
    name = getattr(s, "name", "") or (
        f"{getattr(s, 'first_name', '')} {getattr(s, 'last_name', '')}".strip()
    )
    return s, (name or "Utilizador"), getattr(s, "phone", "") or ""


def _contact_json(c: TrustedContact) -> dict:
    return {"uuid": c.uuid, "name": c.name, "phone": c.phone, "createdAt": c.created_at}


def _incident_json(i: SafetyIncident) -> dict:
    return {
        "uuid": i.uuid,
        "kind": i.kind,
        "app": i.app,
        "subjectName": i.subject_name,
        "subjectPhone": i.subject_phone,
        "tripUuid": i.trip_uuid,
        "latitude": i.latitude,
        "longitude": i.longitude,
        "note": i.note,
        "status": i.status,
        "createdAt": i.created_at,
        "closedAt": i.closed_at,
    }


def _trip(call: Call, uuid: str) -> Trip:
    t = call.db.query(Trip).filter_by(uuid=str(uuid)).first()
    if not t:
        raise RtError(404, "trip_not_found", "viagem inexistente")
    s, _, _ = _subject(call)
    if call.app == "rider" and t.rider_id != s.id:
        raise RtError(403, "forbidden", "viagem de outra conta")
    if call.app == "driver" and t.driver_id != s.id:
        raise RtError(403, "forbidden", "viagem de outro motorista")
    return t


@handles(APP, "GET", "/rt/safety/contacts")
def list_contacts(call: Call):
    s, _, _ = _subject(call)
    rows = (
        call.db.query(TrustedContact)
        .filter_by(app=call.app, subject_uuid=s.uuid)
        .order_by(TrustedContact.id)
        .all()
    )
    return {"contacts": [_contact_json(c) for c in rows], "limit": MAX_CONTACTS}


@handles(APP, "POST", "/rt/safety/contacts")
def add_contact(call: Call):
    s, _, _ = _subject(call)
    name = str(call.body.get("name") or "").strip()[:120]
    phone = str(call.body.get("phone") or "").strip()[:30]
    if not name or len(phone) < 6:
        raise RtError(400, "invalid_contact", "indique nome e telefone")
    existing = (
        call.db.query(TrustedContact)
        .filter_by(app=call.app, subject_uuid=s.uuid)
        .count()
    )
    if existing >= MAX_CONTACTS:
        raise RtError(409, "contact_limit", f"maximo de {MAX_CONTACTS} contactos")
    dup = (
        call.db.query(TrustedContact)
        .filter_by(app=call.app, subject_uuid=s.uuid, phone=phone)
        .first()
    )
    if dup:
        raise RtError(409, "duplicate_contact", "contacto ja existe")
    c = TrustedContact(app=call.app, subject_uuid=s.uuid, name=name, phone=phone)
    call.db.add(c)
    call.db.flush()
    return {"contact": _contact_json(c)}


@handles(APP, "DELETE", "/rt/safety/contacts/{uuid}")
def delete_contact(call: Call):
    s, _, _ = _subject(call)
    c = (
        call.db.query(TrustedContact)
        .filter_by(uuid=call.vars["uuid"], app=call.app, subject_uuid=s.uuid)
        .first()
    )
    if not c:
        raise RtError(404, "contact_not_found", "contacto inexistente")
    call.db.delete(c)
    return {"ok": True}


@handles(APP, "POST", "/rt/safety/sos")
def sos(call: Call):
    s, name, phone = _subject(call)
    trip_uuid = str(call.body.get("tripUuid") or call.body.get("trip_uuid") or "")
    if trip_uuid:
        _trip(call, trip_uuid)
    i = SafetyIncident(
        app=call.app,
        subject_uuid=s.uuid,
        subject_name=name,
        subject_phone=phone,
        kind="sos",
        trip_uuid=trip_uuid,
        latitude=call.body.get("latitude"),
        longitude=call.body.get("longitude"),
        note=str(call.body.get("note") or "")[:500],
    )
    call.db.add(i)
    call.db.flush()
    rows = (
        call.db.query(TrustedContact)
        .filter_by(app=call.app, subject_uuid=s.uuid)
        .order_by(TrustedContact.id)
        .all()
    )
    return {
        "incident": _incident_json(i),
        "contacts": [_contact_json(c) for c in rows],
        "message": "Alerta registado. A operacao foi notificada.",
    }


@handles(APP, "POST", "/rt/safety/share")
def share_trip(call: Call):
    s, _, _ = _subject(call)
    trip_uuid = str(call.body.get("tripUuid") or call.body.get("trip_uuid") or "")
    if not trip_uuid:
        raise RtError(400, "missing_trip", "indique a viagem")
    _trip(call, trip_uuid)
    token = secrets.token_urlsafe(18)
    share = TripShare(
        token=token,
        trip_uuid=trip_uuid,
        app=call.app,
        subject_uuid=s.uuid,
        expires_at=now() + SHARE_TTL_S,
    )
    call.db.add(share)
    call.db.flush()
    base = config.PUBLIC_BASE_URL or f"http://{config.PUBLIC_HOST}:{config.CONSOLE_PORT}"
    return {
        "token": token,
        "path": f"/share/{token}",
        "url": f"{base}/share/{token}",
        "expiresAt": share.expires_at,
    }


@handles(APP, "POST", "/rt/safety/ride-check")
def ride_check(call: Call):
    """Check-in durante a viagem: 'ok' ou 'help'."""
    s, name, phone = _subject(call)
    trip_uuid = str(call.body.get("tripUuid") or call.body.get("trip_uuid") or "")
    if not trip_uuid:
        raise RtError(400, "missing_trip", "indique a viagem")
    _trip(call, trip_uuid)
    state = str(call.body.get("status") or "ok").strip().lower()
    if state not in ("ok", "help"):
        raise RtError(400, "invalid_status", "estado invalido")
    i = SafetyIncident(
        app=call.app,
        subject_uuid=s.uuid,
        subject_name=name,
        subject_phone=phone,
        kind="ride_check",
        trip_uuid=trip_uuid,
        latitude=call.body.get("latitude"),
        longitude=call.body.get("longitude"),
        note=state,
        status="open" if state == "help" else "closed",
        closed_at=None if state == "help" else now(),
    )
    call.db.add(i)
    call.db.flush()
    return {"status": state, "incident": _incident_json(i)}


def _recording_json(r: TripRecording) -> dict:
    return {"uuid": r.uuid, "tripUuid": r.trip_uuid, "kind": r.kind,
            "startedAt": r.started_at, "endedAt": r.ended_at,
            "durationS": r.duration_s, "hasFile": bool(r.file_name)}


@handles(APP, "POST", "/rt/safety/recording/start")
def recording_start(call: Call):
    s, _, _ = _subject(call)
    trip_uuid = str(call.body.get("tripUuid") or call.body.get("trip_uuid") or "")
    if not trip_uuid:
        raise RtError(400, "missing_trip", "indique a viagem")
    _trip(call, trip_uuid)
    kind = str(call.body.get("kind") or "audio").lower()
    if kind not in ("audio", "video"):
        raise RtError(400, "invalid_kind", "tipo invalido")
    r = TripRecording(trip_uuid=trip_uuid, app=call.app, subject_uuid=s.uuid, kind=kind)
    call.db.add(r)
    call.db.flush()
    return {"recording": _recording_json(r)}


@handles(APP, "POST", "/rt/safety/recording/{uuid}/stop")
def recording_stop(call: Call):
    s, _, _ = _subject(call)
    r = (call.db.query(TripRecording)
         .filter_by(uuid=call.vars["uuid"], app=call.app, subject_uuid=s.uuid).first())
    if not r:
        raise RtError(404, "recording_not_found", "gravacao inexistente")
    raw_b64 = str(call.body.get("contentBase64") or "").strip()
    if raw_b64:
        if "," in raw_b64 and raw_b64.split(",", 1)[0].startswith("data:"):
            raw_b64 = raw_b64.split(",", 1)[1]
        try:
            raw = base64.b64decode(raw_b64, validate=True)
        except (binascii.Error, ValueError):
            raise RtError(400, "invalid_file", "gravacao invalida")
        if len(raw) > 20 * 1024 * 1024:
            raise RtError(413, "file_too_large", "maximo de 20 MB")
        config.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        ext = ".m4a" if r.kind == "audio" else ".mp4"
        name = f"rec-{r.uuid}{ext}"
        (config.UPLOAD_DIR / name).write_bytes(raw)
        r.file_name = name
    r.ended_at = now()
    r.duration_s = max(0, r.ended_at - r.started_at)
    return {"recording": _recording_json(r)}


@handles(APP, "GET", "/rt/safety/incidents")
def my_incidents(call: Call):
    s, _, _ = _subject(call)
    rows = (
        call.db.query(SafetyIncident)
        .filter_by(app=call.app, subject_uuid=s.uuid)
        .order_by(SafetyIncident.id.desc())
        .limit(20)
        .all()
    )
    return {"incidents": [_incident_json(i) for i in rows]}
