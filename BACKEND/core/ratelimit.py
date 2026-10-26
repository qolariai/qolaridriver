# -*- coding: utf-8 -*-
"""Rate limit em memória (janela deslizante) para o laboratório.

Não substitui um API gateway: é uma barreira barata para login emap-report. O estado
vive no processo; com vários workers, cada um tem a sua janela.
"""
import threading
import time
from collections import defaultdict, deque

_hits: dict[str, deque[float]] = defaultdict(deque)
_lock = threading.Lock()


def allow(key: str, limit: int, window_s: float = 60.0) -> bool:
    now = time.time()
    with _lock:
        q = _hits[key]
        while q and q[0] <= now - window_s:
            q.popleft()
        if len(q) >= limit:
            return False
        q.append(now)
        if len(_hits) > 4096:
            for k in list(_hits)[:512]:
                _hits.pop(k, None)
        return True


def reset() -> None:
    with _lock:
        _hits.clear()
