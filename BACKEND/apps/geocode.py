# -*- coding: utf-8 -*-
"""Geocodificacao inversa (coordenadas -> morada) com a Google Geocoding API, com cache.

Chave: env GOOGLE_MAPS_KEY (vazia = desligado, usado nos testes); senao data/google_maps_api_key.txt
(no servidor) ou ../ANDOIRD/google_maps_api_key.txt (no PC). Cache em memoria + data/geocode_cache.json,
por coordenada arredondada a 4 casas (~11 m). Sem chave ou com erro devolve um resultado so com coordenadas
(nunca lanca: quem chama e um handler das apps).
"""
import json, os, threading

import config

LANG = "pt-PT"
_lock = threading.Lock()
_cache: dict | None = None
_CACHE_FILE = config.DATA_DIR / "geocode_cache.json"


def _key() -> str:
    if "GOOGLE_MAPS_KEY" in os.environ:
        return os.environ["GOOGLE_MAPS_KEY"].strip()
    for p in (config.DATA_DIR / "google_maps_api_key.txt", config.BASE_DIR.parent / "google_maps_api_key.txt",
              config.BASE_DIR.parent / "ANDOIRD" / "google_maps_api_key.txt"):
        if p.is_file():
            return p.read_text(encoding="utf-8").strip()
    return ""


def _load() -> dict:
    global _cache
    if _cache is None:
        try:
            _cache = json.loads(_CACHE_FILE.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            _cache = {}
    return _cache


def _parse(res: dict, lat: float, lng: float) -> dict:
    """Resultado da Google -> {id, name, line1, line2, full, provider}. Portugal: 'Rua X 181' / '2700-312 Amadora'."""
    comps = {}
    for c in res.get("address_components") or []:
        for t in c.get("types") or []:
            comps.setdefault(t, c.get("long_name") or "")
    full = res.get("formatted_address") or ""
    parts = [p.strip() for p in full.split(",") if p.strip()]
    if parts and parts[-1] in ("Portugal", comps.get("country")):
        parts = parts[:-1]
    poi = None
    if set(res.get("types") or []) & {"establishment", "point_of_interest", "airport", "transit_station"} and len(parts) > 1:
        poi, parts = parts[0], parts[1:]  # "Aeroporto ... (LIS), Alameda ..., 1700-111 Lisboa"
    route, num = comps.get("route"), comps.get("street_number")
    line1 = f"{route} {num}" if route and num else (route or (parts[0] if parts else ""))
    # 1.a parte da formatted_address = a rua (em forma curta, "R. ..."); o resto e codigo postal e localidade
    line2 = ", ".join(parts[1:]) or comps.get("locality") or comps.get("administrative_area_level_2") or ""
    return {"id": res.get("place_id") or f"geo:{lat:.6f},{lng:.6f}", "name": poi or line1 or full, "line1": line1,
            "line2": line2, "full": full, "provider": "google_places"}


def _fallback(lat: float, lng: float) -> dict:
    s = f"{lat:.5f}, {lng:.5f}"
    return {"id": f"geo:{lat:.6f},{lng:.6f}", "name": s, "line1": s, "line2": "", "full": s, "provider": "qolari"}


def reverse(lat: float, lng: float) -> dict:
    ck = f"{lat:.4f},{lng:.4f}"
    with _lock:
        hit = _load().get(ck)
    if hit:
        return hit
    key = _key()
    if not key:
        return _fallback(lat, lng)
    try:
        import httpx
        r = httpx.get("https://maps.googleapis.com/maps/api/geocode/json",
                      params={"latlng": f"{lat},{lng}", "language": LANG, "key": key}, timeout=4.0)
        data = r.json()
    except Exception:
        return _fallback(lat, lng)
    results = [x for x in data.get("results") or [] if "plus_code" not in (x.get("types") or [])]
    if data.get("status") != "OK" or not results:
        return _fallback(lat, lng)
    out = _parse(results[0], lat, lng)
    with _lock:
        _load()[ck] = out
        try:
            _CACHE_FILE.write_text(json.dumps(_cache, ensure_ascii=False), encoding="utf-8")
        except OSError:
            pass
    return out


def places_search(query: str, near_lat: float | None = None, near_lng: float | None = None,
                  limit: int = 8) -> list[dict]:
    """Pesquisa de locais/POIs (Google Places Text Search). Sem chave/erro devolve []."""
    q = (query or "").strip()
    if not q:
        return []
    lat0 = near_lat if near_lat is not None else 38.7223
    lng0 = near_lng if near_lng is not None else -9.1393
    ck = f"p:{q.lower()}@{lat0:.3f},{lng0:.3f}"
    with _lock:
        hit = _load().get(ck)
    if hit is not None:
        return hit
    key = _key()
    if not key:
        return []
    params = {"query": q, "location": f"{lat0},{lng0}", "radius": "30000",
              "language": LANG, "region": "pt", "key": key}
    try:
        import httpx
        r = httpx.get("https://maps.googleapis.com/maps/api/place/textsearch/json", params=params, timeout=5.0)
        data = r.json()
    except Exception:
        return []
    if data.get("status") not in ("OK", "ZERO_RESULTS"):
        return []
    out = []
    for res in (data.get("results") or [])[:limit]:
        loc = (res.get("geometry") or {}).get("location") or {}
        lat, lng = loc.get("lat"), loc.get("lng")
        if lat is None or lng is None:
            continue
        full = res.get("formatted_address") or res.get("name") or ""
        out.append({
            "id": res.get("place_id") or f"place:{lat:.6f},{lng:.6f}",
            "name": res.get("name") or full,
            "line1": full,
            "line2": "",
            "full": full,
            "lat": float(lat),
            "lng": float(lng),
            "provider": "google_places",
        })
    with _lock:
        _load()[ck] = out
        try:
            _CACHE_FILE.write_text(json.dumps(_cache, ensure_ascii=False), encoding="utf-8")
        except OSError:
            pass
    return out


def forward(query: str, near_lat: float | None = None, near_lng: float | None = None,
            limit: int = 8) -> list[dict]:
    """Pesquisa de moradas/locais (texto -> resultados com coordenadas). Sem chave/erro devolve []."""
    q = (query or "").strip()
    if not q:
        return []
    bias = f"@{near_lat:.3f},{near_lng:.3f}" if near_lat is not None and near_lng is not None else ""
    ck = f"q:{q.lower()}{bias}"
    with _lock:
        hit = _load().get(ck)
    if hit is not None:
        return hit
    key = _key()
    if not key:
        return []
    params = {"address": q, "language": LANG, "key": key, "components": "country:PT", "region": "pt"}
    if near_lat is not None and near_lng is not None:
        params["bounds"] = f"{near_lat - 0.25:.4f},{near_lng - 0.45:.4f}|{near_lat + 0.25:.4f},{near_lng + 0.45:.4f}"
    else:
        params["bounds"] = "38.60,-9.30|38.85,-9.05"
    try:
        import httpx
        r = httpx.get("https://maps.googleapis.com/maps/api/geocode/json", params=params, timeout=4.0)
        data = r.json()
    except Exception:
        return []
    if data.get("status") != "OK":
        return []
    out = []
    for res in (data.get("results") or [])[:limit]:
        loc = (res.get("geometry") or {}).get("location") or {}
        lat, lng = loc.get("lat"), loc.get("lng")
        if lat is None or lng is None:
            continue
        p = _parse(res, float(lat), float(lng))
        p.update({"lat": float(lat), "lng": float(lng)})
        out.append(p)
    with _lock:
        _load()[ck] = out
        try:
            _CACHE_FILE.write_text(json.dumps(_cache, ensure_ascii=False), encoding="utf-8")
        except OSError:
            pass
    return out
