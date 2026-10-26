# -*- coding: utf-8 -*-
"""Compara duas capturas (regressão visual simples).

    python tools/visual_diff.py baseline.png atual.png --threshold 0.02 --out diff.png

Diferença média absoluta por canal, 0..1. Sai com código 1 se passar o limite.
Não substitui revisão humana; apanha deslocamentos/cortes grandes.
"""
import argparse
import sys
from pathlib import Path

from PIL import Image, ImageChops


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("baseline")
    ap.add_argument("current")
    ap.add_argument("--threshold", type=float, default=0.02)
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    a = Image.open(args.baseline).convert("RGB")
    b = Image.open(args.current).convert("RGB")
    if a.size != b.size:
        b = b.resize(a.size)
    diff = ImageChops.difference(a, b)
    pixels = list(diff.getdata())
    total = sum(sum(p) for p in pixels)
    maximum = len(pixels) * 255 * 3
    ratio = total / maximum
    print(f"diferença média: {ratio:.4%} (limite {args.threshold:.2%})")
    if args.out:
        # amplifica para ser visível
        amp = diff.point(lambda x: min(255, x * 4))
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        amp.save(args.out)
        print(f"diff: {args.out}")
    return 1 if ratio > args.threshold else 0


if __name__ == "__main__":
    sys.exit(main())
