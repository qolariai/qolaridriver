# -*- coding: utf-8 -*-
"""Percorre os itens do menu da Lite (so leitura). Volta SEMPRE pela seta da app (nunca pelo Voltar do sistema, que
sai da Lite para a app anterior da pilha) e nunca toca em 'Encerrar sessao'."""
import re, sys, time
sys.path.insert(0, ".")
import spec_tools_cap as c

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


