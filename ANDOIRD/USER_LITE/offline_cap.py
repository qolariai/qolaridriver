# -*- coding: utf-8 -*-
"""Estados offline da Lite (so leitura): corta Wi-Fi e dados ~2 min, captura, e REPOE sempre (try/finally)."""
import sys, time
sys.path.insert(0, ".")
import spec_tools_cap as c
import menu_loop_lib as m

def sh(*a): return c.adb("shell", *a).stdout.decode("utf-8", "replace").strip()
wifi, data = sh("settings", "get", "global", "wifi_on"), sh("settings", "get", "global", "mobile_data")
try:
    assert m.go_home(), "nao cheguei ao inicio"
    sh("svc", "wifi", "disable"); sh("svc", "data", "disable"); time.sleep(8)
    for name, act in [("050_offline_inicio", None), ("051_offline_pesquisa", ("tap", 357, 1169)), ("052_offline_apos_voltar", ("tap", 119, 238))]:
        if act:
            if not c.in_lite(): print("Lite perdeu o foco"); break
            sh("input", "tap", str(act[1]), str(act[2])); time.sleep(3)
        if not c.in_lite(): print("Lite perdeu o foco"); break
        xml = c.shot(name); c.log(name, "offline")
        import re
        print(name, "|", " / ".join(re.findall(r'text="([^"]+)"', xml.decode() if isinstance(xml, bytes) else xml)[:8]).encode("ascii", "replace").decode())
finally:
    if wifi == "1": sh("svc", "wifi", "enable")
    if data == "1": sh("svc", "data", "enable")
    time.sleep(8)
    print("repostos: wifi=", sh("settings", "get", "global", "wifi_on"), "dados=", sh("settings", "get", "global", "mobile_data"))
