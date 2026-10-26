# -*- coding: utf-8 -*-
"""Captura de um ecra da Uber Lite (so leitura): screencap + uiautomator dump + linha em travessia.csv.
Uso: python spec_tools_cap.py <nome> [--tap "texto" | --xy X Y | --back] [--scroll]
Nao escreve texto nem aceita nada; so toca no que for indicado e regista sempre o antes."""
import csv, subprocess, sys, time
from pathlib import Path

S = "AQCK024C17020494"
ROOT = Path(__file__).resolve().parent / "ux_capture"
adb = lambda *a, **k: subprocess.run(["adb", "-s", S, *a], capture_output=True, **k)


def shot(name):
    # A Lite desenha o conteudo numa WebView: a arvore de acessibilidade so aparece depois de um instante, por isso
    # tira-se o dump ate 3 vezes e fica o que tiver mais texto.
    time.sleep(3.5)
    (ROOT / f"{name}.png").write_bytes(adb("exec-out", "screencap", "-p").stdout)
    xml = b""
    for _ in range(3):
        adb("shell", "rm", "-f", "/sdcard/ui.xml")
        adb("shell", "uiautomator", "dump", "/sdcard/ui.xml")
        cur = adb("shell", "cat", "/sdcard/ui.xml").stdout
        if len(cur) > len(xml):
            xml = cur
        if b"text=" in xml and xml.count(b'text="') > 3:
            break
        time.sleep(1.5)
    import re as _re   # dados pessoais: o numero de telefone pre-preenchido nao fica nos dumps
    xml = _re.sub(rb"9\d{8}", b"9XXXXXXXX", xml)
    (ROOT / "dumps" / f"{name}.xml").write_bytes(xml)
    return xml.decode("utf-8", "replace")


def log(name, action, note=""):
    p = ROOT / "travessia.csv"
    new = not p.exists()
    with p.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["captura", "versao_da_app", "hora", "acao", "nota"])
        w.writerow([name, "1.248.10001", time.strftime("%H:%M:%S"), action, note])


def find(xml, text):
    import re
    for m in re.finditer(r'(?:text|content-desc)="([^"]*)"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', xml):
        if m.group(1) == text:
            return (int(m.group(2)) + int(m.group(4))) // 2, (int(m.group(3)) + int(m.group(5))) // 2
    return None


def in_lite():
    out = adb("shell", "dumpsys", "window").stdout.decode("utf-8", "replace")
    return any("com.ubercab.uberlite" in l for l in out.splitlines() if "mCurrentFocus" in l)


if __name__ == "__main__":
    a = sys.argv[1:]
    if not in_lite():     # nunca captura nem toca noutra app
        print("A Lite nao esta em primeiro plano: nada feito."); sys.exit(2)
    name = a[0]
    xml = shot(name)
    texts = []
    import re
    for m in re.finditer(r'text="([^"]+)"', xml):
        texts.append(m.group(1))
    print(name, "|", " / ".join(texts[:12]).encode("ascii", "replace").decode())
    act = "captura"
    if "--scroll" in a:
        adb("shell", "input", "swipe", "640", "2500", "640", "900", "400")
        time.sleep(1); shot(name + "_s1"); act = "captura+scroll"
        adb("shell", "input", "swipe", "640", "900", "640", "2500", "400")
    if "--tap" in a:
        t = a[a.index("--tap") + 1]
        xy = find(xml, t)
        if xy:
            adb("shell", "input", "tap", str(xy[0]), str(xy[1])); act = f"toque '{t}'"
        else:
            act = f"toque '{t}' NAO ENCONTRADO"
    elif "--xy" in a:
        i = a.index("--xy"); adb("shell", "input", "tap", a[i + 1], a[i + 2]); act = f"toque {a[i+1]},{a[i+2]}"
    elif "--back" in a:
        adb("shell", "input", "keyevent", "KEYCODE_BACK"); act = "voltar"
    log(name, act)
    print("->", act)
