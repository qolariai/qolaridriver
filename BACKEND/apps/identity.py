# -*- coding: utf-8 -*-
"""Sessoes, tokens (POST /rt/identity/oauth2/token -> TokenResponse) e dispositivos das 3 apps.

O ecra de login e o da propria app: a biblioteca uauth das APKs abre a pagina do dominio auth
(/v2, ver apps/usl.py) e confirma em /rt/silk-screen/submit-form. Codigo de verificacao: config.OTP_CODE.

grant_type aceites no /token: authorization_code (LoginAttempt.auth_code + code_verifier PKCE),
refresh_token, password (username = telefone, password = codigo; usado pelos testes).
"""
import base64, hashlib

import config
from apps.rtapi import Call, RtError, SUBJECT_MODEL, handles
from core.db import touch
from core.security import random_code, sign, verify
from domain import settings
from domain.models import AuthSession, Device, LoginAttempt, Rider, Driver, now

APPS = ("rider", "driver", "fleet")
LOGIN_TTL_S = 600


# ---- sessoes e tokens ------------------------------------------------------------------------
def normalize_phone(raw: str) -> str:
    digits = "".join(ch for ch in (raw or "") if ch.isdigit() or ch == "+")
    if digits.startswith("00"):
        digits = "+" + digits[2:]
    if digits and not digits.startswith("+"):
        digits = "+351" + digits if len(digits) == 9 else "+" + digits
    return digits


def find_subject(db, app: str, phone: str):
    model = SUBJECT_MODEL[app]
    return db.query(model).filter(model.phone == normalize_phone(phone)).first()


def open_session(db, app: str, subject, ip: str = "", ua: str = "") -> dict:
    sess = AuthSession(app=app, subject_uuid=subject.uuid, ip=ip, user_agent=ua[:200])
    db.add(sess)
    db.flush()
    touch(db, "sessions")
    return token_payload(app, subject.uuid, sess.id)


def token_payload(app: str, sub: str, sid: str) -> dict:
    access = sign({"app": app, "sub": sub, "sid": sid, "typ": "access"}, config.ACCESS_TTL_S)
    refresh = sign({"app": app, "sub": sub, "sid": sid, "typ": "refresh"}, 10 * config.ACCESS_TTL_S)
    ttl = config.ACCESS_TTL_S
    # camelCase = TokenResponse do APK (rtapi.services.identity); snake_case = OAuth2 classico
    return {"accessToken": access, "refreshToken": refresh, "tokenType": "Bearer", "expiresIn": ttl,
            "refreshTokenExpiresIn": 10 * ttl, "scope": "everything", "sessionID": sid,
            "idToken": access,
            "access_token": access, "refresh_token": refresh, "token_type": "Bearer", "expires_in": ttl}


def _register(db, app: str, phone: str, first: str, last: str):
    """Conta nova no login (Rider sempre; Driver fica pendente; Fleet nunca)."""
    if app == "rider":
        if not settings.get(db, "rider_signup_open"):
            return None, "Registo de passageiros fechado."
        r = Rider(phone=phone, first_name=first or "Passageiro", last_name=last)
        db.add(r)
        db.flush()
        return r, None
    if app == "driver":
        status = "approved" if settings.get(db, "driver_auto_approve") else "pending"
        d = Driver(phone=phone, first_name=first or "Motorista", last_name=last, status=status)
        db.add(d)
        db.flush()
        touch(db, "drivers")
        return d, None
    return None, "Esta conta Fleet não existe. Peça ao administrador da plataforma para a criar."


def pkce_ok(challenge: str, verifier: str) -> bool:
    """S256: base64url(sha256(verifier)) sem '=' == challenge."""
    digest = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    return digest == challenge


def redeem_login(db, app: str, *, session_id: str = "", auth_code: str = "", verifier: str = ""):
    """Gasta um LoginAttempt (por id de sessao ou authCode) -> (tentativa, utilizador)."""
    q = db.query(LoginAttempt).filter_by(app=app, used=False)
    row = (q.filter_by(id=session_id).first() if session_id else None) or         (q.filter_by(auth_code=auth_code).first() if auth_code else None)
    if not row or now() - row.created_at > LOGIN_TTL_S:
        raise RtError(400, "invalid_grant", "sessao de login invalida ou expirada")
    if row.code_challenge and not pkce_ok(row.code_challenge, verifier):
        raise RtError(400, "invalid_grant", "code_verifier nao corresponde ao codeChallenge")
    row.used = True
    subj = db.query(SUBJECT_MODEL[app]).filter_by(uuid=row.subject_uuid).first()
    if subj is None:
        raise RtError(404, "user_not_found", "conta inexistente")
    return row, subj


# ---- OAuth2 ----------------------------------------------------------------------------------
@handles(APPS, "POST", "/rt/identity/oauth2/token", "/oauth/v2/token", "/oauth/token",
         "/rt/identity/oauth2/sso-exchange-token")
def oauth_token(call: Call):
    db, app = call.db, call.app
    grant = call.get("grant_type", "grantType", default="")
    ua = call.headers.get("user-agent", "")
    if grant in ("authorization_code", "code") or call.get("code"):
        _, subj = redeem_login(db, app, auth_code=str(call.get("code", default="")),
                               verifier=str(call.get("code_verifier", "codeVerifier", default="")))
        return open_session(db, app, subj, call.ip, ua)
    if grant == "refresh_token" or call.get("refresh_token", "refreshToken"):
        claims = verify(str(call.get("refresh_token", "refreshToken", default="")))
        sess = db.get(AuthSession, claims.get("sid", "")) if claims else None
        if not claims or claims.get("typ") != "refresh" or claims.get("app") != app or not sess or sess.revoked:
            raise RtError(401, "invalid_grant", "refresh token invalido")
        sess.last_used_at = now()
        return token_payload(app, claims["sub"], sess.id)
    if grant == "password" or call.get("username", "phone", "phoneNumber"):
        phone = str(call.get("username", "phone", "phoneNumber", default=""))
        if str(call.get("password", "code", default="")) != config.OTP_CODE:
            raise RtError(401, "invalid_grant", "codigo errado")
        subj = find_subject(db, app, phone)
        if not subj:
            raise RtError(404, "user_not_found", "conta inexistente")
        return open_session(db, app, subj, call.ip, ua)
    raise RtError(400, "unsupported_grant_type", f"grant_type '{grant}' nao suportado")


@handles(APPS, "POST", "/rt/identity/oauth2/invalidate-token", "/rt/identity/oauth2/revokesession")
def revoke(call: Call):
    call.subject(required=False)
    if call.session:
        call.session.revoked = True
        touch(call.db, "sessions")
    return {}


@handles(APPS, "POST", "/rt/identity/oauth2/user-id-token")
def user_id_token(call: Call):
    subj = call.subject()
    return {"idToken": sign({"app": call.app, "sub": subj.uuid, "typ": "id"}, 3600)}


@handles(APPS, "POST", "/rt/identity/auth/issue-web-auth-cookies")
def web_cookies(call: Call):
    return {}


# Autenticacao silenciosa por operadora (nao existe aqui): a app cai no login normal
@handles(APPS, "POST", "/rt/silent-authentication/initiate")
def silent_initiate(call: Call):
    return {"requestId": random_code(8), "targetUrl": "", "expiresAtUnixMs": (now() + 60) * 1000}


@handles(APPS, "POST", "/rt/silent-authentication/submit")
def silent_submit(call: Call):
    raise RtError(400, "silent_auth_unavailable", "autenticacao silenciosa indisponivel")


# ---- dispositivos ----------------------------------------------------------------------------
@handles(APPS, "POST", "/rt/devices/upsert", "/rt/devices/upsert-v2")
def device_upsert(call: Call):
    db = call.db
    subj = call.subject(required=False)
    b = call.body
    dev = b.get("deviceData") if isinstance(b.get("deviceData"), dict) else b
    key = str(dev.get("deviceId") or dev.get("deviceUUID") or dev.get("installationId")
              or call.headers.get("x-uber-device-id") or call.headers.get("x-qolari-device-id") or call.ip)
    row = db.query(Device).filter_by(app=call.app, device_key=key).first()
    if not row:
        row = Device(app=call.app, device_key=key)
        db.add(row)
    row.subject_uuid = subj.uuid if subj else row.subject_uuid
    row.model = str(dev.get("deviceModel") or dev.get("model") or call.headers.get("x-uber-device-model")
                    or call.headers.get("x-qolari-device-model") or row.model)[:120]
    row.os_version = str(dev.get("deviceOsVersion") or dev.get("osVersion")
                         or call.headers.get("x-uber-device-os") or row.os_version)[:40]
    row.app_version = str(call.headers.get("x-uber-client-version") or call.headers.get("x-qolari-client-version")
                          or row.app_version)[:40]
    row.push_token = str(dev.get("pushToken") or dev.get("deviceToken") or row.push_token)[:300]
    row.ip, row.last_seen_at = call.ip, now()
    touch(db, "devices")
    return {"isGuestMode": False}


@handles(APPS, "POST", "/rt/devices/task")
def device_task(call: Call):
    # sem instrucoes de atestacao (Play Integrity/SafetyNet): a app segue sem atestar
    return {"timeoutMS": 0}


@handles(APPS, "POST", "/rt/devices/exemption")
def device_exemption(call: Call):
    return {"exemptToken": random_code(16)}


@handles(APPS, "POST", "/rt/communications/device-token/create")
def push_token(call: Call):
    return device_upsert(call)


# ---- P6 - lacunas vistas no trafego real do servidor (contratos minimos; ver apps/driver.py) --------
@handles(APPS, "POST", "/rt/identity/oauth2/get-apps-not-in-device-session-group")   # 18; lista vazia = nenhuma app em falta
def apps_not_in_device_session_group(call: Call):
    return {"appsNotInDeviceSessionGroup": []}


@handles(APPS, "POST", "/rt/identity/oauth2/add-sso-id")                         # 17
def add_sso_id(call: Call):
    return {"accountGroups": [], "wontAdd": []}


@handles(APPS, "POST", "/api/grpc/uberdevices.upsert-user-device/UpsertUserDevice")   # 16; gRPC-web: sumidouro como /rt/devices/upsert
def grpc_upsert_user_device(call: Call):
    return {}
