# -*- coding: utf-8 -*-
# Revert brand renaming inside *internal resource references* that live in
# text nodes:  @style/Qolari.* -> @style/Uber.*   fonts/Qolari* -> fonts/Uber*
import os, re

ROOT = r"C:\xampp\htdocs\QOLARI\PROJETOS OFICIAIS\QOLARI DRIVER\DRIVER\decoded"
re_text = re.compile(r'>([^<]+)<')

def fix(t):
    if t.lstrip().startswith(('@', '?')):          # resource reference
        return t.replace('Qolari', 'Uber').replace('QOLARI', 'UBER') \
                .replace('qolari', 'uber')
    if 'fonts/Qolari' in t or 'fonts/qolari' in t:  # font asset paths
        return t.replace('fonts/Qolari', 'fonts/Uber') \
                .replace('fonts/qolari', 'fonts/uber')
    return t

changed = 0
for dp, _, fns in os.walk(os.path.join(ROOT, 'res')):
    for fn in fns:
        if not fn.endswith('.xml'):
            continue
        p = os.path.join(dp, fn)
        try:
            s = open(p, encoding='utf-8').read()
        except Exception:
            continue
        ns = re_text.sub(lambda m: '>' + fix(m.group(1)) + '<', s)
        if ns != s:
            open(p, 'w', encoding='utf-8').write(ns)
            changed += 1
            print('  fixed', os.path.relpath(p, ROOT))
print('DONE. files:', changed)
