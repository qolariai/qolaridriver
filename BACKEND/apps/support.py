# -*- coding: utf-8 -*-
"""Apoio in-app: conversas entre a conta (Driver/Rider/Fleet) e a operacao."""
import base64
import binascii
from pathlib import Path

import config
from apps.rtapi import Call, RtError, handles
from domain.models import ScreenShare, SupportMessage, SupportThread, now

APP = ("rider", "driver", "fleet")
CATEGORIES = {"viagem", "conta", "pagamento", "seguranca", "bug", "outro"}
ATTACH_EXT = {".jpg", ".jpeg", ".png", ".webp", ".pdf"}


def _subject(call: Call):
    s = call.subject()
    name = getattr(s, "name", "") or (
        f"{getattr(s, 'first_name', '')} {getattr(s, 'last_name', '')}".strip()
    )
    return s, (name or "Utilizador"), getattr(s, "phone", "") or ""


def _thread_json(db, t: SupportThread) -> dict:
    rows = db.query(SupportMessage).filter(SupportMessage.thread_id == t.id).all()
    last = rows[-1] if rows else None
    unread = sum(1 for m in rows if m.sender == "support" and not m.read_by_user)
    return {
        "uuid": t.uuid,
        "category": t.category,
        "status": t.status,
        "createdAt": t.created_at,
        "updatedAt": t.updated_at,
        "lastMessage": last.body if last else "",
        "unread": unread,
    }


def _message_json(m: SupportMessage) -> dict:
    return {"id": m.id, "sender": m.sender, "body": m.body, "createdAt": m.created_at,
            "fileName": m.file_name or "", "hasFile": bool(m.file_name)}


def _attachment(call: Call, owner: str) -> str | None:
    """Guarda um anexo base64 e devolve o nome do ficheiro (ou None)."""
    raw_b64 = str(call.body.get("contentBase64") or call.body.get("content") or "").strip()
    if not raw_b64:
        return None
    if "," in raw_b64 and raw_b64.split(",", 1)[0].startswith("data:"):
        raw_b64 = raw_b64.split(",", 1)[1]
    try:
        raw = base64.b64decode(raw_b64, validate=True)
    except (binascii.Error, ValueError):
        raise RtError(400, "invalid_file", "anexo invalido")
    if not raw:
        raise RtError(400, "empty_file", "anexo vazio")
    if len(raw) > config.UPLOAD_MAX_BYTES:
        raise RtError(413, "file_too_large", "maximo de 8 MB")
    original = str(call.body.get("fileName") or "anexo")
    suffix = Path(original).suffix.lower()
    if suffix == ".jpeg":
        suffix = ".jpg"
    if suffix not in ATTACH_EXT:
        if raw.startswith(b"\xff\xd8\xff"):
            suffix = ".jpg"
        elif raw.startswith(b"\x89PNG"):
            suffix = ".png"
        elif raw.startswith(b"%PDF"):
            suffix = ".pdf"
        else:
            raise RtError(415, "unsupported_file", "so JPG, PNG, WEBP ou PDF")
    config.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    name = f"support-{owner}{suffix}"
    (config.UPLOAD_DIR / name).write_bytes(raw)
    return name


def _own(call: Call, uuid: str) -> SupportThread:
    s, _, _ = _subject(call)
    t = (
        call.db.query(SupportThread)
        .filter_by(uuid=str(uuid), app=call.app, subject_uuid=s.uuid)
        .first()
    )
    if not t:
        raise RtError(404, "thread_not_found", "conversa inexistente")
    return t


@handles(APP, "POST", "/rt/support/threads")
def create_thread(call: Call):
    s, name, phone = _subject(call)
    category = str(call.body.get("category") or "outro").strip().lower()
    body = str(call.body.get("message") or "").strip()[:1000]
    if category not in CATEGORIES:
        category = "outro"
    if not body and not call.body.get("contentBase64"):
        raise RtError(400, "missing_message", "escreva uma mensagem")
    t = SupportThread(
        app=call.app, subject_uuid=s.uuid, subject_name=name,
        subject_phone=phone, category=category,
    )
    call.db.add(t)
    call.db.flush()
    file_name = _attachment(call, t.uuid)
    call.db.add(SupportMessage(thread_id=t.id, sender="user", body=body or "Anexo", file_name=file_name))
    t.updated_at = now()
    call.db.flush()
    return {"thread": _thread_json(call.db, t)}


@handles(APP, "GET|POST", "/rt/support/threads")
def list_threads(call: Call):
    s, _, _ = _subject(call)
    rows = (
        call.db.query(SupportThread)
        .filter_by(app=call.app, subject_uuid=s.uuid)
        .order_by(SupportThread.updated_at.desc())
        .limit(50)
        .all()
    )
    return {"threads": [_thread_json(call.db, t) for t in rows]}


@handles(APP, "GET", "/rt/support/threads/{uuid}")
def get_thread(call: Call):
    t = _own(call, call.vars["uuid"])
    rows = (
        call.db.query(SupportMessage)
        .filter_by(thread_id=t.id)
        .order_by(SupportMessage.id)
        .all()
    )
    for m in rows:
        if m.sender == "support":
            m.read_by_user = True
    return {"thread": _thread_json(call.db, t), "messages": [_message_json(m) for m in rows]}


@handles(APP, "POST", "/rt/support/threads/{uuid}/messages")
def add_message(call: Call):
    t = _own(call, call.vars["uuid"])
    body = str(call.body.get("message") or "").strip()[:1000]
    if not body and not call.body.get("contentBase64"):
        raise RtError(400, "missing_message", "escreva uma mensagem")
    file_name = _attachment(call, f"{t.uuid}-{now()}")
    m = SupportMessage(thread_id=t.id, sender="user", body=body or "Anexo", file_name=file_name)
    call.db.add(m)
    t.status, t.updated_at = "open", now()
    call.db.flush()
    return {"message": _message_json(m)}


@handles(APP, "POST", "/rt/support/threads/{uuid}/read")
def read_thread(call: Call):
    t = _own(call, call.vars["uuid"])
    for m in call.db.query(SupportMessage).filter_by(thread_id=t.id, sender="support").all():
        m.read_by_user = True
    return {"ok": True}


def _share_json(s: ScreenShare) -> dict:
    return {"uuid": s.uuid, "active": bool(s.active), "frameAt": s.frame_at,
            "hasFrame": bool(s.file_name), "createdAt": s.created_at}


@handles(APP, "POST", "/rt/support/threads/{uuid}/screen-share/start")
def screen_share_start(call: Call):
    t = _own(call, call.vars["uuid"])
    s = (call.db.query(ScreenShare)
         .filter_by(thread_id=t.id, active=True)
         .order_by(ScreenShare.id.desc()).first())
    if not s:
        s = ScreenShare(thread_id=t.id, app=call.app, subject_uuid=t.subject_uuid)
        call.db.add(s)
        call.db.flush()
    return {"share": _share_json(s)}


@handles(APP, "POST", "/rt/support/threads/{uuid}/screen-share/{shareUuid}/frame")
def screen_share_frame(call: Call):
    t = _own(call, call.vars["uuid"])
    s = (call.db.query(ScreenShare)
         .filter_by(uuid=call.vars["shareUuid"], thread_id=t.id).first())
    if not s:
        raise RtError(404, "share_not_found", "partilha inexistente")
    raw_b64 = str(call.body.get("contentBase64") or "").strip()
    if "," in raw_b64 and raw_b64.split(",", 1)[0].startswith("data:"):
        raw_b64 = raw_b64.split(",", 1)[1]
    try:
        raw = base64.b64decode(raw_b64, validate=True)
    except (binascii.Error, ValueError):
        raise RtError(400, "invalid_frame", "frame invalido")
    if not raw:
        raise RtError(400, "empty_frame", "frame vazio")
    if len(raw) > 2 * 1024 * 1024:
        raise RtError(413, "frame_too_large", "frame demasiado grande")
    config.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    name = f"screen-{s.uuid}.jpg"
    (config.UPLOAD_DIR / name).write_bytes(raw)
    s.file_name, s.frame_at, s.active = name, now(), True
    return {"ok": True, "at": s.frame_at}


@handles(APP, "POST", "/rt/support/threads/{uuid}/screen-share/{shareUuid}/stop")
def screen_share_stop(call: Call):
    t = _own(call, call.vars["uuid"])
    s = (call.db.query(ScreenShare)
         .filter_by(uuid=call.vars["shareUuid"], thread_id=t.id).first())
    if not s:
        raise RtError(404, "share_not_found", "partilha inexistente")
    s.active = False
    return {"share": _share_json(s)}
