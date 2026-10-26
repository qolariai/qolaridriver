"""baseline — cria o esquema do laboratorio

Revision ID: 0001_baseline
Revises:
Create Date: 2026-10-25
"""
from alembic import op

import domain.models  # noqa: F401
from core.db import Base

revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Baseline: o esquema atual e criado pelo metadata. As proximas revisoes devem ser
    # geradas com `alembic revision --autogenerate` e revistas a mao.
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    # Nao apagar tabelas por omissao: produção exige backup e revisão manual.
    pass
