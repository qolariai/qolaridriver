# -*- coding: utf-8 -*-
"""Alembic baseline cria o esquema num SQLite vazio."""
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_alembic_baseline_creates_schema(tmp_path):
    db = tmp_path / "mig.db"
    env = {**os.environ, "DB_URL": f"sqlite:///{db.as_posix()}"}
    r = subprocess.run([sys.executable, "-m", "alembic", "-c", "alembic.ini", "upgrade", "head"],
                       cwd=ROOT, env=env, capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    con = sqlite3.connect(db)
    tables = {x[0] for x in con.execute("select name from sqlite_master where type='table'")}
    version = con.execute("select version_num from alembic_version").fetchone()[0]
    con.close()
    assert "trips" in tables and "map_reports" in tables
    assert version == "0001_baseline"
