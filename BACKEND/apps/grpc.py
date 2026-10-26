# -*- coding: utf-8 -*-
"""gRPC das apps (HTTP/2 sem TLS, servido pelo hypercorn numa porta por app — config.GRPC_PORTS).

As APKs fazem parte das chamadas por gRPC (`@GrpcApi(path="api/grpc/<servico>/<metodo>")`, canal
`la1.e0` -> grpc-okhttp). Originalmente o canal ia para cn-geo1.uber.com:443 com TLS; na Driver foi
mudado para `127.0.0.1:8092` em claro (smali `la1/e0.a`, ver PROMPT_BACKEND_CENTRAL.md).

Registo:  @grpc_handles("driver", "/uber.marketplace....ParameterServingPresentation/GetMobileParameters")
Handler:  fn(app, fields, raw) -> bytes (mensagem protobuf ja codificada; b"" = mensagem vazia)
Sem handler: mensagem vazia + grpc-status 0, e o pedido fica "por mapear" na consola (como no rtapi).
"""
import asyncio
import struct
import threading
import time
import traceback

import config
from apps import rtapi

GRPC_ROUTES: dict[tuple[str, str], callable] = {}


def grpc_handles(apps, *paths):
    apps = (apps,) if isinstance(apps, str) else tuple(apps)

    def deco(fn):
        for a in apps:
            for p in paths:
                GRPC_ROUTES[(a, p)] = fn
        return fn
    return deco


# ---- protobuf minimo (so para registo e para montar respostas simples) -----------------------
def _varint(buf: bytes, i: int):
    n = shift = 0
    while True:
        b = buf[i]
        i += 1
        n |= (b & 0x7F) << shift
        if not b & 0x80:
            return n, i
        shift += 7


def decode(buf: bytes, depth: int = 0):
    """bytes -> {tag: [valores]} (submensagens descodificadas quando parecem validas; senao texto/bytes)."""
    out, i = {}, 0
    try:
        while i < len(buf):
            key, i = _varint(buf, i)
            tag, wt = key >> 3, key & 7
            if wt == 0:
                v, i = _varint(buf, i)
            elif wt == 1:
                v, i = struct.unpack_from("<d", buf, i)[0], i + 8
            elif wt == 5:
                v, i = struct.unpack_from("<f", buf, i)[0], i + 4
            elif wt == 2:
                n, i = _varint(buf, i)
                raw, i = buf[i:i + n], i + n
                v = None
                if depth < 6 and raw:
                    sub = decode(raw, depth + 1)
                    if sub is not None and sub:
                        v = sub
                if v is None:
                    try:
                        v = raw.decode("utf-8")
                    except UnicodeDecodeError:
                        v = raw.hex()
            else:
                return None
            out.setdefault(tag, []).append(v)
    except (IndexError, struct.error):
        return None
    return out


def enc_varint(n: int) -> bytes:
    out = bytearray()
    while True:
        b = n & 0x7F
        n >>= 7
        if n:
            out.append(b | 0x80)
        else:
            out.append(b)
            return bytes(out)


def field(tag: int, value) -> bytes:
    """Campo protobuf: int -> varint, bool -> varint, str/bytes -> length-delimited, float -> double."""
    if isinstance(value, bool) or isinstance(value, int):
        return enc_varint(tag << 3) + enc_varint(int(value))
    if isinstance(value, float):
        return enc_varint(tag << 3 | 1) + struct.pack("<d", value)
    if isinstance(value, str):
        value = value.encode()
    return enc_varint(tag << 3 | 2) + enc_varint(len(value)) + value


# ---- ASGI ------------------------------------------------------------------------------------
PORT_APP = {}


async def asgi(scope, receive, send):
    if scope["type"] == "lifespan":
        while True:
            msg = await receive()
            if msg["type"] == "lifespan.startup":
                await send({"type": "lifespan.startup.complete"})
            elif msg["type"] == "lifespan.shutdown":
                await send({"type": "lifespan.shutdown.complete"})
                return
    if scope["type"] != "http":
        return
    t0 = time.perf_counter()
    app = PORT_APP.get((scope.get("server") or ("", 0))[1], "driver")
    path = scope["path"]
    body = b""
    while True:
        msg = await receive()
        body += msg.get("body", b"")
        if not msg.get("more_body"):
            break
    msg_bytes = body[5:] if len(body) >= 5 else b""
    fields = decode(msg_bytes) if msg_bytes else {}
    # as APKs mandam /api/grpc/<servico>/<metodo> (@GrpcApi path="api/grpc/...")
    fn = GRPC_ROUTES.get((app, path[len("/api/grpc"):] if path.startswith("/api/grpc/") else path))
    status, message, out = "0", "", b""
    try:
        if fn:
            out = fn(app, fields or {}, msg_bytes) or b""
    except Exception as e:
        traceback.print_exc()
        status, message = "13", f"{type(e).__name__}: {e}"  # INTERNAL
    frame = b"\x00" + struct.pack(">I", len(out)) + out
    await send({"type": "http.response.start", "status": 200, "trailers": True,
                "headers": [(b"content-type", b"application/grpc")]})
    await send({"type": "http.response.body", "body": frame, "more_body": False})
    await send({"type": "http.response.trailers", "more_trailers": False,
                "headers": [(b"grpc-status", status.encode()), (b"grpc-message", message.encode())]})
    handler = f"{fn.__module__.split('.')[-1]}.{fn.__name__}" if fn else ""
    shown = {"_grpc": path, "request": fields if fields is not None else msg_bytes.hex()[:400]}
    await asyncio.to_thread(rtapi._record, app, "POST", path, path, handler, 200 if status == "0" else 500,
                            (time.perf_counter() - t0) * 1000, None,
                            {"grpc-status": status, "message": message, "response": decode(out) or out.hex()},
                            len(body), "application/grpc " + str(shown)[:1500])


def start_in_thread():
    """Arranca o hypercorn (HTTP/2 sem TLS) nas portas gRPC, numa thread com o seu proprio event loop."""
    from hypercorn.asyncio import serve
    from hypercorn.config import Config

    cfg = Config()
    cfg.bind = [f"{config.BIND_HOST}:{p}" for p in config.GRPC_PORTS.values()]
    cfg.loglevel = "WARNING"
    PORT_APP.update({p: a for a, p in config.GRPC_PORTS.items()})

    async def main():
        # shutdown_trigger proprio: sem ele o hypercorn instala sinais, o que so e possivel na thread principal
        await serve(asgi, cfg, shutdown_trigger=asyncio.Event().wait)

    def run():
        asyncio.run(main())

    t = threading.Thread(target=run, name="grpc", daemon=True)
    t.start()
    return t
