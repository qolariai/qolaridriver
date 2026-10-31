# -*- coding: utf-8 -*-
"""Motor SQLAlchemy (SQLite em data/qolari.db; DB_URL=mysql+pymysql://... para o MySQL do XAMPP)."""
from contextlib import contextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

import config
from core import events


class Base(DeclarativeBase):
    pass


_sqlite = config.DB_URL.startswith("sqlite")
if _sqlite:
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)

engine = create_engine(config.DB_URL,
                       connect_args={"check_same_thread": False, "timeout": 15} if _sqlite else {})

if _sqlite:
    @event.listens_for(engine, "connect")
    def _pragmas(conn, _):
        cur = conn.cursor()
        cur.execute("PRAGMA journal_mode=WAL")
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()

Session = sessionmaker(bind=engine, expire_on_commit=False)


def init_db():
    from domain import models  # noqa: F401  regista as tabelas
    Base.metadata.create_all(engine)
    _migrate()


def _migrate():
    """Colunas novas em tabelas ja existentes (create_all nao altera tabelas).

    Mantem-se simples de proposito: so ADD COLUMN com valor por omissao.
    """
    wanted = {
        "offers": [
            ("kind", "VARCHAR(10) DEFAULT 'exclusive'"),
            ("claimed_at", "INTEGER"),
        ],
        "drivers": [
            # "Parar novos pedidos" (botao do planeador): online mas fora do despacho.
            ("paused", "BOOLEAN DEFAULT 0"),
            # Modo Destino (lupa do mapa): destino marcado + filtros usados hoje.
            ("dest_lat", "FLOAT"),
            ("dest_lng", "FLOAT"),
            ("dest_label", "VARCHAR(160) DEFAULT ''"),
            ("dest_used_today", "INTEGER DEFAULT 0"),
            ("dest_used_day", "INTEGER DEFAULT 0"),
        ],
    }
    with engine.begin() as conn:
        for table, columns in wanted.items():
            rows = conn.exec_driver_sql(f"PRAGMA table_info({table})").fetchall()
            if not rows:
                continue
            have = {r[1] for r in rows}
            for name, decl in columns:
                if name not in have:
                    conn.exec_driver_sql(f"ALTER TABLE {table} ADD COLUMN {name} {decl}")


def touch(db, *topics: str):
    """Marca a sessao: depois do commit acorda os long-pollings (consola e apps)."""
    db.info.setdefault("topics", set()).update(topics or ("all",))


@event.listens_for(Session, "after_commit")
def _after_commit(session):
    topics = session.info.pop("topics", None)
    if topics:
        events.publish(topics)


@event.listens_for(Session, "after_rollback")
def _after_rollback(session):
    session.info.pop("topics", None)


@contextmanager
def session_scope():
    db = Session()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
