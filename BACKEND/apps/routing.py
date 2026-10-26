# -*- coding: utf-8 -*-
"""Rota entre dois pontos. Sem chave nem rede, usa a linha reta com a velocidade media da cidade (30 km/h);
com `ROUTING_URL` (um servidor OSRM, ex.: http://127.0.0.1:5000) pede a rota real. Nunca levanta: se o servico falhar, cai na linha reta."""
import json
import math
import os
import threading
import time
import urllib.request

AVG_KMH = 30.0
CACHE_TTL_S = float(os.environ.get("ROUTE_CACHE_TTL_S", "600"))
_FAIL_TTL_S = 60.0

_cache: dict[tuple, tuple[float, dict]] = {}
_lock = threading.Lock()


def haversine_m(a: tuple, b: tuple) -> float:
    r = 6371000.0
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dp, dl = p2 - p1, math.radians(b[1] - a[1])
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def points_from(body: dict, query: dict | None = None):
    """((lat, lng), (lat, lng)) a partir de {origin, destination}, {start, end} ou dos parametros da query."""
    src = dict(query or {})
    src.update(body or {})
    for a, b in (("origin", "destination"), ("start", "end"), ("from", "to")):
        o, d = src.get(a), src.get(b)
        if isinstance(o, dict) and isinstance(d, dict):
            p = (_num(o.get("latitude", o.get("lat"))), _num(o.get("longitude", o.get("lng"))))
            q = (_num(d.get("latitude", d.get("lat"))), _num(d.get("longitude", d.get("lng"))))
            if None not in p and None not in q:
                return p, q
    return None


def _straight(a: tuple, b: tuple) -> dict:
    dist = haversine_m(a, b)
    return {"source": "straight_line", "distanceMeters": round(dist), "durationSeconds": round(dist / (AVG_KMH / 3.6)),
            "polyline": [{"latitude": a[0], "longitude": a[1]}, {"latitude": b[0], "longitude": b[1]}]}


def route(a: tuple, b: tuple) -> dict:
    url = os.environ.get("ROUTING_URL", "").rstrip("/")
    key = (round(a[0], 5), round(a[1], 5), round(b[0], 5), round(b[1], 5), url)
    now = time.time()
    with _lock:
        hit = _cache.get(key)
        if hit and hit[0] > now:
            return hit[1]
    result = None
    if url:
        try:
            req = f"{url}/route/v1/driving/{a[1]},{a[0]};{b[1]},{b[0]}?overview=full&geometries=geojson"
            with urllib.request.urlopen(req, timeout=4) as r:
                data = json.load(r)
            rt = data["routes"][0]
            result = {"source": "osrm", "distanceMeters": round(rt["distance"]), "durationSeconds": round(rt["duration"]),
                      "polyline": [{"latitude": lat, "longitude": lng} for lng, lat in rt["geometry"]["coordinates"]]}
        except Exception:
            result = None
    if result is None:
        result = _straight(a, b)
    ttl = CACHE_TTL_S if result.get("source") == "osrm" else _FAIL_TTL_S
    with _lock:
        _cache[key] = (now + ttl, result)
        if len(_cache) > 512:
            for k in list(_cache)[:128]:
                _cache.pop(k, None)
    return result
