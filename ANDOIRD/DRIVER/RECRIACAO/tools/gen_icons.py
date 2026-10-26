# -*- coding: utf-8 -*-
"""Gera os icones proprios (vector drawables 24dp, traco de 2dp) usados por Views e Compose.
Desenhados para esta recriacao: nao copiam os icones da original. Uso: python gen_icons.py <pasta res/drawable>"""
import sys
from pathlib import Path

STROKE = {  # nome -> pathData (traco)
    "person": "M12,4 a4,4 0 1,0 0.01,0 M4,20 a8,5 0 0,1 16,0 Z",
    "lock": "M5,11 H19 V20 H5 Z M8,11 V8 a4,4 0 0,1 8,0 V11 M12,15 h0.01",
    "pencil": "M4,20 L5,15 L16,4 L20,8 L9,19 Z M14,6 L18,10",
    "accessibility": "M12,3 a2,2 0 1,0 0.01,0 M5,9 H19 M12,9 V15 M12,15 L8,21 M12,15 L16,21",
    "phone": "M8,3 H16 a2,2 0 0,1 2,2 V19 a2,2 0 0,1 -2,2 H8 a2,2 0 0,1 -2,-2 V5 a2,2 0 0,1 2,-2 Z M11,18 h2",
    "navigation": "M12,3 L20,20 L12,16 L4,20 Z",
    "speaker": "M4,9 H8 L13,5 V19 L8,15 H4 Z M16,9 a4,4 0 0,1 0,6 M18,6 a8,8 0 0,1 0,12",
    "moon": "M20,14 a8,8 0 1,1 -9,-10 a6,6 0 0,0 9,10 Z",
    "help": "M12,3 a9,9 0 1,0 0.01,0 M9.5,9.5 a2.5,2.5 0 1,1 3.5,2.3 c-0.7,0.4 -1,0.9 -1,1.7 M12,17.5 h0.01",
    "shield": "M12,3 L19,6 V12 c0,4.5 -3,7.5 -7,9 c-4,-1.5 -7,-4.5 -7,-9 V6 Z M8.5,12 L11,14.5 L15.5,9.5",
    "gear": "M12,3 L14,5 H17 L18,8 L20,10 V13 L18,15 L17,18 H14 L12,21 L10,18 H7 L6,15 L4,13 V10 L6,8 L7,5 H10 Z M12,9 a3,3 0 1,0 0.01,0",
    "compass": "M12,3 L21,12 L12,21 L3,12 Z M12,9 L15,12 L12,15 L9,12 Z",
    "briefcase": "M3,8 H21 V19 H3 Z M9,8 V5 H15 V8",
    "gift": "M4,10 H20 V20 H4 Z M3,7 H21 V10 H3 Z M12,7 V20 M12,7 c-3,-4 -6,-1 -3,0 M12,7 c3,-4 6,-1 3,0",
    "car": "M4,14 L6,8 H18 L20,14 V19 H4 Z M4,14 H20 M7,17 h0.01 M17,17 h0.01",
    "document": "M6,3 H18 V21 H6 Z M9,8 H15 M9,12 H15",
    "umbrella": "M3,12 a9,8 0 0,1 18,0 Z M12,12 V18 a2,2 0 0,1 -4,0",
    "calculator": "M6,3 H18 V21 H6 Z M9,7 H15 V10 H9 Z M9,13 h0.01 M12,13 h0.01 M15,13 h0.01 M9,17 h0.01 M12,17 h0.01 M15,17 h0.01",
    "wallet": "M3,6 L21,6 L21,18 L3,18 Z M15,12 L18,12",
    "info": "M12,3 a9,9 0 1,0 0.01,0 M12,11 V17 M12,7.5 h0.01",
    "chevron": "M9,5 L16,12 L9,19",
    "back": "M20,12 H5 M11,5 L4,12 L11,19",
    "route": "M7,4 a2,2 0 1,0 0.01,0 M7,6 V16 a3,3 0 0,0 6,0 V8 a3,3 0 0,1 6,0 V10",
    "fleet": "M3,15 L5,10 H13 L15,15 V19 H3 Z M7,10 L9,6 H17 L19,10",
    "book": "M3,5 L12,7 L21,5 V19 L12,21 L3,19 Z M12,7 V21",
    "box": "M12,3 L20,7 V17 L12,21 L4,17 V7 Z M4,7 L12,11 L20,7 M12,11 V21",
    "calendar": "M4,6 H20 V20 H4 Z M4,10 H20 M8,3 V7 M16,3 V7",
    "folder": "M3,6 H10 L12,8 H21 V19 H3 Z",
    "pin_plus": "M12,21 C6,15 5,12 5,9 a7,7 0 0,1 14,0 c0,3 -1,6 -7,12 Z M12,7 V13 M9,10 H15",
    "mail": "M3,6 L21,6 L21,18 L3,18 Z M3,7 L12,13 L21,7",
    "check": "M5,12 L10,17 L19,7",
    "bolt": "M13,3 L6,13 H12 L11,21 L18,10 H12 Z",
    "search": "M11,4 a7,7 0 1,0 0.01,0 M16,16 L21,21",
    "filter": "M4,8 H12 M18,8 H20 M4,16 H6 M12,16 H20 M15,6 a2,2 0 1,0 0.01,0 M9,14 a2,2 0 1,0 0.01,0",
    "expand": "M4,10 V4 H10 M20,14 V20 H14 M4,4 L10,10 M20,20 L14,14",
    "wifi_off": "M3,9 a14,14 0 0,1 18,0 M6,12.5 a9,9 0 0,1 12,0 M9,16 a4.5,4.5 0 0,1 6,0 M12,19.5 h0.01 M4,4 L20,20",
    "warning": "M12,3 L22,20 H2 Z M12,9 V14 M12,17 h0.01",
    "list": "M8,6 H21 M8,12 H21 M8,18 H21 M4,6 h0.01 M4,12 h0.01 M4,18 h0.01",
    "chart": "M5,20 V12 M10,20 V5 M15,20 V9 M20,20 V14",
    "locate": "M12,8 a4,4 0 1,0 0.01,0 M12,2 V5 M12,19 V22 M2,12 H5 M19,12 H22",
    "steering": "M12,3 a9,9 0 1,0 0.01,0 M3,12 H9 M15,12 H21 M12,15 V21 M12,10 a2,2 0 1,0 0.01,0",
    "arrow_right": "M5,12 H19 M13,6 L19,12 L13,18",
    "minus": "M5,12 H19",
    "chevron_down": "M6,9 L12,15 L18,9",
    "home_map": "M4,11 L12,4 L20,11 V20 H15 V14 H9 V20 H4 Z",
    "close": "M6,6 L18,18 M18,6 L6,18",
    "bookmark": "M6,3 H18 V21 L12,16 L6,21 Z",
    "burst": "M12,2 L14.5,6 L19,5 L18,9.5 L22,12 L18,14.5 L19,19 L14.5,18 L12,22 L9.5,18 L5,19 L6,14.5 L2,12 L6,9.5 L5,5 L9.5,6 Z M12,9 a3,3 0 1,0 0.01,0",
    "plane": "M2,14 L10,12 L8,3 L11,3 L16,11 L22,9 L22,12 L16,15 L11,21 L8,21 L10,15 L2,17 Z",
}
FILL = {  # nome -> pathData (preenchido)
    "star": "M12,3 L14.5,9 L21,9.5 L16,14 L17.5,21 L12,17.5 L6.5,21 L8,14 L3,9.5 L9.5,9 Z",
    "thumb": "M3,11 H7 V20 H3 Z M8,11 L11,3 c1.5,0 2.5,1 2.5,2.5 L13,9 H19 c1.3,0 2.3,1.2 2,2.5 L19.5,19 c-0.3,1 -1,1.5 -2,1.5 H8 Z",
    "half_circle": "M12,3 a9,9 0 0,1 0,18 Z",
    "diamond": "M12,2 L22,12 L12,22 L2,12 Z",
}


def vector(path, filled):
    paint = ('android:fillColor="#000000"' if filled else
             'android:fillColor="#00000000"\n        android:strokeColor="#000000"\n        android:strokeLineCap="round"\n'
             '        android:strokeLineJoin="round"\n        android:strokeWidth="2"')
    return ('<?xml version="1.0" encoding="utf-8"?>\n<!-- Icone proprio, gerado por tools/gen_icons.py -->\n'
            '<vector xmlns:android="http://schemas.android.com/apk/res/android"\n    android:width="24dp"\n    android:height="24dp"\n'
            '    android:viewportWidth="24"\n    android:viewportHeight="24">\n    <path\n'
            f'        android:pathData="{path}"\n        {paint} />\n</vector>\n')


out = Path(sys.argv[1])
n = 0
for name, p in STROKE.items():
    (out / f"ic_{name}.xml").write_text(vector(p, False), encoding="utf-8"); n += 1
for name, p in FILL.items():
    (out / f"ic_{name}.xml").write_text(vector(p, True), encoding="utf-8"); n += 1
print(n, "icones ->", out)
