# -*- coding: utf-8 -*-
"""Limites diários/semanais por calendário (DST)."""
import time

from apps import fleet


def test_day_bounds_are_calendar_days():
    ts = int(time.mktime((2026, 10, 25, 23, 30, 0, 0, 0, -1)))  # dia da mudança de hora
    start, end = fleet._day_bounds(ts)
    lt = time.localtime(end)
    assert (lt.tm_hour, lt.tm_min) == (0, 0)
    assert lt.tm_mday == 26
    assert 86400 <= end - start <= 90000


def test_week_bounds_start_and_end_at_midnight():
    start, end = fleet._week_bounds()
    assert time.localtime(start).tm_hour == 0
    assert time.localtime(end).tm_hour == 0
    assert end > start
