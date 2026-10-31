# -*- coding: utf-8 -*-
"""Modelo de dados da plataforma de mobilidade.

Pessoas por app:   Rider (app Rider)  |  Driver (app Driver)  |  FleetUser (app Fleet)
Oferta:            City -> Product (categoria + tarifa)  |  Organization (frota) -> Vehicle, Driver
Procura:           Trip (maquina de estados em domain/trips.py) -> Offer (despacho) -> TripEvent
Dinheiro:          LedgerEntry (movimentos por parte) -> Payout (pagamentos a motoristas/frotas)
Apps:              AuthSession (tokens), LoginAttempt (login /v2), Device, PushMessage (ramen)

Dinheiro sempre em centimos (int). Datas em epoch segundos (int) - o que as apps Uber usam
(timestamps em s ou ms conforme o campo) converte-se nos adaptadores das apps.
Todas as entidades expostas as apps tem `uuid` (as apps identificam tudo por UUID).
"""
import json, time, uuid as _uuid

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.db import Base


def now() -> int:
    return int(time.time())


def new_uuid() -> str:
    return str(_uuid.uuid4())


def jget(raw, default=None):
    if not raw:
        return default
    try:
        return json.loads(raw)
    except ValueError:
        return default


def jset(value) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


# ---- consola ---------------------------------------------------------------------------------
class AdminUser(Base):
    __tablename__ = "admin_users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(120), unique=True)
    name: Mapped[str] = mapped_column(String(120), default="")
    password_hash: Mapped[str] = mapped_column(String(200))
    role: Mapped[str] = mapped_column(String(20), default="admin")   # admin | operator | finance
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[int] = mapped_column(Integer, default=now)
    last_login_at: Mapped[int | None] = mapped_column(Integer, nullable=True)


class Setting(Base):
    __tablename__ = "settings"
    key: Mapped[str] = mapped_column(String(60), primary_key=True)
    value: Mapped[str] = mapped_column(Text)   # JSON


class AuditLog(Base):
    """Quem mudou o que na consola."""
    __tablename__ = "audit_log"
    id: Mapped[int] = mapped_column(primary_key=True)
    at: Mapped[int] = mapped_column(Integer, default=now, index=True)
    admin_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    admin_email: Mapped[str] = mapped_column(String(120), default="")
    action: Mapped[str] = mapped_column(String(60))
    entity: Mapped[str] = mapped_column(String(40), default="")
    entity_id: Mapped[str] = mapped_column(String(60), default="")
    detail: Mapped[str] = mapped_column(Text, default="")


# ---- oferta ----------------------------------------------------------------------------------
class City(Base):
    __tablename__ = "cities"
    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[str] = mapped_column(String(36), unique=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(80))
    country_iso2: Mapped[str] = mapped_column(String(2), default="PT")
    currency: Mapped[str] = mapped_column(String(3), default="EUR")
    timezone: Mapped[str] = mapped_column(String(40), default="Europe/Lisbon")
    center_lat: Mapped[float] = mapped_column(Float)
    center_lng: Mapped[float] = mapped_column(Float)
    radius_km: Mapped[float] = mapped_column(Float, default=25)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    products: Mapped[list["Product"]] = relationship(back_populates="city", order_by="Product.sort_order")


class Product(Base):
    """Categoria de viagem (Qolari X, Comfort, XL...) com a sua tarifa, por cidade."""
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[str] = mapped_column(String(36), unique=True, default=new_uuid)
    city_id: Mapped[int] = mapped_column(ForeignKey("cities.id"))
    code: Mapped[str] = mapped_column(String(40))
    name: Mapped[str] = mapped_column(String(60))
    description: Mapped[str] = mapped_column(String(200), default="")
    capacity: Mapped[int] = mapped_column(Integer, default=4)
    base_fare: Mapped[int] = mapped_column(Integer, default=100)      # centimos
    per_km: Mapped[int] = mapped_column(Integer, default=60)
    per_min: Mapped[int] = mapped_column(Integer, default=12)
    minimum_fare: Mapped[int] = mapped_column(Integer, default=350)
    booking_fee: Mapped[int] = mapped_column(Integer, default=50)
    cancel_fee: Mapped[int] = mapped_column(Integer, default=300)
    surge: Mapped[float] = mapped_column(Float, default=1.0)
    min_vehicle_year: Mapped[int] = mapped_column(Integer, default=2010)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    city: Mapped[City] = relationship(back_populates="products")


class Organization(Base):
    """Parceiro de frota (app Fleet): tem motoristas e veiculos e fica com uma % dos ganhos."""
    __tablename__ = "organizations"
    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[str] = mapped_column(String(36), unique=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(120))
    tax_id: Mapped[str] = mapped_column(String(30), default="")
    email: Mapped[str] = mapped_column(String(120), default="")
    phone: Mapped[str] = mapped_column(String(30), default="")
    city_id: Mapped[int | None] = mapped_column(ForeignKey("cities.id"), nullable=True)
    fleet_fee_pct: Mapped[float] = mapped_column(Float, default=10.0)   # % do ganho do motorista
    iban: Mapped[str] = mapped_column(String(40), default="")
    status: Mapped[str] = mapped_column(String(20), default="active")  # active | suspended
    created_at: Mapped[int] = mapped_column(Integer, default=now)

    drivers: Mapped[list["Driver"]] = relationship(back_populates="organization")
    vehicles: Mapped[list["Vehicle"]] = relationship(back_populates="organization")
    users: Mapped[list["FleetUser"]] = relationship(back_populates="organization")


class FleetUser(Base):
    """Quem entra na app Fleet (dono/gestor de uma frota)."""
    __tablename__ = "fleet_users"
    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[str] = mapped_column(String(36), unique=True, default=new_uuid)
    org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"))
    first_name: Mapped[str] = mapped_column(String(60))
    last_name: Mapped[str] = mapped_column(String(60), default="")
    phone: Mapped[str] = mapped_column(String(30), unique=True)
    email: Mapped[str] = mapped_column(String(120), default="")
    role: Mapped[str] = mapped_column(String(20), default="owner")   # owner | manager
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[int] = mapped_column(Integer, default=now)
    last_seen_at: Mapped[int | None] = mapped_column(Integer, nullable=True)

    organization: Mapped[Organization] = relationship(back_populates="users")


class Driver(Base):
    __tablename__ = "drivers"
    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[str] = mapped_column(String(36), unique=True, default=new_uuid)
    org_id: Mapped[int | None] = mapped_column(ForeignKey("organizations.id"), nullable=True)
    city_id: Mapped[int | None] = mapped_column(ForeignKey("cities.id"), nullable=True)
    first_name: Mapped[str] = mapped_column(String(60))
    last_name: Mapped[str] = mapped_column(String(60), default="")
    phone: Mapped[str] = mapped_column(String(30), unique=True)
    email: Mapped[str] = mapped_column(String(120), default="")
    license_number: Mapped[str] = mapped_column(String(40), default="")
    # pending (registo) -> approved | rejected ; approved <-> suspended
    status: Mapped[str] = mapped_column(String(20), default="pending")
    # offline | online | on_trip  (on_trip = tem viagem aceite/em curso)
    availability: Mapped[str] = mapped_column(String(20), default="offline")
    # True = "Parar novos pedidos": continua online (sessao aberta, horas online contam) mas
    # o despacho nao lhe manda propostas ate retomar. Nao muda `availability` para nao perder
    # a sessao nem o estado da viagem em curso.
    paused: Mapped[bool] = mapped_column(Boolean, default=False)
    vehicle_id: Mapped[int | None] = mapped_column(ForeignKey("vehicles.id", use_alter=True), nullable=True)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    heading: Mapped[float] = mapped_column(Float, default=0)
    location_at: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rating_sum: Mapped[int] = mapped_column(Integer, default=0)
    rating_count: Mapped[int] = mapped_column(Integer, default=0)
    offers_received: Mapped[int] = mapped_column(Integer, default=0)
    offers_accepted: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[int] = mapped_column(Integer, default=now)
    last_seen_at: Mapped[int | None] = mapped_column(Integer, nullable=True)
    online_since: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # True = motorista simulado (a consola move-o no mapa); a 1.a localizacao vinda da app -> False
    simulated: Mapped[bool] = mapped_column(Boolean, default=False)

    organization: Mapped[Organization | None] = relationship(back_populates="drivers")
    vehicle: Mapped["Vehicle | None"] = relationship(foreign_keys=[vehicle_id])

    @property
    def name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def rating(self) -> float:
        return round(self.rating_sum / self.rating_count, 2) if self.rating_count else 5.0


class Vehicle(Base):
    __tablename__ = "vehicles"
    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[str] = mapped_column(String(36), unique=True, default=new_uuid)
    org_id: Mapped[int | None] = mapped_column(ForeignKey("organizations.id"), nullable=True)
    owner_driver_id: Mapped[int | None] = mapped_column(ForeignKey("drivers.id"), nullable=True)
    make: Mapped[str] = mapped_column(String(40))
    model: Mapped[str] = mapped_column(String(40))
    year: Mapped[int] = mapped_column(Integer, default=2020)
    color: Mapped[str] = mapped_column(String(30), default="")
    color_hex: Mapped[str] = mapped_column(String(7), default="#222222")
    plate: Mapped[str] = mapped_column(String(15), unique=True)
    vin: Mapped[str] = mapped_column(String(20), default="")
    seats: Mapped[int] = mapped_column(Integer, default=4)
    products: Mapped[str] = mapped_column(Text, default="[]")   # JSON: ids de Product permitidos
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending | active | inactive
    created_at: Mapped[int] = mapped_column(Integer, default=now)

    organization: Mapped[Organization | None] = relationship(back_populates="vehicles")

    @property
    def product_ids(self) -> list[int]:
        return jget(self.products, [])

    @property
    def label(self) -> str:
        return f"{self.make} {self.model} · {self.plate}"


class Rider(Base):
    __tablename__ = "riders"
    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[str] = mapped_column(String(36), unique=True, default=new_uuid)
    first_name: Mapped[str] = mapped_column(String(60), default="")
    last_name: Mapped[str] = mapped_column(String(60), default="")
    phone: Mapped[str] = mapped_column(String(30), unique=True)
    email: Mapped[str] = mapped_column(String(120), default="")
    status: Mapped[str] = mapped_column(String(20), default="active")   # active | blocked
    rating_sum: Mapped[int] = mapped_column(Integer, default=0)
    rating_count: Mapped[int] = mapped_column(Integer, default=0)
    default_payment: Mapped[str] = mapped_column(String(10), default="cash")   # cash | card
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[int] = mapped_column(Integer, default=now)
    last_seen_at: Mapped[int | None] = mapped_column(Integer, nullable=True)

    @property
    def name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip() or self.phone

    @property
    def rating(self) -> float:
        return round(self.rating_sum / self.rating_count, 2) if self.rating_count else 5.0


class Document(Base):
    """Documento de um motorista (carta, CC, registo criminal...) ou de um veiculo (DUA, seguro...)."""
    __tablename__ = "documents"
    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[str] = mapped_column(String(36), unique=True, default=new_uuid)
    owner_type: Mapped[str] = mapped_column(String(10))    # driver | vehicle
    owner_id: Mapped[int] = mapped_column(Integer, index=True)
    kind: Mapped[str] = mapped_column(String(40))
    number: Mapped[str] = mapped_column(String(60), default="")
    expires_on: Mapped[str | None] = mapped_column(String(10), nullable=True)   # AAAA-MM-DD
    status: Mapped[str] = mapped_column(String(20), default="pending")   # pending|approved|rejected
    file_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    notes: Mapped[str] = mapped_column(String(300), default="")
    reviewed_by: Mapped[str] = mapped_column(String(120), default="")
    reviewed_at: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[int] = mapped_column(Integer, default=now)


class Promo(Base):
    __tablename__ = "promos"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(30), unique=True)
    description: Mapped[str] = mapped_column(String(200), default="")
    kind: Mapped[str] = mapped_column(String(10), default="percent")   # percent | amount
    value: Mapped[int] = mapped_column(Integer)                         # % ou centimos
    max_discount: Mapped[int | None] = mapped_column(Integer, nullable=True)   # centimos
    max_uses: Mapped[int | None] = mapped_column(Integer, nullable=True)
    per_rider: Mapped[int] = mapped_column(Integer, default=1)
    uses: Mapped[int] = mapped_column(Integer, default=0)
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"), nullable=True)
    valid_from: Mapped[int | None] = mapped_column(Integer, nullable=True)
    valid_to: Mapped[int | None] = mapped_column(Integer, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[int] = mapped_column(Integer, default=now)


class RiderPromo(Base):
    """Codigo aplicado na conta do passageiro (usa-se na proxima viagem)."""
    __tablename__ = "rider_promos"
    id: Mapped[int] = mapped_column(primary_key=True)
    rider_id: Mapped[int] = mapped_column(ForeignKey("riders.id"), index=True)
    promo_id: Mapped[int] = mapped_column(ForeignKey("promos.id"))
    used_trip_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[int] = mapped_column(Integer, default=now)

    promo: Mapped[Promo] = relationship()


# ---- procura ---------------------------------------------------------------------------------
TRIP_ACTIVE = ("requested", "accepted", "arrived", "in_progress")
TRIP_FINAL = ("completed", "cancelled", "no_drivers")


class Trip(Base):
    __tablename__ = "trips"
    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[str] = mapped_column(String(36), unique=True, default=new_uuid)
    city_id: Mapped[int] = mapped_column(ForeignKey("cities.id"))
    rider_id: Mapped[int] = mapped_column(ForeignKey("riders.id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    driver_id: Mapped[int | None] = mapped_column(ForeignKey("drivers.id"), nullable=True, index=True)
    vehicle_id: Mapped[int | None] = mapped_column(ForeignKey("vehicles.id"), nullable=True)
    org_id: Mapped[int | None] = mapped_column(ForeignKey("organizations.id"), nullable=True, index=True)
    # requested -> accepted -> arrived -> in_progress -> completed ; cancelled ; no_drivers
    state: Mapped[str] = mapped_column(String(20), default="requested", index=True)
    pickup_lat: Mapped[float] = mapped_column(Float)
    pickup_lng: Mapped[float] = mapped_column(Float)
    pickup_address: Mapped[str] = mapped_column(String(200), default="")
    dropoff_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    dropoff_lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    dropoff_address: Mapped[str] = mapped_column(String(200), default="")
    est_distance_m: Mapped[int] = mapped_column(Integer, default=0)
    est_duration_s: Mapped[int] = mapped_column(Integer, default=0)
    est_fare: Mapped[int] = mapped_column(Integer, default=0)
    surge: Mapped[float] = mapped_column(Float, default=1.0)
    distance_m: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_s: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fare: Mapped[int | None] = mapped_column(Integer, nullable=True)        # final, ja com desconto
    discount: Mapped[int] = mapped_column(Integer, default=0)
    fare_breakdown: Mapped[str] = mapped_column(Text, default="{}")        # JSON
    promo_id: Mapped[int | None] = mapped_column(ForeignKey("promos.id"), nullable=True)
    payment_method: Mapped[str] = mapped_column(String(10), default="cash")
    pin: Mapped[str] = mapped_column(String(4), default="")
    cancelled_by: Mapped[str] = mapped_column(String(10), default="")    # rider|driver|admin|system
    cancel_reason: Mapped[str] = mapped_column(String(200), default="")
    rider_to_driver_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    driver_to_rider_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rider_comment: Mapped[str] = mapped_column(String(300), default="")
    requested_at: Mapped[int] = mapped_column(Integer, default=now, index=True)
    accepted_at: Mapped[int | None] = mapped_column(Integer, nullable=True)
    arrived_at: Mapped[int | None] = mapped_column(Integer, nullable=True)
    started_at: Mapped[int | None] = mapped_column(Integer, nullable=True)
    completed_at: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cancelled_at: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source: Mapped[str] = mapped_column(String(10), default="rider")   # rider | console

    rider: Mapped[Rider] = relationship()
    driver: Mapped[Driver | None] = relationship()
    vehicle: Mapped[Vehicle | None] = relationship()
    product: Mapped[Product] = relationship()
    city: Mapped[City] = relationship()
    events: Mapped[list["TripEvent"]] = relationship(order_by="TripEvent.id", cascade="all, delete-orphan")
    offers: Mapped[list["Offer"]] = relationship(order_by="Offer.id", cascade="all, delete-orphan",
                                                 back_populates="trip")

    @property
    def is_active(self) -> bool:
        return self.state in TRIP_ACTIVE


class TripEvent(Base):
    __tablename__ = "trip_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    trip_id: Mapped[int] = mapped_column(ForeignKey("trips.id"), index=True)
    at: Mapped[int] = mapped_column(Integer, default=now)
    kind: Mapped[str] = mapped_column(String(30))
    actor: Mapped[str] = mapped_column(String(10), default="system")
    detail: Mapped[str] = mapped_column(String(300), default="")


class Offer(Base):
    """Proposta de uma viagem a um motorista (despacho). Uma pendente de cada vez por viagem.

    `kind` separa os dois tipos de pedido da Uber Driver:
      - `exclusive`: viagem exclusiva (so este motorista a recebe; recusar conta para a taxa de aceitacao);
      - `radar`: Radar de viagens (varios motoristas ao mesmo tempo; quem toca entra no emparelhamento
        e so um fica com a viagem; ignorar NAO conta para a taxa de aceitacao).
    `claimed_at` marca quem tocou no Radar; `offered_at` quando a proposta foi entregue.
    """
    __tablename__ = "offers"
    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[str] = mapped_column(String(36), unique=True, default=new_uuid)
    trip_id: Mapped[int] = mapped_column(ForeignKey("trips.id"), index=True)
    driver_id: Mapped[int] = mapped_column(ForeignKey("drivers.id"), index=True)
    state: Mapped[str] = mapped_column(String(12), default="pending")
    # exclusive|radar
    kind: Mapped[str] = mapped_column(String(10), default="exclusive")
    # no Radar: true depois de o motorista tocar (entrou no emparelhamento)
    claimed_at: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pickup_distance_m: Mapped[int] = mapped_column(Integer, default=0)
    pickup_eta_s: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[int] = mapped_column(Integer, default=now)
    expires_at: Mapped[int] = mapped_column(Integer)
    responded_at: Mapped[int | None] = mapped_column(Integer, nullable=True)

    driver: Mapped[Driver] = relationship()
    trip: Mapped[Trip] = relationship(back_populates="offers")


# ---- dinheiro --------------------------------------------------------------------------------
class LedgerEntry(Base):
    """Movimento na conta de uma parte. Saldo de motorista/frota = soma (positivo = a plataforma deve)."""
    __tablename__ = "ledger"
    id: Mapped[int] = mapped_column(primary_key=True)
    at: Mapped[int] = mapped_column(Integer, default=now, index=True)
    party: Mapped[str] = mapped_column(String(10))   # platform | driver | fleet | rider
    party_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    # fare (ganho bruto) | commission | fleet_fee | cash_collected | cancel_fee | promo | payout | adjustment
    kind: Mapped[str] = mapped_column(String(20))
    amount: Mapped[int] = mapped_column(Integer)
    trip_id: Mapped[int | None] = mapped_column(ForeignKey("trips.id"), nullable=True, index=True)
    payout_id: Mapped[int | None] = mapped_column(ForeignKey("payouts.id"), nullable=True)
    note: Mapped[str] = mapped_column(String(200), default="")


class Payout(Base):
    __tablename__ = "payouts"
    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[str] = mapped_column(String(36), unique=True, default=new_uuid)
    party: Mapped[str] = mapped_column(String(10))       # driver | fleet
    party_id: Mapped[int] = mapped_column(Integer, index=True)
    amount: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(10), default="pending")   # pending | paid | cancelled
    reference: Mapped[str] = mapped_column(String(60), default="")
    created_at: Mapped[int] = mapped_column(Integer, default=now)
    paid_at: Mapped[int | None] = mapped_column(Integer, nullable=True)


# ---- ligacao das apps ------------------------------------------------------------------------
class AuthSession(Base):
    """Sessao de uma app (o token leva o id). Revogar na consola = logout no telemovel."""
    __tablename__ = "auth_sessions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    app: Mapped[str] = mapped_column(String(10))           # rider | driver | fleet
    subject_uuid: Mapped[str] = mapped_column(String(36), index=True)
    created_at: Mapped[int] = mapped_column(Integer, default=now)
    last_used_at: Mapped[int] = mapped_column(Integer, default=now)
    user_agent: Mapped[str] = mapped_column(String(200), default="")
    ip: Mapped[str] = mapped_column(String(45), default="")
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)


class LoginAttempt(Base):
    """Login concluido na pagina do dominio auth (/v2) a espera de ser confirmado pela app.

    A pagina redireciona para `app_url?session=<id>&authCode=<auth_code>`; a app confirma com
    POST /rt/silk-screen/submit-form (ecra TypeVerifySession) e o code_verifier PKCE do `codeChallenge`."""
    __tablename__ = "login_attempts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    app: Mapped[str] = mapped_column(String(10))
    subject_uuid: Mapped[str] = mapped_column(String(36))
    auth_code: Mapped[str] = mapped_column(String(64), index=True)
    code_challenge: Mapped[str] = mapped_column(String(128), default="")
    is_signup: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[int] = mapped_column(Integer, default=now)
    used: Mapped[bool] = mapped_column(Boolean, default=False)


class Device(Base):
    __tablename__ = "devices"
    id: Mapped[int] = mapped_column(primary_key=True)
    app: Mapped[str] = mapped_column(String(10))
    device_key: Mapped[str] = mapped_column(String(120), index=True)   # id que a app envia
    subject_uuid: Mapped[str | None] = mapped_column(String(36), nullable=True)
    model: Mapped[str] = mapped_column(String(120), default="")
    os_version: Mapped[str] = mapped_column(String(40), default="")
    app_version: Mapped[str] = mapped_column(String(40), default="")
    push_token: Mapped[str] = mapped_column(String(300), default="")
    ip: Mapped[str] = mapped_column(String(45), default="")
    first_seen_at: Mapped[int] = mapped_column(Integer, default=now)
    last_seen_at: Mapped[int] = mapped_column(Integer, default=now)


class PushMessage(Base):
    """Fila de mensagens por utilizador (canal 'ramen' das apps: propostas, estado da viagem)."""
    __tablename__ = "push_messages"
    id: Mapped[int] = mapped_column(primary_key=True)
    app: Mapped[str] = mapped_column(String(10))
    subject_uuid: Mapped[str] = mapped_column(String(36), index=True)
    topic: Mapped[str] = mapped_column(String(60))
    payload: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[int] = mapped_column(Integer, default=now)
    delivered_at: Mapped[int | None] = mapped_column(Integer, nullable=True)


class EndpointStat(Base):
    """Uso real de cada endpoint pelas apps (para a pagina 'Integracao' da consola)."""
    __tablename__ = "endpoint_stats"
    id: Mapped[int] = mapped_column(primary_key=True)
    app: Mapped[str] = mapped_column(String(10))
    method: Mapped[str] = mapped_column(String(8))
    path: Mapped[str] = mapped_column(String(300))       # template (/rt/riders/{riderUUID}/status)
    handler: Mapped[str] = mapped_column(String(80), default="")   # "" = sem handler (resposta generica)
    calls: Mapped[int] = mapped_column(Integer, default=0)
    errors: Mapped[int] = mapped_column(Integer, default=0)
    last_status: Mapped[int] = mapped_column(Integer, default=0)
    first_at: Mapped[int] = mapped_column(Integer, default=now)
    last_at: Mapped[int] = mapped_column(Integer, default=now)
    last_request: Mapped[str] = mapped_column(Text, default="")
    last_response: Mapped[str] = mapped_column(Text, default="")


class DriverSession(Base):
    """Periodo em que o motorista esteve online (para as horas online de Rendimentos). ended_at vazio = aberta."""
    __tablename__ = "driver_sessions"
    id: Mapped[int] = mapped_column(primary_key=True)
    driver_id: Mapped[int] = mapped_column(ForeignKey("drivers.id"), index=True)
    started_at: Mapped[int] = mapped_column(Integer, default=now, index=True)
    ended_at: Mapped[int | None] = mapped_column(Integer, nullable=True)


class Notification(Base):
    """Notificacao da Caixa de entrada de um motorista."""
    __tablename__ = "notifications"
    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[str] = mapped_column(String(36), unique=True, default=new_uuid)
    owner_type: Mapped[str] = mapped_column(String(10), default="driver")
    owner_id: Mapped[int] = mapped_column(Integer, index=True)
    title: Mapped[str] = mapped_column(String(160))
    body: Mapped[str] = mapped_column(String(400), default="")
    created_at: Mapped[int] = mapped_column(Integer, default=now, index=True)
    read: Mapped[bool] = mapped_column(Boolean, default=False)
