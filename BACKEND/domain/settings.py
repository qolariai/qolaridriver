# -*- coding: utf-8 -*-
"""Parametros da plataforma editaveis na consola (tabela settings, JSON por chave)."""
from domain.models import Setting, jget, jset

DEFAULTS = {
    "platform_commission_pct": 20.0,   # % da tarifa bruta que fica para a plataforma
    "offer_timeout_s": 20,             # tempo do motorista para aceitar uma proposta
    # ---- Radar de viagens (Trip Radar) ----
    "radar_enabled": True,             # liga o despacho em lote (varios motoristas ao mesmo tempo)
    "radar_batch_size": 6,             # motoristas que recebem a mesma viagem no Radar
    "radar_window_s": 20,              # tempo que o pedido fica visivel no Radar (para tocar)
    "radar_match_s": 4,                # tempo de emparelhamento depois do 1.o toque (melhor ETA ganha)
    "radar_max_rejections": 2,         # rondas de Radar falhadas antes de a viagem voltar a Exclusiva
    "radar_min_pickup_km": 2.0,        # recolha mais longe que isto -> candidata a Radar
    "radar_share_pct": 0,              # % extra de viagens curtas ao Radar (0 = so as dificeis)
    "dispatch_radius_km": 8.0,         # so motoristas a menos disto da recolha
    "arrive_radius_m": 80,             # motorista a menos disto da recolha -> "chegou" (a Driver nao avisa)
    "search_timeout_s": 90,            # sem motorista ao fim disto -> no_drivers
    "max_offers_per_trip": 6,
    "rider_free_cancel_s": 120,        # cancelar depois disto (com motorista atribuido) paga taxa
    "wait_free_s": 120,                # espera gratis na recolha (contagem decrescente no ecra)
    # ---- Modo Destino (lupa do mapa) ----
    "destination_mode_radius_km": 7.0,   # so viagens cujo destino fica a menos disto do marcado
    "destination_mode_daily_filters": 2, # filtros por dia (o original mostra "2/2 filtros restantes")
    "avg_speed_kmh": 28.0,             # estimativas de duracao e simulacao
    "road_factor": 1.35,               # distancia em linha reta -> estrada
    "simulate_movement": True,         # motoristas simulados andam sozinhos no mapa
    "driver_auto_approve": False,      # registo na app Driver ja fica aprovado
    "rider_signup_open": True,         # numero novo na app Rider cria conta
    "support_phone": "+351 210 000 000",
}

LABELS = {
    "platform_commission_pct": "Comissão da plataforma (%)",
    "offer_timeout_s": "Tempo para aceitar proposta (s)",
    "radar_enabled": "Radar de viagens (despacho em lote)",
    "radar_batch_size": "Motoristas por leilão no Radar",
    "radar_window_s": "Tempo do pedido no Radar (s)",
    "radar_match_s": "Emparelhamento após 1.º toque (s)",
    "radar_max_rejections": "Recusas no Radar até voltar a Exclusiva",
    "radar_min_pickup_km": "Radar: recolha mínima para entrar no Radar (km)",
    "radar_share_pct": "Radar: % de viagens curtas enviadas ao Radar",
    "dispatch_radius_km": "Raio de despacho (km)",
    "arrive_radius_m": "Chegada automática à recolha (m)",
    "search_timeout_s": "Procura máxima por motorista (s)",
    "max_offers_per_trip": "Propostas máximas por viagem",
    "rider_free_cancel_s": "Cancelamento grátis do passageiro (s)",
    "wait_free_s": "Espera grátis na recolha (s)",
    "destination_mode_radius_km": "Modo Destino: raio à volta do destino (km)",
    "destination_mode_daily_filters": "Modo Destino: filtros por dia",
    "avg_speed_kmh": "Velocidade média (km/h)",
    "road_factor": "Fator estrada / linha reta",
    "simulate_movement": "Simular movimento dos motoristas de teste",
    "driver_auto_approve": "Aprovar motoristas automaticamente",
    "rider_signup_open": "Registo aberto na app Rider",
    "support_phone": "Telefone de apoio",
}


def get(db, key: str):
    row = db.get(Setting, key)
    return jget(row.value, DEFAULTS.get(key)) if row else DEFAULTS.get(key)


def all_values(db) -> dict:
    out = dict(DEFAULTS)
    for row in db.query(Setting).all():
        out[row.key] = jget(row.value, out.get(row.key))
    return out


def update(db, values: dict) -> dict:
    for key, value in values.items():
        if key not in DEFAULTS:
            raise KeyError(key)
        default = DEFAULTS[key]
        if isinstance(default, bool):
            value = bool(value)
        elif isinstance(default, (int, float)):
            value = type(default)(value)
            if value < 0:
                raise ValueError(f"{key} nao pode ser negativo")
        row = db.get(Setting, key)
        if row:
            row.value = jset(value)
        else:
            db.add(Setting(key=key, value=jset(value)))
    db.flush()
    return all_values(db)
