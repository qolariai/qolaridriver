import os, re

def xp(p):
    p = os.path.abspath(p)
    if len(p) > 240 and not p.startswith('\\\\?\\'):
        return '\\\\?\\' + p
    return p

n = 0
err = 0
for dp, dn, fn in os.walk('qolarifleet_src'):
    for f in fn:
        if not f.endswith('.smali'):
            continue
        p = os.path.join(dp, f)
        try:
            s = open(xp(p), encoding='utf-8').read()
        except Exception as e:
            err += 1
            print('ERR', p, e)
            continue
        ns = re.sub(r'(?<![/\w])const-string v', 'const-string/jumbo v', s)
        if ns != s:
            open(xp(p), 'w', encoding='utf-8').write(ns)
            n += 1
print('smali patched:', n, 'errors:', err)
