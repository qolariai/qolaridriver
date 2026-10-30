# -*- coding: utf-8 -*-
r"""Arranque:  .venv\Scripts\python server.py

Abre as 4 portas num so processo (uvicorn com varios sockets). Se uma porta estiver ocupada
(ex.: Apache do XAMPP na 80) avisa e continua com as outras.
"""
import socket, sys

import uvicorn

import config

LABEL = {"driver": "Qolari Driver", "rider": "Qolari Rider", "fleet": "Qolari Fleet"}


def bind(port: int) -> socket.socket | None:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # sem SO_REUSEADDR no Windows: la deixaria 2 processos na mesma porta. Em Linux e preciso: sem ele um
    # restart falha com "Address already in use" enquanto ha ligacoes da execucao anterior em TIME_WAIT
    if sys.platform != "win32":
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.bind((config.BIND_HOST, port))
    except OSError as e:
        s.close()
        print(f"  !! porta {port} indisponivel ({e.strerror}) -> netstat -ano | findstr :{port}")
        return None
    s.listen(128)
    s.set_inheritable(True)
    return s


def main():
    sys.stdout.reconfigure(line_buffering=True)
    print("Qolari Mobility — backend local")
    socks = []
    console = bind(config.CONSOLE_PORT)
    if not console:
        sys.exit("a porta da consola e obrigatoria")
    socks.append(console)
    pw = config.ADMIN_PASSWORD if config.ADMIN_PASSWORD == "admin" else "(ADMIN_PASSWORD)"  # nao escrever a real no log
    print(f"  consola   http://127.0.0.1:{config.CONSOLE_PORT}   (login {config.ADMIN_EMAIL} / {pw})")
    for app, port in config.APP_PORTS.items():
        s = bind(port)
        if s:
            socks.append(s)
            host = config.PUBLIC_HOST + ("" if port == 80 else f":{port}")
            print(f"  {LABEL[app]:<14} http://{host}")
    for port, app in config.EXTRA_APP_PORTS.items():
        if port in config.APP_PORTS.values():
            continue
        s = bind(port)
        if s:
            socks.append(s)
            print(f"  {LABEL[app]:<14} http://<IP do PC>" + ("" if port == 80 else f":{port}") + "  (rede: iOS)")
    from apps import grpc
    grpc.start_in_thread()
    for app, port in config.GRPC_PORTS.items():
        print(f"  {LABEL[app]:<14} gRPC http://{config.PUBLIC_HOST}:{port}  (HTTP/2 sem TLS)")
    print(f"  codigo de login nas apps: {config.OTP_CODE}")
    server = uvicorn.Server(uvicorn.Config("main:app", log_level="warning", access_log=False))
    server.run(sockets=socks)


if __name__ == "__main__":
    main()
