# -*- coding: utf-8 -*-
"""Endpoints partilhados: canal de mensagens 'ramen', conta do utilizador, consentimentos.

Ramen (network.ramen.internal.model.Response nos modelos do Rider):
    GET /ramen/sessions/{sessionId}/messages -> {"msg": [Message], "ts": ms}
    Message = {type, msg (JSON em string), seq, uuid, session, priority, interpretType}
Long-polling: segura o pedido ate haver mensagens para o utilizador (ou POLL_HOLD_S).
"""
import json

import config
from apps import present
from apps.rtapi import Call, handles
from core import events
from domain import push
from domain.models import now

APPS = ("rider", "driver", "fleet")

# (app, topico do dominio) -> fn(db, payload) -> [(tipo ramen, payload)]: cada app regista aqui a traducao das
# mensagens do dominio para os PushModel que espera (ex.: driver "offer" -> push_driver_unified_offers_v3).
TRANSLATORS: dict = {}


def _messages(call: Call, session_id: str) -> dict:
    subj = call.subject()
    uuid = subj.uuid
    items = push.pending(call.db, uuid)
    if not items:
        call.db.commit()                       # larga o snapshot de leitura antes de esperar
        v = events.version()
        deadline = now() + config.POLL_HOLD_S
        while not items and now() < deadline:
            v = events.wait(v, max(deadline - now(), 0.1))
            items = push.pending(call.db, uuid)
            call.db.commit()
    out = []
    for m in items:
        fn = TRANSLATORS.get((call.app, m["topic"]))
        for kind, payload in (fn(call.db, m["payload"]) if fn else [(m["topic"], m["payload"])]):
            # interpretType "FULL": com x-uber-ramen-diff-mode v1 a Driver (us6.b) trata qualquer outro valor como
            # patch, falha ("missing source element") e descarta a mensagem.
            out.append({"type": kind, "msg": json.dumps(payload, ensure_ascii=False), "seq": m["id"],
                        "uuid": f"{m['id']}-{len(out)}", "session": session_id, "priority": 1,
                        "interpretType": "FULL"})
    return {"ts": now() * 1000, "msg": out}


@handles(APPS, "GET", "/ramen/sessions/{sessionId}/messages")
def ramen_messages(call: Call):
    return _messages(call, call.vars["sessionId"])


@handles(APPS, "GET|POST", "/ramen/events/ack", "/ramen/events/v2/ack", "/ramen/events/v2/recv",
         "/ramen/events/recv")
def ramen_ack(call: Call):
    return {}


# ---- conta -----------------------------------------------------------------------------------
def _user_info(subj) -> dict:
    pp = present.phone_parts(subj.phone)
    return {"userInfo": {
        "name": {"firstname": subj.first_name, "lastname": subj.last_name,
                 "firstName": subj.first_name, "lastName": subj.last_name},
        "email": {"emailAddress": subj.email, "email": subj.email, "isVerified": bool(subj.email)},
        "mobile": {"mobileCountryCode": pp["countryCode"], "mobileNumber": pp["nationalPhoneNumber"],
                   "phoneNumber": subj.phone, "isVerified": True},
        "photo": {}}}


@handles(APPS, "POST", "/rt/users/get-user-info")
def user_info(call: Call):
    return _user_info(call.subject())


@handles(APPS, "POST", "/rt/users/update-user-identity", "/rt/users/update-populous-user-info")
def update_user(call: Call):
    subj = call.subject()
    b = call.body
    name = b.get("name") if isinstance(b.get("name"), dict) else b
    first = name.get("firstName") or name.get("firstname") or b.get("firstName")
    last = name.get("lastName") or name.get("lastname") or b.get("lastName")
    if first:
        subj.first_name = str(first)[:60]
    if last is not None:
        subj.last_name = str(last)[:60]
    email = b.get("email")
    if isinstance(email, dict):
        email = email.get("emailAddress") or email.get("email")
    if email:
        subj.email = str(email)[:120]
    return _user_info(subj)


@handles(APPS, "GET", "/rt/users/get-compliance", "/rt/users/get-compliance-and-copy-for-features")
def compliance(call: Call):
    return {"consents": [], "features": []}


@handles(APPS, "POST", "/rt/users/sync-compliance-and-copy-for-features", "/rt/users/update-compliance",
         "/rt/users/update-compliance-with-task", "/rt/users/need-verification")
def compliance_post(call: Call):
    return {}


@handles(APPS, "POST", "/rt/users/get-security-settings")
def security_settings(call: Call):
    return {"securitySettings": {"twoStepVerificationEnabled": False}}


@handles(APPS, "GET", "/rt/users/contacts")
def contacts(call: Call):
    return {"contacts": []}


@handles(APPS, "POST", "/rt/locations/v1/upload-driver-device-locations")
def upload_locations_any(call: Call):
    """Driver (e Fleet, que tambem tem este endpoint): ultima posicao do lote -> motorista."""
    from apps.driver import apply_locations
    if call.app == "driver":
        apply_locations(call, call.subject())
    return {}


# ---- P6 - lacunas vistas no trafego real do servidor (contrato minimo; ver apps/driver.py) ----------
@handles(APPS, "POST", "/rt/inbox/unread-config")                                # 6; sem separadores nem contadores
def inbox_unread_config(call: Call):
    return {"badgeCount": 0, "dotBadgeCount": 0, "tabsConfig": []}
