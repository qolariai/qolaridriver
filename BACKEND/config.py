# -*- coding: utf-8 -*-
"""Configuracao do backend Qolari Mobility (Rider + Driver + Fleet).

Cada app tem o URL do backend gravado na APK (recompiladas com tools/repoint_apks.py +
tools/patch_apk_host.py; ver README):

    Qolari Driver  http://127.0.0.1:8091
    Qolari Rider   http://127.0.0.1:8090
    Qolari Fleet   http://127.0.0.1:3000

No telemovel (USB) o 127.0.0.1 chega ao PC por `adb reverse tcp:PORTA tcp:PORTA` (mesmas portas).
O servidor abre uma porta por app e identifica a app pela porta local onde o pedido entrou.
A consola (backoffice) tem a sua propria porta.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("DATA_DIR", BASE_DIR / "data"))
LOG_DIR = Path(os.environ.get("LOG_DIR", BASE_DIR / "logs"))
CONTRACTS_DIR = BASE_DIR / "contracts"

DB_URL = os.environ.get("DB_URL", f"sqlite:///{(DATA_DIR / 'qolari.db').as_posix()}")

# porta -> app (as portas que estao gravadas nas APKs)
APP_PORTS = {
    "driver": int(os.environ.get("DRIVER_PORT", "8091")),
    "rider": int(os.environ.get("RIDER_PORT", "8090")),
    "fleet": int(os.environ.get("FLEET_PORT", "3000")),
}
# portas extra -> app, alem das de cima. A IPA iOS da Driver usa http://192.168.1.9 sem porta (= 80)
# e chega pela rede Wi-Fi (sem adb reverse). EXTRA_APP_PORTS="80=driver,81=rider"; vazio = nenhuma.
EXTRA_APP_PORTS = {int(p): a for p, a in (x.split("=") for x in os.environ.get("EXTRA_APP_PORTS", "80=driver").split(",") if x)}
CONSOLE_PORT = int(os.environ.get("CONSOLE_PORT", "8300"))
# gRPC das apps (HTTP/2 sem TLS; apps/grpc.py). A Driver foi alterada para 127.0.0.1:8092 (adb reverse tcp:8092)
GRPC_PORTS = {"driver": int(os.environ.get("DRIVER_GRPC_PORT", "8092"))}
BIND_HOST = os.environ.get("BIND_HOST", "0.0.0.0")
# IP que as APKs usam (so para mostrar na consola)
PUBLIC_HOST = os.environ.get("PUBLIC_HOST", "127.0.0.1")
# Base publica da consola/partilha (ex.: https://admin-driver.qolari.com). Vazio = host:porta de laboratorio.
PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "").rstrip("/")

# Login sem SMS: o codigo de verificacao e sempre este
OTP_CODE = os.environ.get("OTP_CODE", "0000")

SECRET = os.environ.get("SECRET", "qolari-lab-trocar")
ACCESS_TTL_S = int(os.environ.get("ACCESS_TTL_S", str(30 * 86400)))
CONSOLE_TTL_S = int(os.environ.get("CONSOLE_TTL_S", str(12 * 3600)))
# STRICT_AUTH=1 -> pedido das apps sem token valido = 401 (por omissao usa o utilizador do seed)
STRICT_AUTH = os.environ.get("STRICT_AUTH", "0") == "1"

# 1.o administrador da consola (so e criado com a BD vazia)
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@qolari.local")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin")

# Build do backoffice React (../BACKOFFICE/dist), servido em http://127.0.0.1:8300/
BACKOFFICE_DIST = Path(os.environ.get("BACKOFFICE_DIST", BASE_DIR.parent / "BACKOFFICE" / "dist"))

# Ficheiros estaticos servidos nas portas das apps em /static/ (ex.: static/products/<code>.png)
STATIC_DIR = BASE_DIR / "static"

# Ficheiros enviados (documentos de motoristas/veiculos)
UPLOAD_DIR = DATA_DIR / "uploads"
UPLOAD_MAX_BYTES = 8 * 1024 * 1024

# Relogio do dominio (expira propostas, despacho, simulacao); os testes desligam-no
RUN_TICKER = os.environ.get("RUN_TICKER", "1") == "1"

# Rate limit em memoria (login/map-report); os testes desligam-no
RATE_LIMIT = os.environ.get("RATE_LIMIT", "1") == "1"

# Long-polling das apps (ramen) e da consola
POLL_HOLD_S = float(os.environ.get("POLL_HOLD_S", "20"))

# FCM HTTP v1 (a chave da conta de servico nunca vai para o repositorio)
FCM_SERVICE_ACCOUNT = Path(os.environ.get("FCM_SERVICE_ACCOUNT", DATA_DIR / "firebase-service-account.json"))
FCM_PROJECT_ID = os.environ.get("FCM_PROJECT_ID", "qolari-driver-prod")

# 'lab' (por omissao) ou 'production'. Em producao, validate_production() recusa os defaults.
ENVIRONMENT = os.environ.get("ENVIRONMENT", "lab")
PRODUCTION = ENVIRONMENT == "production"


def production_problems() -> list[str]:
    """Problemas que impedem arrancar com ENVIRONMENT=production."""
    problems = []
    if SECRET == "qolari-lab-trocar":
        problems.append("SECRET ainda e o default do laboratorio")
    if ADMIN_PASSWORD == "admin":
        problems.append("ADMIN_PASSWORD ainda e 'admin'")
    if not STRICT_AUTH:
        problems.append("STRICT_AUTH=0 (qualquer pedido sem token usa o 1.o utilizador)")
    if DB_URL.startswith("sqlite"):
        problems.append("DB_URL e SQLite; usar PostgreSQL em producao")
    if not RATE_LIMIT:
        problems.append("RATE_LIMIT=0")
    if OTP_CODE == "0000":
        problems.append("OTP_CODE fixo (0000); ligar SMS/OTP real")
    if PUBLIC_HOST in ("127.0.0.1", "localhost"):
        problems.append("PUBLIC_HOST ainda aponta para localhost")
    if not (os.environ.get("GOOGLE_MAPS_KEY", "").strip()
            or (DATA_DIR / "google_maps_api_key.txt").is_file()
            or (BASE_DIR.parent / "google_maps_api_key.txt").is_file()):
        problems.append("sem GOOGLE_MAPS_KEY nem google_maps_api_key.txt")
    return problems


def validate_production() -> None:
    if PRODUCTION:
        problems = production_problems()
        if problems:
            raise RuntimeError("configuracao de producao insegura: " + "; ".join(problems))
