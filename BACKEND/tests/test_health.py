# -*- coding: utf-8 -*-
"""Health/readiness."""
from main import health


def test_health_checks_database():
    h = health()
    assert h["ok"] is True and h["db"] == "ok"
    assert h["environment"] in ("lab", "production")
    assert "ports" in h
