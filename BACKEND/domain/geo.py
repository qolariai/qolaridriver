# -*- coding: utf-8 -*-
"""Geometria simples (sem servicos externos): distancias, estimativas e movimento simulado."""
import math

EARTH_M = 6_371_000


def haversine_m(lat1, lng1, lat2, lng2) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_M * math.asin(math.sqrt(a))


def bearing(lat1, lng1, lat2, lng2) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lng2 - lng1)
    x = math.sin(dl) * math.cos(p2)
    y = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    return (math.degrees(math.atan2(x, y)) + 360) % 360


def road_estimate(lat1, lng1, lat2, lng2, road_factor: float, speed_kmh: float) -> tuple[int, int]:
    """-> (distancia em metros, duracao em segundos) por estrada (aproximado)."""
    dist = haversine_m(lat1, lng1, lat2, lng2) * road_factor
    return int(dist), int(dist / (speed_kmh / 3.6)) if speed_kmh > 0 else 0


def step_towards(lat, lng, tlat, tlng, meters: float) -> tuple[float, float, float, bool]:
    """Avanca `meters` em linha reta -> (lat, lng, rumo, chegou)."""
    total = haversine_m(lat, lng, tlat, tlng)
    head = bearing(lat, lng, tlat, tlng)
    if total <= meters or total < 1:
        return tlat, tlng, head, True
    f = meters / total
    return lat + (tlat - lat) * f, lng + (tlng - lng) * f, head, False


def parse_point(text: str) -> tuple[float, float] | None:
    """'38.72,-9.14' -> (38.72, -9.14)."""
    try:
        a, b = text.split(",")
        lat, lng = float(a), float(b)
    except (ValueError, AttributeError):
        return None
    if -90 <= lat <= 90 and -180 <= lng <= 180:
        return lat, lng
    return None
