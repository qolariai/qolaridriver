# -*- coding: utf-8 -*-
"""P2 - Extracao da especificacao estatica de UI/UX a partir de uma pasta apktool (read-only sobre o original).

Uso:
    python extract_spec.py --decoded <pasta_apktool> --out <pasta_ui_spec> [--apk <base.apk>]

Nao depende da Driver: recebe a arvore descompilada e a pasta de saida (reutilizavel para Rider e Fleet).
Le: AndroidManifest.xml, apktool.yml, res/*, assets/ (so lista).
Escreve em --out: meta.json, manifest.json, values/*.json (todos os values*), design_tokens.json,
layouts/, drawables/ (XML + raster), anim/, animator/, interpolator/, color/, menu/, xml/,
fonts.json (so lista; a fonte nunca e copiada), assets_index.json, inventory.json.
Os ficheiros copiados sao REFERENCIA de fidelidade: nunca entram na app nova.
"""
import argparse
import hashlib
import json
import re
import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ANDROID = "{http://schemas.android.com/apk/res/android}"
RASTER = {".png", ".webp", ".jpg", ".jpeg", ".gif"}


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_yml_value(yml, key):
    m = re.search(r"^\s*%s:\s*(.+)$" % re.escape(key), yml, re.M)
    return m.group(1).strip().strip("'\"") if m else None


def parse_manifest(decoded):
    root = ET.parse(decoded / "AndroidManifest.xml").getroot()
    app = root.find("application")
    out = {"package": root.get("package"), "permissions": [], "uses_features": [], "activities": [],
           "services": [], "receivers": [], "providers": [], "deeplinks": [],
           "application_name": app.get(ANDROID + "name") if app is not None else None}
    for p in root.findall("uses-permission"):
        out["permissions"].append(p.get(ANDROID + "name"))
    for p in root.findall("uses-feature"):
        out["uses_features"].append({"name": p.get(ANDROID + "name"), "required": p.get(ANDROID + "required")})
    if app is None:
        return out
    for kind, key in (("activity", "activities"), ("service", "services"), ("receiver", "receivers"), ("provider", "providers")):
        for el in app.findall(kind):
            item = {"name": el.get(ANDROID + "name"), "exported": el.get(ANDROID + "exported"),
                    "launchMode": el.get(ANDROID + "launchMode"),
                    "screenOrientation": el.get(ANDROID + "screenOrientation"),
                    "authorities": el.get(ANDROID + "authorities"), "intent_filters": []}
            for f in el.findall("intent-filter"):
                fil = {"actions": [x.get(ANDROID + "name") for x in f.findall("action")],
                       "categories": [x.get(ANDROID + "name") for x in f.findall("category")],
                       "data": [{k.split("}")[-1]: v for k, v in d.attrib.items()} for d in f.findall("data")]}
                item["intent_filters"].append(fil)
                for d in fil["data"]:
                    if d.get("scheme") or d.get("host"):
                        out["deeplinks"].append({"component": item["name"], **d})
            out[key].append(item)
    return out


def parse_values_file(path):
    """Devolve {tipo: {nome: valor}} para strings, cores, dimens, ints, bools, arrays, plurals e styles."""
    out = {}
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError:
        return out
    for el in root:
        name = el.get("name")
        if not name:
            continue
        tag = el.tag
        if tag in ("string", "color", "dimen", "integer", "bool", "item", "fraction", "id"):
            out.setdefault(tag, {})[name] = (el.text or "").strip()
        elif tag in ("string-array", "array", "integer-array"):
            out.setdefault("arrays", {})[name] = [(i.text or "").strip() for i in el.findall("item")]
        elif tag == "plurals":
            out.setdefault("plurals", {})[name] = {i.get("quantity"): (i.text or "").strip() for i in el.findall("item")}
        elif tag == "style":
            out.setdefault("styles", {})[name] = {"parent": el.get("parent"),
                                                  "items": {i.get("name"): (i.text or "").strip() for i in el.findall("item")}}
        elif tag == "attr":
            out.setdefault("attrs", {})[name] = el.get("format") or ""
    return out


def extract_values(res, out):
    inv = {}
    for d in sorted(p for p in res.iterdir() if p.is_dir() and p.name.startswith("values")):
        merged = {}
        for f in sorted(d.glob("*.xml")):
            for tipo, items in parse_values_file(f).items():
                merged.setdefault(f.stem, {}).setdefault(tipo, {}).update(items)
        if merged:
            write_json(out / "values" / (d.name + ".json"), merged)
            inv[d.name] = sum(len(v) for ft in merged.values() for v in ft.values())
    return inv


def design_tokens(res):
    def collect(dirname, tipo):
        found = {}
        d = res / dirname
        if d.is_dir():
            for f in d.glob("*.xml"):
                found.update(parse_values_file(f).get(tipo, {}))
        return found
    base_styles = {}
    for f in (res / "values").glob("*.xml"):
        base_styles.update(parse_values_file(f).get("styles", {}))
    themes = {k: v for k, v in base_styles.items() if k.startswith("Theme") or "Theme" in k}
    return {"colors_light": collect("values", "color"), "colors_dark": collect("values-night", "color"),
            "dimens": collect("values", "dimen"), "themes": themes}


def copy_tree(res, out, name_prefix, out_name, exts=None):
    n = 0
    for d in sorted(p for p in res.iterdir() if p.is_dir() and p.name.startswith(name_prefix)):
        for f in sorted(d.iterdir()):
            if not f.is_file():
                continue
            if exts is not None and f.suffix.lower() not in exts:
                continue
            dst = out / out_name / d.name
            dst.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, dst / f.name)
            n += 1
    return n


def list_fonts(res):
    fonts = []
    d = res / "font"
    if d.is_dir():
        for f in sorted(d.iterdir()):
            fonts.append({"file": f.name, "bytes": f.stat().st_size,
                          "nota": "so listada; a fonte nao e copiada (proprietaria)"})
    return fonts


def assets_index(decoded):
    out = []
    a = decoded / "assets"
    if a.is_dir():
        for f in sorted(a.rglob("*")):
            if f.is_file():
                out.append({"path": f.relative_to(a).as_posix(), "bytes": f.stat().st_size})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--decoded", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--apk", type=Path, default=None, help="APK de origem (para registar o sha256)")
    args = ap.parse_args()
    dec, out = args.decoded.resolve(), args.out.resolve()
    res = dec / "res"
    if not (dec / "AndroidManifest.xml").exists() or not res.is_dir():
        print("pasta apktool invalida:", dec)
        return 1
    out.mkdir(parents=True, exist_ok=True)

    yml = (dec / "apktool.yml").read_text(encoding="utf-8") if (dec / "apktool.yml").exists() else ""
    meta = {"decoded": str(dec), "apk": str(args.apk) if args.apk else None,
            "apk_sha256": sha256(args.apk) if args.apk and args.apk.exists() else None,
            "versionName": read_yml_value(yml, "versionName"), "versionCode": read_yml_value(yml, "versionCode"),
            "minSdk": read_yml_value(yml, "minSdkVersion"), "targetSdk": read_yml_value(yml, "targetSdkVersion")}
    write_json(out / "meta.json", meta)
    print("meta:", meta["versionName"], meta["versionCode"])

    manifest = parse_manifest(dec)
    write_json(out / "manifest.json", manifest)
    print("manifest:", len(manifest["activities"]), "activities,", len(manifest["permissions"]), "permissoes,", len(manifest["deeplinks"]), "deeplinks")

    values_inv = extract_values(res, out)
    print("values:", len(values_inv), "pastas")
    write_json(out / "design_tokens.json", design_tokens(res))

    inv = {"layouts": copy_tree(res, out, "layout", "layouts", {".xml"}),
           "drawables_xml": copy_tree(res, out, "drawable", "drawables", {".xml"}),
           "drawables_raster": copy_tree(res, out, "drawable", "drawables", RASTER),
           "mipmaps": copy_tree(res, out, "mipmap", "mipmaps", None),
           "anim": copy_tree(res, out, "anim", "anim", {".xml"}),
           "animator": copy_tree(res, out, "animator", "animator", {".xml"}),
           "interpolator": copy_tree(res, out, "interpolator", "interpolator", {".xml"}),
           "color_selectors": copy_tree(res, out, "color", "color", {".xml"}),
           "menu": copy_tree(res, out, "menu", "menu", {".xml"}),
           "xml": copy_tree(res, out, "xml", "xml", {".xml"}),
           "navigation": copy_tree(res, out, "navigation", "navigation", {".xml"}),
           "values_entradas": values_inv}
    fonts = list_fonts(res)
    write_json(out / "fonts.json", fonts)
    inv["fonts_listadas"] = len(fonts)
    assets = assets_index(dec)
    write_json(out / "assets_index.json", assets)
    inv["assets_listados"] = len(assets)
    write_json(out / "inventory.json", inv)
    for k, v in inv.items():
        if k != "values_entradas":
            print(f"  {k}: {v}")
    print("done ->", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
