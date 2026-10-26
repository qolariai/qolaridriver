# -*- coding: utf-8 -*-
"""Envio FCM HTTP v1 (conta de serviço). O `ramen` continua a ser o fallback.

A chave fica em `BACKEND/data/firebase-service-account.json` (ou FCM_SERVICE_ACCOUNT) e
nunca é versionada. Sem o ficheiro, `enabled()` é falso e tudo é no-op.
"""
import json
import queue
import threading

import httpx
from google.auth.transport.requests import Request
from google.oauth2 import service_account

import config

SCOPE = "https://www.googleapis.com/auth/firebase.messaging"
_lock = threading.Lock()
_creds = None
_queue: "queue.Queue[tuple]" = queue.Queue()
_worker: threading.Thread | None = None


def enabled() -> bool:
    return config.FCM_SERVICE_ACCOUNT.is_file()


def project_id() -> str:
    if config.FCM_PROJECT_ID:
        return config.FCM_PROJECT_ID
    try:
        return json.loads(config.FCM_SERVICE_ACCOUNT.read_text(encoding="utf-8")).get("project_id", "")
    except (OSError, ValueError):
        return ""


def _credentials():
    global _creds
    with _lock:
        if _creds is None:
            _creds = service_account.Credentials.from_service_account_file(
                str(config.FCM_SERVICE_ACCOUNT), scopes=[SCOPE],
            )
        if not _creds.valid:
            _creds.refresh(Request())
        return _creds


def _send(token: str, title: str, body: str, data: dict) -> None:
    payload = {
        "message": {
            "token": token,
            "notification": {"title": title, "body": body},
            "data": {str(k): str(v) for k, v in (data or {}).items()},
            "android": {
                "priority": "high",
                "notification": {"channel_id": "qolari_default"},
            },
        },
    }
    r = httpx.post(
        f"https://fcm.googleapis.com/v1/projects/{project_id()}/messages:send",
        headers={"Authorization": f"Bearer {_credentials().token}"},
        json=payload,
        timeout=6.0,
    )
    r.raise_for_status()


def _worker_loop() -> None:
    while True:
        item = _queue.get()
        try:
            _send(*item)
        except Exception:
            # push é acelerador, não fonte de verdade; o ramen cobre a falha
            pass
        finally:
            _queue.task_done()


def queue_push(token: str, title: str, body: str, data: dict | None = None) -> None:
    if not token or not enabled():
        return
    global _worker
    with _lock:
        if _worker is None or not _worker.is_alive():
            _worker = threading.Thread(target=_worker_loop, name="fcm", daemon=True)
            _worker.start()
    _queue.put((token, title, body, data or {}))
