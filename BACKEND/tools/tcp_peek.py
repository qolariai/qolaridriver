# -*- coding: utf-8 -*-
"""Proxy TCP de diagnostico: escuta em <porta>, regista os primeiros bytes de cada ligacao e encaminha
para <destino>. Serve para ver o que uma app manda antes de chegar ao HTTP (ex.: HTTP/2 em claro, TLS).

    python tcp_peek.py 8091 18091 [ficheiro.log]
"""
import socket, sys, threading, time

LISTEN, TARGET = int(sys.argv[1]), int(sys.argv[2])
LOG = open(sys.argv[3] if len(sys.argv) > 3 else f"peek_{LISTEN}.log", "a", encoding="utf-8", buffering=1)


def pipe(src, dst, tag, first):
    try:
        while True:
            data = src.recv(65536)
            if not data:
                break
            if first[0] < 3:
                LOG.write(f"{time.strftime('%H:%M:%S')} {tag} {len(data)}B {data[:160]!r}\n")
                first[0] += 1
            dst.sendall(data)
    except OSError:
        pass
    finally:
        for s in (src, dst):
            try:
                s.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass


def handle(c):
    try:
        u = socket.create_connection(("127.0.0.1", TARGET))
    except OSError as e:
        LOG.write(f"destino indisponivel: {e}\n")
        c.close()
        return
    n_up, n_down = [0], [0]
    threading.Thread(target=pipe, args=(c, u, ">>", n_up), daemon=True).start()
    pipe(u, c, "<<", n_down)


srv = socket.socket()
srv.bind(("127.0.0.1", LISTEN))
srv.listen(64)
LOG.write(f"--- a escutar {LISTEN} -> {TARGET}\n")
while True:
    conn, _ = srv.accept()
    threading.Thread(target=handle, args=(conn,), daemon=True).start()
