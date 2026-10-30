# -*- coding: utf-8 -*-
"""Indice OSM local (limite de velocidade e nome de via) e parsing das instrucoes.

Sem rede: a base de dados e sintetica e construida no diretorio temporario de cada teste.
"""
import os
import sqlite3

import pytest

from apps import osmgeo, routing


# ---- base sintetica ---------------------------------------------------------------------------
#
# Um cruzamento em Lisboa com tudo o que interessa:
#   way 1 = Avenida da Liberdade (primary, nome, maxspeed 50), sentido unico
#   way 2 = Rua sem limite explicito (residential) -> limite por classe (50)
#   way 3 = Autoestrada (motorway, maxspeed 120, sentido unico)
#   way 4 = Rotunda (junction=roundabout) -> 30
#   way 5 = Via com limite por sentido (maxspeed:forward 70 / maxspeed:backward 50)
#   way 6 = Vía sem nome (service) -> nome cai no ref

LAT0, LON0 = 38.7200, -9.1400


def _seg(db, way_id, alat, alon, blat, blon):
    cur = db.execute(
        "INSERT INTO segs (way_id, a_lat, a_lon, b_lat, b_lon) VALUES (?,?,?,?,?)",
        (way_id, alat, alon, blat, blon),
    )
    sid = cur.lastrowid
    db.execute(
        "INSERT INTO segs_rt (seg_id, minlat, maxlat, minlon, maxlon) VALUES (?,?,?,?,?)",
        (sid, min(alat, blat), max(alat, blat), min(alon, blon), max(alon, blon)),
    )


@pytest.fixture()
def osm_db(tmp_path, monkeypatch):
    path = tmp_path / "osm.sqlite"
    db = sqlite3.connect(path)
    db.executescript(
        """
        CREATE TABLE ways (id INTEGER PRIMARY KEY, highway TEXT, ref TEXT, name TEXT,
                           oneway INTEGER DEFAULT 0, junction TEXT, maxspeed TEXT,
                           maxspeed_fwd TEXT, maxspeed_bwd TEXT);
        CREATE TABLE segs (id INTEGER PRIMARY KEY, way_id INTEGER, a_lat REAL, a_lon REAL,
                           b_lat REAL, b_lon REAL);
        CREATE VIRTUAL TABLE segs_rt USING rtree(seg_id, minlat, maxlat, minlon, maxlon);
        """
    )
    db.executemany(
        "INSERT INTO ways (id, highway, ref, name, oneway, junction, maxspeed, maxspeed_fwd, maxspeed_bwd)"
        " VALUES (?,?,?,?,?,?,?,?,?)",
        [
            (1, "primary", "N7", "Avenida da Liberdade", 1, "", "50", "", ""),
            (2, "residential", "", "Rua Sem Limite", 0, "", "", "", ""),
            (3, "motorway", "A5", "Autoestrada do Sul", 1, "", "120", "", ""),
            (4, "primary", "", "Rotunda do Marquês", 0, "roundabout", "", "", ""),
            (5, "trunk", "A36", "CRIL", 0, "", "", "70", "50"),
            (6, "service", "EM 500", "", 0, "", "", "", ""),
        ],
    )
    # Segmentos em linha reta lat->lat (sentido sul->norte, rumo 0).
    _seg(db, 1, LAT0, LON0, LAT0 + 0.001, LON0)
    _seg(db, 2, LAT0, LON0 + 0.010, LAT0 + 0.001, LON0 + 0.010)
    _seg(db, 3, LAT0, LON0 + 0.020, LAT0 + 0.001, LON0 + 0.020)
    _seg(db, 4, LAT0, LON0 + 0.030, LAT0 + 0.001, LON0 + 0.030)
    _seg(db, 5, LAT0, LON0 + 0.040, LAT0 + 0.001, LON0 + 0.040)
    _seg(db, 6, LAT0, LON0 + 0.050, LAT0 + 0.001, LON0 + 0.050)
    db.commit()
    db.close()

    monkeypatch.setenv("OSM_DB", str(path))
    osmgeo.clear_cache()
    yield path
    osmgeo.clear_cache()


# ---- lookup ------------------------------------------------------------------------------------
def test_finds_nearest_way_and_name(osm_db):
    found = osmgeo.lookup(LAT0 + 0.0004, LON0 + 0.00002, heading=0)
    assert found is not None
    assert found["name"] == "Avenida da Liberdade"
    assert found["way_id"] == 1
    assert found["dist_m"] < 5


def test_explicit_maxspeed_from_way(osm_db):
    found = osmgeo.lookup(LAT0 + 0.0004, LON0, heading=0)
    assert found["kmh"] == 50
    assert found["explicit"] is True


def test_motorway_gets_its_own_limit(osm_db):
    found = osmgeo.lookup(LAT0 + 0.0004, LON0 + 0.020, heading=0)
    assert found["highway"] == "motorway"
    assert found["kmh"] == 120
    assert found["explicit"] is True


def test_class_default_when_no_maxspeed(osm_db):
    found = osmgeo.lookup(LAT0 + 0.0004, LON0 + 0.010, heading=0)
    assert found["highway"] == "residential"
    assert found["kmh"] == 50          # tabela por classe
    assert found["explicit"] is False  # veio da estimativa


def test_roundabout_is_30(osm_db):
    found = osmgeo.lookup(LAT0 + 0.0004, LON0 + 0.030, heading=0)
    assert found["kmh"] == 30


def test_heading_picks_forward_or_backward(osm_db):
    # way 5: forward 70 / backward 50. Segmento vai sul->norte (rumo 0).
    north = osmgeo.lookup(LAT0 + 0.0004, LON0 + 0.040, heading=0)
    south = osmgeo.lookup(LAT0 + 0.0004, LON0 + 0.040, heading=180)
    assert north["kmh"] == 70
    assert south["kmh"] == 50


def test_oneway_ignores_heading(osm_db):
    # way 1 e de sentido unico: mesmo com rumo contrario, vale o maxspeed da via.
    found = osmgeo.lookup(LAT0 + 0.0004, LON0, heading=180)
    assert found["kmh"] == 50


def test_ref_used_when_no_name(osm_db):
    found = osmgeo.lookup(LAT0 + 0.0004, LON0 + 0.050, heading=0)
    assert found["name"] == "EM 500"


def test_too_far_returns_none(osm_db):
    # ~500 m a leste da via mais proxima.
    assert osmgeo.lookup(LAT0, LON0 + 0.006) is None


def test_missing_db_returns_none(tmp_path, monkeypatch):
    monkeypatch.setenv("OSM_DB", str(tmp_path / "nao_existe.sqlite"))
    osmgeo.clear_cache()
    assert osmgeo.lookup(LAT0, LON0, heading=0) is None
    osmgeo.clear_cache()


# ---- parse do maxspeed ------------------------------------------------------------------------
@pytest.mark.parametrize("raw,kmh", [
    ("50", 50),
    ("50 km/h", 50),
    ("90;70", 90),
    ("walk", 5),
    ("none", 130),
    ("signals", None),
    ("50 mph", 80),
    ("", None),
    (None, None),
])
def test_parse_maxspeed(raw, kmh):
    assert osmgeo.parse_maxspeed(raw) == kmh


# ---- parsing das instrucoes (fallback sem OSM) -------------------------------------------------
@pytest.mark.parametrize("html,maneuver,expected", [
    # "em frente": fica a rua atual (2.o negrito), nao a direcao.
    ("Siga para <b>este</b> na <b>Praça do Comércio</b> em direção a <b>Rua da Prata</b>",
     "", "Praça do Comércio"),
    ("Vire <b>à direita</b> em direção a <b>R. dos Arameiros</b>", "turn-right", "R. dos Arameiros"),
    ("Continue até <b>Rua da Bica do Sapato</b>", "straight", "Rua da Bica do Sapato"),
    ("Convergir com <b>Rua da Alfândega</b>", "merge", "Rua da Alfândega"),
    ("Na rotunda, siga pela <b>1.ª</b> saída para <b>R. C</b>", "roundabout", "R. C"),
    # Rotunda sem rua de destino: nada (antes saia "1.ª").
    ("Na rotunda, siga pela <b>1.ª</b> saída", "roundabout", ""),
    # Direcao nao e nome de via.
    ("Curva ligeira à <b>direita</b>", "turn-slight-right", ""),
    ("Vire à <b>direita</b>", "turn-right", ""),
    # Varios nomes separados por <wbr/>: fica o primeiro.
    ("Vire à <b>esquerda</b> em direção a <b>Lgo. dos Caminhos de Ferro</b>/<wbr/><b>R. Teixeira Lopes</b>",
     "turn-left", "Lgo. dos Caminhos de Ferro"),
    ("Continue até <b>2ª Circular</b>/<wbr/><b>A37</b>", "straight", "2ª Circular"),
])
def test_road_name_from_instruction(html, maneuver, expected):
    assert routing.road_name_from_instruction(html, maneuver) == expected


def test_road_name_ignores_distance_div():
    html = ("Siga na <b>Av. da Liberdade</b><div style=\"font-size:0.9em\">250 m</div>")
    assert routing.road_name_from_instruction(html, "straight") == "Av. da Liberdade"


# ---- speed_limit: OSM, classe e heuristica ----------------------------------------------------
def test_speed_limit_uses_osm(osm_db):
    assert routing.speed_limit(None, LAT0 + 0.0004, LON0, 0) == 50
    assert routing.speed_source(None, LAT0 + 0.0004, LON0, 0) == "osm"


def test_speed_limit_osm_class(osm_db):
    assert routing.speed_limit(None, LAT0 + 0.0004, LON0 + 0.010, 0) == 50
    assert routing.speed_source(None, LAT0 + 0.0004, LON0 + 0.010, 0) == "osm_class"


def test_speed_limit_falls_back_to_heuristic_without_db(tmp_path, monkeypatch):
    monkeypatch.setenv("OSM_DB", str(tmp_path / "nada.sqlite"))
    osmgeo.clear_cache()
    # Heuristica antiga: manobra de rotunda -> 30, sem dados -> 50.
    assert routing.speed_limit({"maneuver": "roundabout"}) == 30
    assert routing.speed_limit({"maneuver": "ramp"}) == 50
    assert routing.speed_limit({"road": "A 5"}) == 120
    assert routing.speed_limit({"road": "N 7"}) == 90
    assert routing.speed_limit(None) == 50
    assert routing.speed_source(None) == "heuristic"
    osmgeo.clear_cache()
