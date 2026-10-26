# -*- coding: utf-8 -*-
"""Icones proprios dos 5 separadores: contorno (inativo) e preenchido (ativo), como na original (capturas 000/010-013).
Uso: python gen_tabs.py <pasta res/drawable>. Gera ic_tab_<nome>_off.xml, ic_tab_<nome>_on.xml e o seletor ic_tab_<nome>.xml."""
import sys
from pathlib import Path

HEAD = ('<?xml version="1.0" encoding="utf-8"?>\n<!-- Icone proprio, gerado por tools/gen_tabs.py -->\n'
        '<vector xmlns:android="http://schemas.android.com/apk/res/android"\n    android:width="24dp"\n    android:height="24dp"\n'
        '    android:viewportWidth="24"\n    android:viewportHeight="24">\n')


def stroke(path, width=2):
    return (f'    <path\n        android:pathData="{path}"\n        android:fillColor="#00000000"\n        android:strokeColor="#000000"\n'
            f'        android:strokeLineCap="round"\n        android:strokeLineJoin="round"\n        android:strokeWidth="{width}" />\n')


def fill(path, even_odd=False):
    ft = '        android:fillType="evenOdd"\n' if even_odd else ''
    return f'    <path\n        android:pathData="{path}"\n{ft}        android:fillColor="#000000" />\n'


TABS = {
    "home": (stroke("M4,11 L12,4 L20,11 V20 H15 V14 H9 V20 H4 Z"),
             fill("M3,11.5 L12,3.5 L21,11.5 V21 H15 V15 H9 V21 H3 Z")),
    "discover": (stroke("M17,4 L20,12 L9,20 L5,10 Z M17,4 L9,20"),
                 fill("M17.6,4.8 L20,12 L10.2,19.4 Z M16.2,3.8 L8.4,20.2 L4.4,10.6 Z")),
    "earnings": (stroke("M3,6 H21 V18 H3 Z M12,9.5 a2.5,2.5 0 1,0 0.01,0"),
                 fill("M3,5.5 H21 V18.5 H3 Z M12,9 a3,3 0 1,0 0.01,0", True)),
    "inbox": (stroke("M3,6 H21 V18 H3 Z M3,7 L12,13 L21,7"),
              fill("M3,5 H21 V19 H3 Z M3.2,6.6 L12,12.6 L20.8,6.6 V8.4 L12,14.4 L3.2,8.4 Z", True)),
    "menu": (stroke("M4,7 H20 M4,12 H20 M4,17 H20"),
             stroke("M4,7 H20 M4,12 H20 M4,17 H20", 3.2)),
}
out = Path(sys.argv[1])
for name, (off, on) in TABS.items():
    (out / f"ic_tab_{name}_off.xml").write_text(HEAD + off + "</vector>\n", encoding="utf-8")
    (out / f"ic_tab_{name}_on.xml").write_text(HEAD + on + "</vector>\n", encoding="utf-8")
    (out / f"ic_tab_{name}.xml").write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n<selector xmlns:android="http://schemas.android.com/apk/res/android">\n'
        f'    <item android:drawable="@drawable/ic_tab_{name}_on" android:state_checked="true" />\n'
        f'    <item android:drawable="@drawable/ic_tab_{name}_off" />\n</selector>\n', encoding="utf-8")
print("ok", out)
