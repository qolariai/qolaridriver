# -*- coding: utf-8 -*-
"""Amostra cores de pontos e regioes das capturas da User Lite.

Uso: python sample_colors.py <imagem> <x,y> [x,y ...]
     python sample_colors.py <imagem> --top x1,y1,x2,y2
"""
import sys
from collections import Counter

from PIL import Image


def main() -> None:
    path = sys.argv[1]
    im = Image.open(path).convert("RGB")
    if sys.argv[2] == "--top":
        x1, y1, x2, y2 = (int(v) for v in sys.argv[3].split(","))
        crop = im.crop((x1, y1, x2, y2))
        counts = Counter(crop.getdata())
        total = sum(counts.values())
        for color, n in counts.most_common(12):
            print(f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}  {100 * n / total:5.2f}%  {n}")
        return
    for arg in sys.argv[2:]:
        x, y = (int(v) for v in arg.split(","))
        c = im.getpixel((x, y))
        print(f"{arg:10} #{c[0]:02x}{c[1]:02x}{c[2]:02x}")


if __name__ == "__main__":
    main()
