# -*- coding: utf-8 -*-
"""FCM: no-op sem conta de serviço e texto das notificações."""
import config
from apps import fcm
from domain.push import _notification


def test_fcm_disabled_without_service_account(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "FCM_SERVICE_ACCOUNT", tmp_path / "missing.json")
    assert fcm.enabled() is False
    fcm.queue_push("token", "t", "b")  # não pode lançar


def test_offer_and_trip_notification_text():
    title, body = _notification("push_driver_unified_offers_v3", {})
    assert "viagem" in title.lower() and body
    title, body = _notification("trip_status", {"state": "accepted"})
    assert "accepted" in body
