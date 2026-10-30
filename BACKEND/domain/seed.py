# -*- coding: utf-8 -*-
"""Dados iniciais (so com a BD vazia): Lisboa, 4 categorias, 2 frotas, motoristas, passageiros,
uma promocao e uma semana de viagens concluidas para os graficos da consola.

Contas de teste (login nas apps com o telefone + codigo config.OTP_CODE, por omissao 0000):
    Rider   +351910000001 (Ana)      +351910000002 (Bruno)
    Driver  +351920000001 (Carlos, Frota Tejo)   +351920000004 (Diana, independente)
    Fleet   +351930000001 (Rui, dono da Frota Tejo)
"""
import random

import config
from core.security import hash_password
from domain import trips
from domain.models import (Notification, AdminUser, City, Document, Driver, FleetUser, LedgerEntry, Organization,
                           Product, Promo, Rider, Trip, TripEvent, Vehicle, jset, now)

# pontos conhecidos de Lisboa (tambem usados pelo simulador da consola)
PLACES = [
    ("Rua Augusta 24, Lisboa", 38.7107, -9.1367),
    ("Aeroporto Humberto Delgado", 38.7742, -9.1342),
    ("Rossio", 38.7139, -9.1394),
    ("Marquês de Pombal", 38.7253, -9.1500),
    ("Parque das Nações", 38.7681, -9.0947),
    ("Belém", 38.6979, -9.2063),
    ("Cais do Sodré", 38.7060, -9.1446),
    ("Saldanha", 38.7347, -9.1453),
    ("Alvalade", 38.7531, -9.1440),
    ("Benfica", 38.7510, -9.2003),
    ("Santa Apolónia", 38.7140, -9.1226),
    ("Campo Pequeno", 38.7420, -9.1460),
    ("Alcântara", 38.7046, -9.1777),
]

PRODUCTS = [
    # code, nome, descricao, lugares, base, km, min, minimo, reserva, cancel, ano min
    ("qolari_x", "Qolari X", "Viagens do dia a dia", 4, 100, 60, 12, 350, 50, 300, 2012),
    ("comfort", "Comfort", "Carros mais recentes e espaçosos", 4, 150, 85, 16, 500, 50, 400, 2018),
    ("xl", "Qolari XL", "Até 6 passageiros", 6, 200, 110, 20, 700, 50, 500, 2014),
    ("green", "Green", "100% elétrico", 4, 120, 65, 13, 400, 50, 300, 2018),
]


def seed(db) -> bool:
    if db.query(AdminUser).count():
        return False
    db.add(AdminUser(email=config.ADMIN_EMAIL, name="Administrador",
                     password_hash=hash_password(config.ADMIN_PASSWORD), role="admin"))

    lisboa = City(name="Lisboa", country_iso2="PT", currency="EUR", timezone="Europe/Lisbon",
                  center_lat=38.7369, center_lng=-9.1427, radius_km=30)
    db.add(lisboa)
    db.flush()
    prods = {}
    for i, (code, name, desc, cap, base, km, mn, minimum, fee, cfee, year) in enumerate(PRODUCTS):
        p = Product(city=lisboa, code=code, name=name, description=desc, capacity=cap, base_fare=base,
                    per_km=km, per_min=mn, minimum_fare=minimum, booking_fee=fee, cancel_fee=cfee,
                    min_vehicle_year=year, sort_order=i)
        db.add(p)
        prods[code] = p
    db.flush()

    tejo = Organization(name="Frota Tejo, Lda.", tax_id="515000001", email="geral@frotatejo.pt",
                        phone="+351930000001", city_id=lisboa.id, fleet_fee_pct=12,
                        iban="PT50 0000 0000 0000 0000 0000 1")
    norte = Organization(name="Lisboa Drive Partners", tax_id="515000002", email="ops@ldp.pt",
                         phone="+351930000002", city_id=lisboa.id, fleet_fee_pct=8)
    db.add_all([tejo, norte])
    db.flush()
    db.add_all([
        FleetUser(organization=tejo, first_name="Rui", last_name="Matos", phone="+351930000001",
                  email="rui@frotatejo.pt", role="owner"),
        FleetUser(organization=norte, first_name="Sofia", last_name="Lopes", phone="+351930000002",
                  email="sofia@ldp.pt", role="owner"),
    ])

    x, comfort, xl, green = (prods[c].id for c in ("qolari_x", "comfort", "xl", "green"))
    vehicles = [
        # org, marca, modelo, ano, cor, hex, matricula, lugares, categorias
        (tejo, "Toyota", "Corolla Hybrid", 2021, "Cinzento", "#8a8d91", "AA-11-BB", 4, [x, comfort]),
        (tejo, "Tesla", "Model 3", 2022, "Branco", "#f2f2f2", "AB-22-CD", 4, [x, comfort, green]),
        (tejo, "Mercedes", "Vito", 2019, "Preto", "#1b1b1b", "AC-33-EF", 7, [x, xl]),
        (norte, "Renault", "Clio", 2017, "Azul", "#2b4a8b", "AD-44-GH", 4, [x]),
        (None, "Kia", "e-Niro", 2020, "Vermelho", "#a3262a", "AE-55-IJ", 4, [x, green]),
        (norte, "Peugeot", "508", 2020, "Preto", "#202020", "AF-66-KL", 4, [x, comfort]),
    ]
    vs = []
    for org, make, model, year, color, hexc, plate, seats, cats in vehicles:
        v = Vehicle(organization=org, make=make, model=model, year=year, color=color, color_hex=hexc,
                    plate=plate, seats=seats, products=jset(cats), status="active",
                    vin=f"VF{random.randint(10**12, 10**13 - 1)}")
        db.add(v)
        vs.append(v)
    db.flush()

    drivers = [
        # nome, apelido, telefone, org, veiculo, estado, online, local
        ("Carlos", "Silva", "+351920000001", tejo, 0, "approved", True, 2),
        ("Marta", "Costa", "+351920000002", tejo, 1, "approved", True, 6),
        ("João", "Ferreira", "+351920000003", tejo, 2, "approved", False, 3),
        ("Diana", "Rocha", "+351920000004", None, 4, "approved", True, 5),
        ("Paulo", "Mendes", "+351920000005", norte, 3, "approved", True, 7),
        ("Inês", "Gomes", "+351920000006", norte, 5, "pending", False, 1),
    ]
    ds = []
    for first, last, phone, org, vi, status, online, place in drivers:
        _, lat, lng = PLACES[place]
        d = Driver(first_name=first, last_name=last, phone=phone, organization=org, city_id=lisboa.id,
                   email=f"{first.lower().replace('ã', 'a').replace('ê', 'e').replace('ó', 'o')}@exemplo.pt",
                   license_number=f"L-{random.randint(100000, 999999)}", status=status,
                   availability="online" if online else "offline", vehicle=vs[vi],
                   lat=lat + random.uniform(-.004, .004), lng=lng + random.uniform(-.004, .004),
                   location_at=now(), online_since=now() if online else None, simulated=True,
                   rating_sum=random.randint(46, 50) * 4, rating_count=40)
        db.add(d)
        ds.append(d)
    db.flush()
    vs[4].owner_driver_id = ds[3].id

    for d in ds:
        st = "approved" if d.status == "approved" else "pending"
        for kind in ("carta_conducao", "cartao_cidadao", "certificado_tvde", "registo_criminal"):
            db.add(Document(owner_type="driver", owner_id=d.id, kind=kind, status=st,
                            number=f"{random.randint(10**7, 10**8 - 1)}", expires_on="2029-12-31"))
    for d in ds:
        db.add(Notification(owner_type="driver", owner_id=d.id, title="Bem-vindo à Qolari",
                            body="A sua conta está pronta. Fique online para receber viagens.", read=False))
    for v in vs:
        for kind in ("dua", "seguro", "inspecao"):
            db.add(Document(owner_type="vehicle", owner_id=v.id, kind=kind, status="approved",
                            expires_on="2027-06-30"))

    riders = [Rider(first_name="Ana", last_name="Pereira", phone="+351910000001", email="ana@exemplo.pt"),
              Rider(first_name="Bruno", last_name="Santos", phone="+351910000002", email="bruno@exemplo.pt",
                    default_payment="card"),
              Rider(first_name="Carla", last_name="Nunes", phone="+351910000003", email="carla@exemplo.pt")]
    db.add_all(riders)
    db.add(Promo(code="BEMVINDO", description="20% na primeira viagem (máx. 5 €)", kind="percent",
                 value=20, max_discount=500, per_rider=1))
    db.flush()
    _history(db, riders, [d for d in ds if d.status == "approved"], list(prods.values()))
    return True


def _history(db, riders, drivers, products):
    """~60 viagens concluidas nos ultimos 7 dias, com o ledger datado (graficos da consola)."""
    rnd = random.Random(7)
    t0 = now()
    for _ in range(60):
        rider, driver = rnd.choice(riders), rnd.choice(drivers)
        product = rnd.choice([p for p in products if not driver.vehicle.product_ids
                              or p.id in driver.vehicle.product_ids])
        a, b = rnd.sample(PLACES, 2)
        state = (driver.availability, driver.lat, driver.lng)
        driver.availability = "online"
        trip = trips.request_trip(db, rider, product, (a[1], a[2]), (b[1], b[2]), a[0], b[0])
        for o in list(trip.offers):          # o despacho escolhe o mais proximo; aqui forca-se
            o.state = "withdrawn"
        trips.offer_to(db, trip, driver, actor="system")
        trips.accept_offer(db, trip.offers[-1])
        trips.start(db, trip)
        trips.complete(db, trip, duration_s=trip.est_duration_s or 600)
        trips.rate(db, trip, "rider", rnd.choice([5, 5, 5, 4, 4, 3]))
        driver.availability, driver.lat, driver.lng = state
        # datar no passado
        start = t0 - rnd.randint(3600, 7 * 86400)
        dur = trip.duration_s or 600
        trip.requested_at, trip.accepted_at = start, start + 40
        trip.arrived_at, trip.started_at = start + 300, start + 360
        trip.completed_at = start + 360 + dur
        db.flush()
        for e in db.query(TripEvent).filter(TripEvent.trip_id == trip.id):
            e.at = start
        for e in db.query(LedgerEntry).filter(LedgerEntry.trip_id == trip.id):
            e.at = trip.completed_at
    # o historico nao gera mensagens pendentes para as apps
    from domain.models import PushMessage
    db.query(PushMessage).delete()
