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
