# -*- coding: utf-8 -*-
"""Login da consola (AdminUser) e permissoes por papel.

    admin     tudo (incluindo definicoes e administradores)
    operator  operacao: viagens, motoristas, passageiros, frotas, veiculos, documentos, simulador
    finance   leitura de tudo + financas (pagamentos, acertos)
"""
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

import config
from core.db import session_scope
from core.security import sign, verify
from domain.models import AdminUser, AuditLog

ROLES = ("admin", "operator", "finance")
_bearer = HTTPBearer(auto_error=False)


def issue(user: AdminUser) -> str:
    return sign({"app": "console", "sub": str(user.id), "role": user.role}, config.CONSOLE_TTL_S)


def user_json(u: AdminUser) -> dict:
    return {"id": u.id, "email": u.email, "name": u.name, "role": u.role, "active": u.active,
            "created_at": u.created_at, "last_login_at": u.last_login_at}


def current(cred: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> dict:
    claims = verify(cred.credentials) if cred else None
    if not claims or claims.get("app") != "console":
        raise HTTPException(401, "sessão inválida ou expirada")
    with session_scope() as db:
        u = db.get(AdminUser, int(claims["sub"]))
        if not u or not u.active:
            raise HTTPException(401, "utilizador inativo")
        return user_json(u)


def can(*roles: str):
    """Dependencia: o papel do utilizador tem de estar em `roles` (admin passa sempre)."""
    def dep(user: dict = Depends(current)) -> dict:
        if user["role"] != "admin" and user["role"] not in roles:
            raise HTTPException(403, "sem permissão para esta ação")
        return user
    return dep


def audit(db, user: dict, action: str, entity: str = "", entity_id="", detail: str = ""):
    db.add(AuditLog(admin_id=user["id"], admin_email=user["email"], action=action, entity=entity,
                    entity_id=str(entity_id), detail=detail[:2000]))
