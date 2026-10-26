# -*- coding: utf-8 -*-
"""Backup da base de dados (SQLite ou PostgreSQL).

    python tools/backup.py --dest ../BACKUPS/db --keep 14

SQLite usa a API de backup online (funciona com o servidor a correr). PostgreSQL usa
`pg_dump` (tem de estar no PATH). O ficheiro leva timestamp UTC; os antigos sao podados.
"""
import argparse
import gzip
import sqlite3
import subprocess
import time
from pathlib import Path

import config


def _stamp() -> str:
    return time.strftime("%Y%m%d-%H%M%S", time.gmtime())


def backup_sqlite(source: Path, dest_dir: Path, stamp: str | None = None) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    out = dest_dir / f"qolari-{stamp or _stamp()}.db"
    src = sqlite3.connect(str(source))
    try:
        dst = sqlite3.connect(str(out))
        try:
            src.backup(dst)
        finally:
            dst.close()
    finally:
        src.close()
    return out


def backup_postgres(url: str, dest_dir: Path, stamp: str | None = None) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    out = dest_dir / f"qolari-{stamp or _stamp()}.sql.gz"
    clean = url.replace("postgresql+psycopg://", "postgresql://").replace("postgresql+psycopg2://", "postgresql://")
    with gzip.open(out, "wb") as fh:
        proc = subprocess.run(["pg_dump", "--no-owner", "--no-acl", clean], stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE)
        if proc.returncode != 0:
            out.unlink(missing_ok=True)
            raise RuntimeError(proc.stderr.decode("utf-8", "replace").strip() or "pg_dump falhou")
        fh.write(proc.stdout)
    return out


def prune(dest_dir: Path, keep: int) -> list[Path]:
    files = sorted(dest_dir.glob("qolari-*"), key=lambda p: p.stat().st_mtime, reverse=True)
    removed = files[max(0, keep):]
    for p in removed:
        p.unlink(missing_ok=True)
    return removed


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", default=str(config.BASE_DIR.parent / "BACKUPS" / "db"))
    ap.add_argument("--keep", type=int, default=14)
    args = ap.parse_args()
    dest = Path(args.dest)
    if config.DB_URL.startswith("sqlite"):
        source = Path(config.DB_URL.split("sqlite:///", 1)[1])
        out = backup_sqlite(source, dest)
    else:
        out = backup_postgres(config.DB_URL, dest)
    removed = prune(dest, args.keep)
    print(f"backup: {out}")
    if removed:
        print(f"podados: {len(removed)}")


if __name__ == "__main__":
    main()
