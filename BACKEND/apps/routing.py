# -*- coding: utf-8 -*-
"""Rota entre dois pontos. Sem chave nem rede, usa a linha reta com a velocidade media da cidade (30 km/h);
com `ROUTING_URL` (um servidor OSRM, ex.: http://127.0.0.1:5000) pede a rota real. Nunca levanta: se o servico falhar, cai na linha reta."""
import json
import math
import os
import urllib.request

AVG_KMH = 30.0


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
    """Rota por estradas: OSRM (se ROUTING_URL) -> Google Directions (se GOOGLE_MAPS_KEY) -> reta.

    A reta e so o ultimo recurso: as apps nao a devem desenhar (regra do projeto), mas o contrato
    devolve sempre polyline para o cliente nao quebrar.
    """
    url = os.environ.get("ROUTING_URL", "").rstrip("/")
    if url:
        try:
            req = f"{url}/route/v1/driving/{a[1]},{a[0]};{b[1]},{b[0]}?overview=full&geometries=geojson"
            with urllib.request.urlopen(req, timeout=4) as r:
                data = json.load(r)
            rt = data["routes"][0]
            return {"source": "osrm", "distanceMeters": round(rt["distance"]), "durationSeconds": round(rt["duration"]),
                    "polyline": [{"latitude": lat, "longitude": lng} for lng, lat in rt["geometry"]["coordinates"]]}
        except Exception:
            pass
    g = _google(a, b)
    if g:
        return g
    return _straight(a, b)


def _google_key() -> str:
    """Chave do Google Maps: env GOOGLE_MAPS_KEY ou o ficheiro google_maps_api_key.txt na raiz do projeto.

    Se a variavel de ambiente estiver definida (mesmo vazia) e ela que manda: os testes poem
    `GOOGLE_MAPS_KEY=""` para garantir que nada sai para a rede.
    """
    if "GOOGLE_MAPS_KEY" in os.environ:
        return os.environ["GOOGLE_MAPS_KEY"].strip()
    # BACKEND/apps/routing.py -> BACKEND -> raiz do projeto
    here = os.path.dirname(os.path.abspath(__file__))
    for base in (os.path.dirname(here), os.path.dirname(os.path.dirname(here))):
        try:
            with open(os.path.join(base, "google_maps_api_key.txt"), encoding="utf-8") as f:
                k = f.read().strip()
            if k:
                return k
        except OSError:
            continue
    return ""


def _decode_polyline(encoded: str) -> list:
    """Descodifica a polilinha do Google Directions (precisao 1e5)."""
    out, index, lat, lng = [], 0, 0, 0
    while index < len(encoded):
        for which in (0, 1):
            shift, result = 0, 0
            while True:
                b = ord(encoded[index]) - 63
                index += 1
                result |= (b & 0x1F) << shift
                shift += 5
                if b < 0x20:
                    break
            delta = ~(result >> 1) if result & 1 else (result >> 1)
            if which == 0:
                lat += delta
            else:
                lng += delta
        out.append({"latitude": lat / 1e5, "longitude": lng / 1e5})
    return out


def _google(a: tuple, b: tuple) -> dict | None:
    """Rota por estradas do Google Directions; None se nao houver chave, rede ou resposta valida."""
    key = _google_key()
    if not key:
        return None
    url = (f"https://maps.googleapis.com/maps/api/directions/json?origin={a[0]},{a[1]}"
           f"&destination={b[0]},{b[1]}&mode=driving&overview=full&language=pt-PT&key={key}")
    try:
        with urllib.request.urlopen(url, timeout=6) as r:
            data = json.load(r)
        if data.get("status") != "OK" or not data.get("routes"):
            return None
        rt = data["routes"][0]
        leg = (rt.get("legs") or [{}])[0]
        pts = _decode_polyline(rt.get("overview_polyline", {}).get("points", ""))
        if len(pts) < 2:
            return None
        return {"source": "google", "distanceMeters": round(leg.get("distance", {}).get("value", 0)),
                "durationSeconds": round(leg.get("duration", {}).get("value", 0)), "polyline": pts,
                # Manobras para o painel de navegacao (seta + rua + distancia ate a manobra).
                "steps": _steps(leg)}
    except Exception:
        return None


def _steps(leg: dict) -> list:
    """Manobras da perna no formato que a app desenha.

    Cada passo leva a instrucao, a rua, a distancia/duracao, o tipo de manobra do Google
    (turn-left, roundabout, straight...) e o polyline do passo.

    O nome da via vem do OSM local (`apps/osmgeo.py`), a partir do ponto medio do passo e do rumo
    do segmento. Sem base OSM cai no parsing da instrucao (o Google nao manda short_name/long_name).
    """
    from apps import osmgeo

    out = []
    for st in leg.get("steps") or []:
        html = st.get("html_instructions") or ""
        line = st.get("polyline", {}).get("points", "")
        pts = _decode_polyline(line)
        end = st.get("end_location") or {}
        maneuver = st.get("maneuver") or ""

        # Ponto medio + rumo do passo: e onde o motorista vai passar.
        road_osm = None
        if len(pts) >= 2:
            mid = pts[len(pts) // 2]
            a = pts[0]
            b = pts[min(1, len(pts) - 1)]
            heading = _bearing(a["latitude"], a["longitude"], b["latitude"], b["longitude"])
            road_osm = osmgeo.lookup(mid["latitude"], mid["longitude"], heading)

        street = road_name_from_instruction(html, maneuver)
        name = (road_osm or {}).get("name") or street
        out.append({
            "instruction": _plain(html),
            # Texto curto para o painel: o Maps mostra a manobra, nao a frase inteira.
            "instructionShort": _short_instruction(_plain(html), maneuver, name),
            "road": name,
            "roadLong": name,
            "roadSource": "osm" if (road_osm or {}).get("name") else ("instruction" if street else "none"),
            "maneuver": maneuver,
            "distanceMeters": round(st.get("distance", {}).get("value", 0)),
            "durationSeconds": round(st.get("duration", {}).get("value", 0)),
            "startLat": (st.get("start_location") or {}).get("lat"),
            "startLng": (st.get("start_location") or {}).get("lng"),
            "endLat": end.get("lat"),
            "endLng": end.get("lng"),
            "lat": end.get("lat"),
            "lng": end.get("lng"),
            "polyline": pts,
        })
    return out


def _short_instruction(text: str, maneuver: str, road: str) -> str:
    """Frase curta da manobra para o painel preto ("Vire à direita", "Na rotunda, 2.ª saída").

    O Google escreve frases longas ("Na rotunda, siga pela 2.ª saída para R. X em direção a Y");
    o painel do Maps mostra o essencial. A via vai na linha de baixo, por isso corta-se ali.
    """
    import re

    # "Na rotunda, siga pela 2.ª saída para ..." -> "Na rotunda, 2.ª saída"
    m = re.search(r"rotunda.*?(\d+\.?ª?)\s*sa[ií]da", text, re.I)
    if m:
        return "Na rotunda, %s.ª saída" % re.sub(r"\D", "", m.group(1))
    # "Vire à direita em direção a X" -> "Vire à direita"
    m = re.match(r"(vire|virar|curva|mantenha|continue|siga|convergir|converja)(.*?)"
                 r"(?:\s+em dire[çc][ãa]o a|\s+para\s+[A-Z]|\s+at[ée]\s+[A-Z]|$)", text, re.I)
    if m:
        head = (m.group(1) + m.group(2)).strip().rstrip(",.;")
        # "Continue até X" / "Siga para oeste na Y": sem o complemento ficaria só "Continue"/"Siga",
        # que nao diz nada ao condutor. Nesses casos fica a via (ou a instrucao inteira, mais abaixo).
        if head.lower() in ("continue", "siga", "convergir", "converja", "mantenha"):
            return text
        return head[0].upper() + head[1:]
    return text


def _bearing(lat1, lon1, lat2, lon2) -> float:
    """Rumo de a->b em graus (0 = norte)."""
    import math
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    x = math.sin(dl) * math.cos(p2)
    y = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    return (math.degrees(math.atan2(x, y)) + 360) % 360


# Palavras que aparecem a negrito mas NAO sao nomes de rua.
NOT_A_STREET = {
    "direita", "esquerda", "em frente", "norte", "sul", "este", "oeste",
    "nordeste", "noroeste", "sudeste", "sudoeste", "ligeira", "acentuada",
    "saída", "saida", "rotunda", "convergir", "continue", "siga",
}


def road_name_from_instruction(html: str, maneuver: str = "") -> str:
    """Nome da via a partir do HTML do Google (fallback quando nao ha OSM).

    Regras (medidas em instrucoes reais em pt-PT):
      - "Siga para <b>este</b> na <b>Praça do Comércio</b> em direção a <b>Rua X</b>"
            -> rua atual = 2.o negrito ("Praça do Comércio")
      - "Vire <b>à direita</b> em direção a <b>R. X</b>"      -> "R. X"
      - "Continue até <b>Rua X</b>"                            -> "Rua X"
      - "Convergir com <b>Rua X</b>"                           -> "Rua X"
      - "Na rotunda, siga pela <b>1.ª</b> saída para <b>R. X</b>" -> "R. X"
      - "Na rotunda, siga pela <b>1.ª</b> saída"               -> ""
      - "Curva ligeira à <b>direita</b>" / "Vire à <b>direita</b>" -> ""
      - Varios nomes com <wbr/> -> fica o primeiro ("Lgo. X/wbr/R. Y" -> "Lgo. X")
    """
    import html as _html
    import re

    # Os <div> do Google trazem a distancia ("<div style=...>80 m</div>"), nao interessam.
    text = re.sub(r"<div[^>]*>.*?</div>", " ", html or "", flags=re.S)

    def bold_after(connector: str) -> str:
        """Primeiro <b> que vem a seguir ao conector ("em direção a", "até", " na ", ...)."""
        m = re.search(connector + r"\s*<b>(.*?)</b>", text, flags=re.S | re.I)
        return _html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip() if m else ""

    def clean(value: str) -> str:
        # "A/<wbr/>B" sao nomes alternativos da MESMA via: fica o primeiro.
        value = re.split(r"/\s*<wbr\s*/?>", value, flags=re.I)[0]
        value = re.split(r"<wbr\s*/?>", value, flags=re.I)[0]
        value = re.sub(r"<[^>]+>", " ", value)
        value = value.split("|")[0].strip(" /;,")
        low = value.lower().strip(" .ªº")
        if not value or low in NOT_A_STREET or re.fullmatch(r"\d+\.?ª?", low):
            return ""
        return value

    straight = (not maneuver) or maneuver == "straight"

    # 1) "Siga para <b>oeste</b> na <b>Rua X</b>": em frente, a via e a que se esta a percorrer.
    if straight:
        found = clean(bold_after(r"\bna"))
        if found:
            return found

    # 2) Rua de entrada/destino, por ordem de especificidade.
    #    "convergir com" vem antes de "em direção a" porque no mesmo passo pode haver as duas
    #    ("... convergir com <b>CRIL</b> em direção a <b>Zona X</b>") e a via e a primeira.
    for connector in (r"convergir com", r"em dire(?:ç|c)(?:ã|a)o a", r"para", r"at(?:é|e)"):
        found = clean(bold_after(connector))
        if found:
            return found

    # 3) Ultimo recurso: o unico negrito que restar (nunca uma direcao nem "1.ª").
    parts = [clean(m) for m in re.findall(r"<b>(.*?)</b>", text, flags=re.S)]
    parts = [p for p in parts if p]
    return parts[-1] if parts else ""


def _bold_parts(html: str) -> list:
    """Textos a negrito da instrucao (os nomes de rua do Google vêm em <b>)."""
    import html as _html
    import re
    return [_html.unescape(re.sub(r"<[^>]+>", "", m)).strip() for m in re.findall(r"<b>(.*?)</b>", html, flags=re.S)]


def _plain(html: str) -> str:
    """Tira o HTML das instrucoes do Google (inclui as <div> da distancia)."""
    import html as _html
    import re
    text = re.sub(r"<div[^>]*>.*?</div>", " ", html, flags=re.S)
    text = re.sub(r"<[^>]+>", "", text)
    return _html.unescape(text).strip().replace("  ", " ")


# Limite de velocidade estimado por tipo de via. O Google Directions nao devolve o limite
# (so a Roads API, com outro custo), por isso usamos o tipo de manobra/rua como aproximacao.
SPEED_BY_MANEUVER = {
    "roundabout": 30,
    "rotary": 30,
    "ramp": 50,
    "merge": 60,
    "fork": 50,
}


def speed_limit(step: dict | None, lat=None, lon=None, heading=None) -> int:
    """Limite da via (km/h): OSM local primeiro, heuristica por via/manobra depois.

    O Google Directions nao devolve o limite (roads.speedLimits da 403 neste projeto), por isso o
    dado vem do OSM. Sem base OSM, mantem-se a heuristica que ja existia.
    """
    if lat is not None and lon is not None:
        from apps import osmgeo
        found = osmgeo.lookup(lat, lon, heading)
        if found:
            return int(found["kmh"])
    return _speed_fallback(step)


def speed_source(step: dict | None, lat=None, lon=None, heading=None) -> str:
    """De onde veio o limite: "osm" (dado da via), "osm_class" (estimativa no OSM) ou "heuristic"."""
    if lat is not None and lon is not None:
        from apps import osmgeo
        found = osmgeo.lookup(lat, lon, heading)
        if found:
            return "osm" if found.get("explicit") else "osm_class"
    return "heuristic"


def _speed_fallback(step: dict | None) -> int:
    if not step:
        return 50
    man = step.get("maneuver") or ""
    for key, value in SPEED_BY_MANEUVER.items():
        if man.startswith(key):
            return value
    road = (step.get("road") or "").upper()
    if road.startswith(("A ", "A-", "AUTOESTRADA", "IP", "IC", "E ")):
        return 120
    if road.startswith(("N ", "N-", "EN ")):
        return 90
    return 50

