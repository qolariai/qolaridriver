# -*- coding: utf-8 -*-
"""Rate limit em memória."""
from core.ratelimit import allow, reset


def test_rate_limit_window():
    reset()
    assert allow("k", 2, 60)
    assert allow("k", 2, 60)
    assert not allow("k", 2, 60)
    assert allow("outro", 1, 60)
    reset()
