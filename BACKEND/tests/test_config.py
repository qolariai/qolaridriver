# -*- coding: utf-8 -*-
"""Guarda de produção: recusa defaults do laboratório."""
import pytest

import config


def _safe(monkeypatch):
    monkeypatch.setattr(config, "PRODUCTION", True)
    monkeypatch.setattr(config, "SECRET", "x" * 32)
    monkeypatch.setattr(config, "ADMIN_PASSWORD", "nao-e-admin")
    monkeypatch.setattr(config, "STRICT_AUTH", True)
    monkeypatch.setattr(config, "DB_URL", "postgresql+psycopg://qolari:x@db/qolari")
    monkeypatch.setattr(config, "RATE_LIMIT", True)
    monkeypatch.setattr(config, "OTP_CODE", "847261")
    monkeypatch.setattr(config, "PUBLIC_HOST", "driver.qolari.com")
    monkeypatch.setenv("GOOGLE_MAPS_KEY", "test-key")


def test_production_accepts_safe_config(monkeypatch):
    _safe(monkeypatch)
    assert config.production_problems() == []
    config.validate_production()


def test_production_refuses_lab_defaults(monkeypatch):
    _safe(monkeypatch)
    monkeypatch.setattr(config, "SECRET", "qolari-lab-trocar")
    monkeypatch.setattr(config, "STRICT_AUTH", False)
    problems = config.production_problems()
    assert any("SECRET" in p for p in problems)
    assert any("STRICT_AUTH" in p for p in problems)
    with pytest.raises(RuntimeError):
        config.validate_production()
