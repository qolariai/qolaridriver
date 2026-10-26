# -*- coding: utf-8 -*-
"""Percorre os itens do menu da Lite (so leitura). Volta SEMPRE pela seta da app (nunca pelo Voltar do sistema, que
sai da Lite para a app anterior da pilha) e nunca toca em 'Encerrar sessao'."""
import re, sys, time
sys.path.insert(0, ".")
import spec_tools_cap as c

ITEMS = [("Promoções", "024_promocoes"), ("Legal", "025_legal"), ("Ajuda", "020_ajuda_completa")]


def focus():
    return c.adb("shell", "dumpsys", "window").stdout.decode("utf-8", "replace")


def in_lite():
    return c.in_lite()


def go_home():
    """Do que estiver aberto para a pagina inicial, so com a seta/X da app."""
    for _ in range(5):
        if not in_lite():
            c.adb("shell", "am", "start", "-n", "com.ubercab.uberlite/.feature.RootActivity"); time.sleep(3)
        xml = c.shot("_probe")
        if c.find(xml, "Sugestões"):
            return True
        c.adb("shell", "input", "tap", "119", "238")     # seta de voltar no canto superior esquerdo
        time.sleep(2)
        xml = c.shot("_probe")
        if c.find(xml, "Sugestões"):
            return True
        c.adb("shell", "input", "tap", "1195", "225")    # X do menu
        time.sleep(2)
    return False


for label, name in ITEMS:
    if not go_home():
        print("nao consegui voltar ao inicio antes de", label); break
    if not in_lite():
        print("A Lite perdeu o primeiro plano: paro sem tocar."); break
    c.adb("shell", "input", "tap", "1175", "240"); time.sleep(2)           # hamburguer
    xml = c.shot("_probe")
    xy = c.find(xml, label)
    if not xy:
        print("item nao visivel:", label); continue
    if not in_lite():
        print("A Lite perdeu o primeiro plano: paro sem tocar."); break
    c.adb("shell", "input", "tap", str(xy[0]), str(xy[1]))
    time.sleep(3 if "Ajuda" in label else 0)
    xml = c.shot(name); c.log(name, f"toque '{label}'")
    t = re.findall(r'text="([^"]+)"', xml)
    print(name, "|", " / ".join(t[:10]).encode("ascii", "replace").decode())
    c.adb("shell", "input", "swipe", "640", "2500", "640", "900", "400"); time.sleep(1.5)
    c.shot(name + "_s1"); c.log(name + "_s1", "scroll")
go_home()
