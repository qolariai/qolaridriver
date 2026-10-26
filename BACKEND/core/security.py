# -*- coding: utf-8 -*-
"""Palavras-passe (scrypt da stdlib) e tokens assinados (HMAC-SHA256, formato JWT).

Os tokens das apps levam: app, sub (uuid do utilizador), sid (AuthSession) e typ (access|refresh).
O token da consola leva app='console' e sub = id do AdminUser.
"""
import base64, hashlib, hmac, json, os, secrets, time

import config


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.scrypt(password.encode(), salt=salt, n=2 ** 14, r=8, p=1, dklen=32)
    return "scrypt$" + base64.b64encode(salt).decode() + "$" + base64.b64encode(dk).decode()


def verify_password(password: str, stored: str) -> bool:
    try:
        _, salt, dk = stored.split("$")
        got = hashlib.scrypt(password.encode(), salt=base64.b64decode(salt), n=2 ** 14, r=8, p=1, dklen=32)
        return hmac.compare_digest(got, base64.b64decode(dk))
    except (ValueError, TypeError):
        return False


def _b64(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def _unb64(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def sign(claims: dict, ttl_s: int) -> str:
    t = int(time.time())
    head = _b64(b'{"alg":"HS256","typ":"JWT"}')
    body = _b64(json.dumps({**claims, "iat": t, "exp": t + ttl_s}, separators=(",", ":")).encode())
    mac = hmac.new(config.SECRET.encode(), f"{head}.{body}".encode(), hashlib.sha256).digest()
    return f"{head}.{body}.{_b64(mac)}"


def verify(token: str) -> dict | None:
    """-> claims, ou None se o token for invalido/expirado."""
    try:
        head, body, mac = token.split(".")
        want = hmac.new(config.SECRET.encode(), f"{head}.{body}".encode(), hashlib.sha256).digest()
        if not hmac.compare_digest(want, _unb64(mac)):
            return None
        claims = json.loads(_unb64(body))
    except (ValueError, TypeError):
        return None
    if claims.get("exp", 0) < time.time():
        return None
    return claims


def random_code(n: int = 24) -> str:
    return secrets.token_urlsafe(n)
