# -*- coding: utf-8 -*-
"""Versao global de mudancas + espera bloqueante (handlers correm em threads)."""
import threading

_cond = threading.Condition()
_version = 0


def publish(topics=None) -> None:
    global _version
    with _cond:
        _version += 1
        _cond.notify_all()


def version() -> int:
    return _version


def wait(since: int, timeout: float) -> int:
    """Bloqueia ate a versao mudar (ou timeout) -> versao atual."""
    with _cond:
        _cond.wait_for(lambda: _version != since, timeout=timeout)
        return _version
