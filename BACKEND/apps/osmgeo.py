# -*- coding: utf-8 -*-
"""Indice OSM local: nome da via e limite de velocidade no ponto onde o motorista esta.

Porquê
------
O Google Directions nao devolve o nome da via nos `steps` (nem `short_name`/`long_name` nem sempre
manobra) e o Roads API `speedLimits` devolve 403 para este projeto (licenca Asset Tracking). O OSM
tem ambos: `name` e `maxspeed`, por via, com coordenadas.

Como
----
`tools/osm_build.py` gera `data/osm_local.sqlite` com as vias e os seus segmentos (R*Tree).
Aqui encontra-se o segmento mais proximo do ponto (< `radius_m`), resolve-se o sentido (oneway /
rotunda / rumo do motorista) e le-se:

    maxspeed:forward / maxspeed:backward  ->  maxspeed  ->  tabela por classe de via

Sem base (ou com `SPEED_LIMIT_PROVIDER=heuristic`) tudo devolve None e o chamador usa a heuristica
que ja existia. Nunca acede a rede.
"""
import math
import os
import sqlite3
import threading
from functools import lru_cache

import config

# Limite por classe de via (km/h), usado quando a via nao tem `maxspeed`.
# Mantem os valores da heuristica anterior para nao mudar o que ja estava validado.
KMH_BY_CLASS = {
    "motorway": 120,
    "motorway_link": 50,
    "trunk": 90,
    "trunk_link": 50,
    "primary": 90,
    "primary_link": 50,
    "secondary": 90,
    "secondary_link": 50,
    "tertiary": 90,
    "tertiary_link": 50,
    "unclassified": 50,
    "residential": 50,
    "living_street": 20,
    "service": 30,
}
KMH_ROUNDABOUT = 30
KMH_DEFAULT = 50

# O bonus de classe so tira o ponto de uma via que esteja a esta distancia ou menos.
# Acima disto, ganha sempre a via geometricamente mais perto.
MAX_BONUS_DIST_M = 15

# Desempate por classe de via (metros de "bonus"): quando ha duas vias a distancias parecidas
# (autoestrada e a via de servico ao lado), ganha a de maior hierarquia. E o que o Maps faz ao
# decidir em que via o carro esta. Sem isto, uma rua de servico a 3 m "ganhava" a autoestrada a 6 m.
CLASS_BONUS_M = {
    "motorway": 14,
    "trunk": 12,
    "primary": 10,
    "secondary": 8,
    "tertiary": 6,
    "unclassified": 3,
    "residential": 2,
    "living_street": 1,
    "service": 0,
    "motorway_link": 6,
    "trunk_link": 5,
    "primary_link": 4,
    "secondary_link": 3,
    "tertiary_link": 2,
}

_local = threading.local()


def db_path() -> str:
    """Caminho da base: env OSM_DB ou data/osm_local.sqlite."""
    env = os.environ.get("OSM_DB")
    if env is not None:
        return env
    return os.path.join(str(config.DATA_DIR), "osm_local.sqlite")


def _conn():
    """Conexao por thread (o servidor usa threads). None se nao houver base."""
    path = db_path()
    if not path or not os.path.exists(path):
        return None
    conn = getattr(_local, "conn", None)
    if conn is None or getattr(_local, "path", None) != path:
        conn = sqlite3.connect(path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        _local.conn = conn
        _local.path = path
    return conn


def available() -> bool:
    return _conn() is not None


def parse_maxspeed(value) -> int | None:
    """'50', '50 km/h', '90;70', '50 mph', 'walk', 'none' -> km/h (None se nao der para ler)."""
    if value is None:
        return None
    text = str(value).strip().lower()
    if not text:
        return None
    if text in ("walk", "walking", "passo"):
        return 5
    if text in ("none", "unlimited"):
        return 130
    if text in ("signals", "variable", "default"):
        return None
    # Varios valores ("90;70") -> o maior, que e o limite da via principal.
    parts = [p.strip() for p in text.replace(";", ",").split(",") if p.strip()]
    best = None
    for part in parts:
        num = ""
        for ch in part:
            if ch.isdigit() or ch == ".":
                num += ch
            else:
                break
        if not num:
            continue
        try:
            v = float(num)
        except ValueError:
            continue
        if "mph" in part:
            v *= 1.60934
        v = int(round(v))
        if best is None or v > best:
            best = v
    return best


def _haversine_m(lat1, lon1, lat2, lon2) -> float:
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def _bearing(lat1, lon1, lat2, lon2) -> float:
    """Rumo do segmento a->b em graus (0 = norte)."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    x = math.sin(dl) * math.cos(p2)
    y = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    return (math.degrees(math.atan2(x, y)) + 360) % 360


def _dist_to_segment(plat, plon, alat, alon, blat, blon) -> float:
    """Distancia (m) do ponto ao segmento, em projecao local (suficiente a esta escala)."""
    # Graus -> metros no ponto medio (equiretangular local).
    latm = math.radians((alat + blat) / 2)
    mx = 111320.0 * math.cos(latm)
    my = 110540.0

    ax, ay = (alon) * mx, (alat) * my
    bx, by = (blon) * mx, (blat) * my
    px, py = (plon) * mx, (plat) * my

    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)
    t = ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    cx, cy = ax + t * dx, ay + t * dy
    return math.hypot(px - cx, py - cy)


@lru_cache(maxsize=4096)
def _lookup_cached(lat5: int, lon5: int, head_bucket: int, radius_m: int):
    """Consulta memorizada. Chave arredondada a 1e-5 graus (~1 m) e rumo em passos de 45 graus."""
    conn = _conn()
    if conn is None:
        return None
    lat, lon = lat5 / 100000.0, lon5 / 100000.0
    # Caixa de busca: raio em graus (com folga).
    dlat = radius_m / 110540.0
    dlon = radius_m / (111320.0 * max(0.2, math.cos(math.radians(lat))))

    rows = conn.execute(
        "SELECT s.id, s.way_id, s.a_lat, s.a_lon, s.b_lat, s.b_lon,"
        "       w.highway, w.ref, w.name, w.oneway, w.junction,"
        "       w.maxspeed, w.maxspeed_fwd, w.maxspeed_bwd"
        "  FROM segs_rt r JOIN segs s ON s.id = r.seg_id JOIN ways w ON w.id = s.way_id"
        " WHERE r.minlat <= ? AND r.maxlat >= ? AND r.minlon <= ? AND r.maxlon >= ?",
        (lat + dlat, lat - dlat, lon + dlon, lon - dlon),
    ).fetchall()

    best = None
    best_score = None
    for row in rows:
        d = _dist_to_segment(lat, lon, row["a_lat"], row["a_lon"], row["b_lat"], row["b_lon"])
        if d > radius_m:
            continue
        # Pontuacao: distancia real menos o bonus da classe. Assim a autoestrada a 8 m ganha a
        # uma viela de servico a 2 m, mas nunca uma via a 40 m contra uma rua a 3 m.
        # O bonus so se aplica a vias a menos de MAX_BONUS_DIST_M: uma primary a 2,5 m nao deve
        # "roubar" o ponto a uma living_street em cima dela.
        bonus = CLASS_BONUS_M.get(row["highway"], 0) if d <= MAX_BONUS_DIST_M else 0
        score = d - bonus
        if best_score is None or score < best_score:
            best, best_score, best_d = row, score, d
    if best is None:
        return None

    # Sentido: rotunda e oneway seguem a->b; nas restantes, o rumo do motorista decide.
    seg_bearing = _bearing(best["a_lat"], best["a_lon"], best["b_lat"], best["b_lon"])
    forward = True
    if not best["oneway"] and best["junction"] != "roundabout" and head_bucket >= 0:
        driver_bearing = head_bucket * 45.0
        diff = abs(((driver_bearing - seg_bearing + 180) % 360) - 180)
        forward = diff <= 90

    raw = best["maxspeed_fwd"] if forward else best["maxspeed_bwd"]
    kmh = parse_maxspeed(raw) or parse_maxspeed(best["maxspeed"])
    if kmh is None:
        kmh = KMH_ROUNDABOUT if best["junction"] == "roundabout" else KMH_BY_CLASS.get(best["highway"], KMH_DEFAULT)

    return {
        "name": best["name"] or best["ref"] or "",
        "ref": best["ref"] or "",
        "kmh": int(kmh),
        "way_id": int(best["way_id"]),
        "dist_m": round(best_d, 1),
        "highway": best["highway"],
        # True quando o limite e da via (OSM) e nao a estimativa por classe.
        "explicit": bool(parse_maxspeed(raw) or parse_maxspeed(best["maxspeed"])),
    }


def lookup(lat, lon, heading=None, radius_m: int = 25):
    """Via e limite no ponto. None se nao houver base ou nenhuma via perto."""
    if lat is None or lon is None:
        return None
    if not os.environ.get("OSM_DB") and not os.path.exists(db_path()):
        return None
    head_bucket = -1 if heading is None else int(round((heading % 360) / 45.0)) % 8
    return _lookup_cached(int(round(lat * 100000)), int(round(lon * 100000)), head_bucket, int(radius_m))


def clear_cache():
    _lookup_cached.cache_clear()
