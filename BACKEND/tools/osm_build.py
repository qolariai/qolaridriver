# -*- coding: utf-8 -*-
"""Constroi o indice OSM local (limites de velocidade e nomes de via) a partir de um PBF.

Uso (offline; nao corre no arranque do servidor nem nos testes):

    python tools/osm_build.py --pbf data/portugal-latest.osm.pbf --out data/osm_local.sqlite

Pode receber varios --pbf (ex.: Portugal + Espanha) e escreve sempre na mesma base.

O que guarda
------------
Só as vias onde se conduz (`highway` de estrada) e, dessas, o essencial:
  ways(id, highway, ref, name, oneway, junction, maxspeed, maxspeed_fwd, maxspeed_bwd)
  segs(id, way_id, a_lat, a_lon, b_lat, b_lon)      -- um registo por par de nos consecutivos
  segs_rt(seg_id, minlat, maxlat, minlon, maxlon)   -- indice espacial (R*Tree)

O runtime (`apps/osmgeo.py`) encontra o segmento mais próximo e le o limite da via.
Sem este ficheiro o backend usa a heuristica por classe (como antes).
"""
import argparse
import os
import sqlite3
import sys
import time

# Classes onde se conduz e que interessam para navegacao.
DRIVABLE = {
    "motorway", "trunk", "primary", "secondary", "tertiary", "unclassified",
    "residential", "living_street", "service",
    "motorway_link", "trunk_link", "primary_link", "secondary_link", "tertiary_link",
}

SCHEMA = """
CREATE TABLE ways (
    id INTEGER PRIMARY KEY,
    highway TEXT,
    ref TEXT,
    name TEXT,
    oneway INTEGER DEFAULT 0,
    junction TEXT,
    maxspeed TEXT,
    maxspeed_fwd TEXT,
    maxspeed_bwd TEXT
);
CREATE TABLE segs (
    id INTEGER PRIMARY KEY,
    way_id INTEGER NOT NULL,
    a_lat REAL NOT NULL, a_lon REAL NOT NULL,
    b_lat REAL NOT NULL, b_lon REAL NOT NULL
);
CREATE VIRTUAL TABLE segs_rt USING rtree(seg_id, minlat, maxlat, minlon, maxlon);
CREATE INDEX segs_way ON segs(way_id);
"""


def _first_name(value: str) -> str:
    """OSM usa "/" e ";" para varios nomes no mesmo campo; fica o primeiro."""
    if not value:
        return ""
    for sep in (";", "/"):
        if sep in value:
            value = value.split(sep)[0]
    return value.strip()


def build(pbf_paths, out_path, bbox=None, verbose=True):
    """Le os PBF e escreve a base. [bbox] = (minlat, minlon, maxlat, maxlon) opcional."""
    import osmium

    tmp = out_path + ".tmp"
    if os.path.exists(tmp):
        os.remove(tmp)
    db = sqlite3.connect(tmp)
    db.executescript(SCHEMA)
    db.execute("PRAGMA journal_mode=OFF")
    db.execute("PRAGMA synchronous=OFF")

    stats = {"ways": 0, "segs": 0, "skipped": 0}
    t0 = time.time()

    class Handler(osmium.SimpleHandler):
        def way(self, w):
            tags = w.tags
            highway = tags.get("highway", "")
            if highway not in DRIVABLE:
                return
            try:
                nodes = [(n.lat, n.lon) for n in w.nodes]
            except osmium.InvalidLocationError:
                stats["skipped"] += 1
                return
            if len(nodes) < 2:
                return
            if bbox:
                minlat, minlon, maxlat, maxlon = bbox
                if not any(minlat <= la <= maxlat and minlon <= lo <= maxlon for la, lo in nodes):
                    return

            db.execute(
                "INSERT OR REPLACE INTO ways"
                " (id, highway, ref, name, oneway, junction, maxspeed, maxspeed_fwd, maxspeed_bwd)"
                " VALUES (?,?,?,?,?,?,?,?,?)",
                (
                    w.id,
                    highway,
                    tags.get("ref", ""),
                    _first_name(tags.get("name", "")),
                    1 if tags.get("oneway") in ("yes", "true", "1", "-1") else 0,
                    tags.get("junction", ""),
                    tags.get("maxspeed", ""),
                    tags.get("maxspeed:forward", ""),
                    tags.get("maxspeed:backward", ""),
                ),
            )
            stats["ways"] += 1
            for (alat, alon), (blat, blon) in zip(nodes, nodes[1:]):
                cur = db.execute(
                    "INSERT INTO segs (way_id, a_lat, a_lon, b_lat, b_lon) VALUES (?,?,?,?,?)",
                    (w.id, alat, alon, blat, blon),
                )
                sid = cur.lastrowid
                db.execute(
                    "INSERT INTO segs_rt (seg_id, minlat, maxlat, minlon, maxlon) VALUES (?,?,?,?,?)",
                    (sid, min(alat, blat), max(alat, blat), min(alon, blon), max(alon, blon)),
                )
                stats["segs"] += 1

    for path in pbf_paths:
        if verbose:
            print("a ler", os.path.basename(path), "...", flush=True)
        handler = Handler()
        # with_locations(): os nos das vias trazem coordenadas (obrigatorio para os segmentos).
        handler.apply_file(path, locations=True)
        db.commit()
        if verbose:
            print("  -> %d vias, %d segmentos" % (stats["ways"], stats["segs"]), flush=True)

    db.commit()
    db.execute("ANALYZE")
    db.close()
    if os.path.exists(out_path):
        os.remove(out_path)
    os.replace(tmp, out_path)

    size_mb = os.path.getsize(out_path) / (1024 * 1024)
    if verbose:
        print("feito em %.1f s -> %s (%.1f MB)" % (time.time() - t0, out_path, size_mb))
        print("  vias: %d | segmentos: %d | ignoradas sem coordenadas: %d"
              % (stats["ways"], stats["segs"], stats["skipped"]))
    return stats


def main(argv=None):
    ap = argparse.ArgumentParser(description="Constroi o indice OSM local do Qolari.")
    ap.add_argument("--pbf", action="append", required=True, help="ficheiro .osm.pbf (repetivel)")
    ap.add_argument("--out", required=True, help="base SQLite a escrever")
    ap.add_argument("--bbox", help="minlat,minlon,maxlat,maxlon (opcional)")
    args = ap.parse_args(argv)

    missing = [p for p in args.pbf if not os.path.exists(p)]
    if missing:
        print("nao encontrei:", ", ".join(missing), file=sys.stderr)
        return 2

    bbox = None
    if args.bbox:
        bbox = tuple(float(x) for x in args.bbox.split(","))
        if len(bbox) != 4:
            print("--bbox precisa de 4 valores", file=sys.stderr)
            return 2

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    build(args.pbf, args.out, bbox)
    return 0


if __name__ == "__main__":
    sys.exit(main())
