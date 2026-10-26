# -*- coding: utf-8 -*-
"""Backup SQLite (online backup)."""
import sqlite3

from tools.backup import backup_sqlite, prune


def test_sqlite_backup_keeps_rows(tmp_path):
    source = tmp_path / "source.db"
    con = sqlite3.connect(source)
    con.execute("create table t (id integer primary key, name text)")
    con.execute("insert into t (name) values ('Ana')")
    con.commit()
    con.close()

    out = backup_sqlite(source, tmp_path / "dest", stamp="20260101-000000")
    assert out.exists()
    copy = sqlite3.connect(out)
    assert copy.execute("select name from t").fetchone()[0] == "Ana"
    copy.close()


def test_prune_keeps_newest(tmp_path):
    for i in range(3):
        (tmp_path / f"qolari-{i}.db").write_bytes(b"x")
    removed = prune(tmp_path, 1)
    assert len(removed) == 2
    assert len(list(tmp_path.glob("qolari-*"))) == 1
