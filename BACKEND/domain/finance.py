# -*- coding: utf-8 -*-
"""Saldos e pagamentos. Saldo = soma do ledger da parte (positivo = a plataforma deve-lhe)."""
from sqlalchemy import func

from core.db import touch
from domain.models import Driver, LedgerEntry, Organization, Payout, now


class FinanceError(Exception):
    pass


def balance(db, party: str, party_id: int) -> int:
    return int(db.query(func.coalesce(func.sum(LedgerEntry.amount), 0))
               .filter(LedgerEntry.party == party, LedgerEntry.party_id == party_id).scalar())


def balances(db, party: str) -> dict[int, int]:
    rows = (db.query(LedgerEntry.party_id, func.sum(LedgerEntry.amount))
            .filter(LedgerEntry.party == party).group_by(LedgerEntry.party_id).all())
    return {pid: int(total) for pid, total in rows if pid is not None}


def summary(db, party: str, party_id: int, since: int | None = None, until: int | None = None) -> dict:
    """Totais por tipo de movimento no periodo (para extratos)."""
    q = db.query(LedgerEntry.kind, func.sum(LedgerEntry.amount)).filter(
        LedgerEntry.party == party, LedgerEntry.party_id == party_id)
    if since:
        q = q.filter(LedgerEntry.at >= since)
    if until:
        q = q.filter(LedgerEntry.at < until)
    by_kind = {k: int(v) for k, v in q.group_by(LedgerEntry.kind).all()}
    return {"by_kind": by_kind, "total": sum(by_kind.values())}


def create_payout(db, party: str, party_id: int, amount: int | None = None, reference: str = "") -> Payout:
    if party == "driver" and not db.get(Driver, party_id):
        raise FinanceError("motorista inexistente")
    if party == "fleet" and not db.get(Organization, party_id):
        raise FinanceError("frota inexistente")
    bal = balance(db, party, party_id)
    amount = bal if amount is None else amount
    if amount <= 0:
        raise FinanceError("sem saldo a pagar")
    if amount > bal:
        raise FinanceError("valor acima do saldo")
    payout = Payout(party=party, party_id=party_id, amount=amount, reference=reference)
    db.add(payout)
    db.flush()
    db.add(LedgerEntry(party=party, party_id=party_id, kind="payout", amount=-amount,
                       payout_id=payout.id, note=f"pagamento #{payout.id}"))
    touch(db, "finance")
    return payout


def mark_paid(db, payout: Payout, reference: str = "") -> Payout:
    if payout.status != "pending":
        raise FinanceError("pagamento ja fechado")
    payout.status, payout.paid_at = "paid", now()
    if reference:
        payout.reference = reference
    touch(db, "finance")
    return payout


def cancel_payout(db, payout: Payout) -> Payout:
    if payout.status != "pending":
        raise FinanceError("so pagamentos pendentes")
    payout.status = "cancelled"
    db.query(LedgerEntry).filter(LedgerEntry.payout_id == payout.id).delete()
    touch(db, "finance")
    return payout


def adjust(db, party: str, party_id: int, amount: int, note: str) -> LedgerEntry:
    if not amount:
        raise FinanceError("valor zero")
    e = LedgerEntry(party=party, party_id=party_id, kind="adjustment", amount=amount, note=note[:200])
    db.add(e)
    touch(db, "finance")
    return e
