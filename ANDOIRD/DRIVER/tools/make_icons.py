# -*- coding: utf-8 -*-
# Generic launcher icon generator (pure-python PNG writer)
# Design: dark rounded square + white "Q" ring mark (steering-wheel like)
import zlib, struct, math, os

ROOT = r"C:\xampp\htdocs\QOLARI\PROJETOS OFICIAIS\QOLARI DRIVER\DRIVER\decoded\res"
BG = (16, 24, 40, 255)        # slate-900
FG = (255, 255, 255, 255)     # white mark

def png_write(path, w, h, px):  # px: bytearray RGBA len w*h*4
    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    raw = b"".join(b"\x00" + bytes(px[y*w*4:(y+1)*w*4]) for y in range(h))
    data = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)) \
           + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")
    open(path, "wb").write(data)

def draw_mark(px, w, h, cx, cy, radius, thick, color):
    """Q-mark: ring + diagonal tail, distance-field anti-aliased."""
    tail_len = radius * 0.55
    for y in range(h):
        for x in range(w):
            dx, dy = x - cx, y - cy
            d = math.hypot(dx, dy)
            a = 0.0
            # ring
            ring = abs(d - radius)
            a = max(a, 1.0 - ring / thick)
            # tail: segment from (r*0.7,r*0.7) dir to (r*0.7+tail,r*0.7+tail) in 45deg
            tx0, ty0 = radius * 0.62, radius * 0.62
            px_, py_ = dx - tx0, dy - ty0
            tdirx = tdiry = math.sqrt(0.5)
            t = px_ * tdirx + py_ * tdiry
            t = max(0.0, min(t, tail_len))
            ddx, ddy = px_ - t * tdirx, py_ - t * tdiry
            tail_d = math.hypot(ddx, ddy)
            a = max(a, 1.0 - tail_d / (thick * 1.05))
            if a > 0.0:
                i = (y * w + x) * 4
                al = min(255, int(255 * a))
                # simple alpha-over on existing pixel
                ba = px[i+3] / 255.0; fa = al / 255.0
                oa = fa + ba * (1 - fa)
                if oa <= 0: continue
                for c in range(3):
                    px[i+c] = int((color[c]*fa + px[i+c]*ba*(1-fa)) / oa)
                px[i+3] = int(255 * oa)

def canvas(w, h, color=None):
    px = bytearray(w * h * 4)
    if color:
        for i in range(0, len(px), 4):
            px[i:i+4] = bytes(color)
    return px

def mask_shape(px, w, h, round_=False, rradius=0.18):
    """apply rounded-rect or circle alpha mask"""
    cx, cy = w / 2.0, h / 2.0
    rr = min(w, h) * rradius if not round_ else 0
    R = min(w, h) / 2.0
    for y in range(h):
        for x in range(w):
            if round_:
                d = math.hypot(x - cx + .5, y - cy + .5)
                a = 1.0 if d <= R else max(0.0, R - d)
            else:
                qx = abs(x - cx + .5) - (cx - rr); qy = abs(y - cy + .5) - (cy - rr)
                d = math.hypot(max(qx, 0), max(qy, 0)) + min(max(qx, qy), 0) - rr
                a = 1.0 if d <= 0 else max(0.0, -d)
            i = (y * w + x) * 4
            px[i+3] = int(px[i+3] * a)

DENS = {"mipmap-mdpi": 1.0, "mipmap-hdpi": 1.5, "mipmap-xhdpi": 2.0,
        "mipmap-xxhdpi": 3.0, "mipmap-xxxhdpi": 4.0}

for d, s in DENS.items():
    dirp = os.path.join(ROOT, d)
    if not os.path.isdir(dirp):
        continue
    ad = int(108 * s)   # adaptive canvas
    lg = int(48 * s)    # legacy icon

    # background (adaptive): solid
    px = canvas(ad, ad, BG)
    png_write(os.path.join(dirp, "ub__ic_launcher_background.png"), ad, ad, px)
    png_write(os.path.join(dirp, "ub__ic_launcher_background_b.png"), ad, ad, px)

    # foreground (adaptive): transparent + centered mark inside safe zone
    px = canvas(ad, ad)
    draw_mark(px, ad, ad, ad/2, ad/2, ad*0.21, max(1.5, ad*0.028), FG)
    png_write(os.path.join(dirp, "ub__ic_launcher_foreground.png"), ad, ad, px)
    png_write(os.path.join(dirp, "ub__ic_launcher_foreground_b.png"), ad, ad, px)

    # legacy square
    px = canvas(lg, lg, BG)
    draw_mark(px, lg, lg, lg/2, lg/2, lg*0.28, max(1.0, lg*0.045), FG)
    mask_shape(px, lg, lg, round_=False, rradius=0.22)
    png_write(os.path.join(dirp, "ub__ic_launcher.png"), lg, lg, px)

    # legacy round
    px = canvas(lg, lg, BG)
    draw_mark(px, lg, lg, lg/2, lg/2, lg*0.28, max(1.0, lg*0.045), FG)
    mask_shape(px, lg, lg, round_=True)
    png_write(os.path.join(dirp, "ub__ic_launcher_round.png"), lg, lg, px)

    print("icons:", d)
print("done")
