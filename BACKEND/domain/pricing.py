# -*- coding: utf-8 -*-
"""Tarifas: estimativa (antes de pedir) e tarifa final (no fim da viagem). Tudo em centimos.

    tarifa = max(minimo, base + km*por_km + min*por_min) * surge + taxa_reserva - desconto
"""
from dataclasses import dataclass, asdict

from domain import geo, settings
from domain.models import Product, Promo, now


@dataclass
class Quote:
    distance_m: int
    duration_s: int
    base: int
    distance: int
    time: int
    minimum_applied: bool
    surge: float
    surge_amount: int
    booking_fee: int
    subtotal: int        # antes do desconto
    discount: int
    total: int

    def as_dict(self):
        return asdict(self)


def compute(product: Product, distance_m: int, duration_s: int, discount_of=None) -> Quote:
    km, minutes = distance_m / 1000, duration_s / 60
    dist_part = round(km * product.per_km)
    time_part = round(minutes * product.per_min)
    metered = product.base_fare + dist_part + time_part
    minimum_applied = metered < product.minimum_fare
    fare = max(metered, product.minimum_fare)
    surged = round(fare * product.surge)
    subtotal = surged + product.booking_fee
    discount = min(discount_of(subtotal), subtotal) if discount_of else 0
    return Quote(distance_m, duration_s, product.base_fare, dist_part, time_part, minimum_applied,
                 product.surge, surged - fare, product.booking_fee, subtotal, discount,
                 subtotal - discount)


def estimate(db, product: Product, plat, plng, dlat, dlng, promo: Promo | None = None) -> Quote:
    if dlat is None or dlng is None:
        dist, dur = 0, 0
    else:
        dist, dur = geo.road_estimate(plat, plng, dlat, dlng, settings.get(db, "road_factor"),
                                      settings.get(db, "avg_speed_kmh"))
    return compute(product, dist, dur, promo_discount(promo) if promo else None)


def promo_discount(promo: Promo):
    def fn(subtotal: int) -> int:
        if promo.kind == "percent":
            d = round(subtotal * promo.value / 100)
        else:
            d = promo.value
        if promo.max_discount:
            d = min(d, promo.max_discount)
        return max(d, 0)
    return fn


def promo_valid(promo: Promo | None, product_id: int | None = None) -> str | None:
    """-> None se valido; senao o motivo."""
    if not promo or not promo.active:
        return "codigo inexistente ou inativo"
    t = now()
    if promo.valid_from and t < promo.valid_from:
        return "codigo ainda nao esta ativo"
    if promo.valid_to and t >= promo.valid_to:
        return "codigo expirado"
    if promo.max_uses is not None and promo.uses >= promo.max_uses:
        return "codigo esgotado"
    if promo.product_id and product_id and promo.product_id != product_id:
        return "codigo nao se aplica a esta categoria"
    return None
