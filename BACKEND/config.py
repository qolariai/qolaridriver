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

# Long-polling das apps (ramen) e da consola
POLL_HOLD_S = float(os.environ.get("POLL_HOLD_S", "20"))
