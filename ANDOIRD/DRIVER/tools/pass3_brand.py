# -*- coding: utf-8 -*-
# Pass 3 — remove remaining *visible* "Uber" in locale string values
# and set app display name to "Qolari Drive".
# Only text nodes (>...<) are touched; name= attributes / ids stay intact.
import os, re, sys

ROOT = r"C:\xampp\htdocs\QOLARI\PROJETOS OFICIAIS\QOLARI DRIVER\DRIVER\decoded"
APP_NAME = "Qolari Drive"

# brand transliterations -> Qolari  (German "Über/über" intentionally excluded:
# it is a normal word, not the brand)
PAIRS = [
    (re.compile(r'Uber'),        'Qolari'),
    (re.compile(r'UBER'),        'QOLARI'),
    (re.compile(r'\buber\b'),    'qolari'),
    (re.compile(r'أوبر'),        'Qolari'),   # ar
    (re.compile(r'أوبَر'),       'Qolari'),
    (re.compile(r'אובר'),        'Qolari'),   # he
    (re.compile(r'优步'),         'Qolari'),   # zh-CN
    (re.compile(r'優步'),         'Qolari'),   # zh-TW
    (re.compile(r'ウーバー'),      'Qolari'),   # ja
    (re.compile(r'우버'),         'Qolari'),   # ko
    (re.compile(r'Убер'),        'Qolari'),   # ru/cyrillic
    (re.compile(r'УБЕР'),        'QOLARI'),
    (re.compile(r'\bубер\b'),    'qolari'),
    (re.compile(r'ऊबर'),         'Qolari'),   # hi
    (re.compile(r'উবার'),        'Qolari'),   # bn
    (re.compile(r'ਉਬਰ'),         'Qolari'),   # pa
    (re.compile(r'ઉબર'),         'Qolari'),   # gu
    (re.compile(r'उबर'),         'Qolari'),   # mr
    (re.compile(r'ஊபர்'),        'Qolari'),   # ta
    (re.compile(r'ఉబర్'),        'Qolari'),   # te
    (re.compile(r'ಉಬರ್'),        'Qolari'),   # kn
    (re.compile(r'ഉബർ'),         'Qolari'),   # ml
    (re.compile(r'อูเบอร์'),      'Qolari'),   # th
    (re.compile(r'Ούμπερ'),      'Qolari'),   # el
    (re.compile(r'უბერ'),        'Qolari'),   # ka
    (re.compile(r'Ուբեր'),       'Qolari'),   # hy
    (re.compile(r'ኡበር'),         'Qolari'),   # am
    (re.compile(r'អ៊ូប៊ឺរ'),       'Qolari'),   # km
    (re.compile(r'အူဘာ'),        'Qolari'),   # my
]

re_text = re.compile(r'>([^<]+)<')
re_appname = re.compile(
    r'(<string name="carbon_app_name"[^>]*>)[^<]*(</string>)')
re_lottie_nm = re.compile(r'("(?:nm|mn)":\s*")([^"]*Uber[^"]*)(")')

def fix_text(t):
    for rx, rep in PAIRS:
        t = rx.sub(rep, t)
    return t

changed_files = 0
total_subs = 0

def walk_xml(base):
    global changed_files, total_subs
    for dp, _, fns in os.walk(base):
        for fn in fns:
            if not fn.endswith('.xml'):
                continue
            p = os.path.join(dp, fn)
            try:
                s = open(p, encoding='utf-8').read()
            except Exception:
                continue
            orig = s
            s = re_text.sub(lambda m: '>' + fix_text(m.group(1)) + '<', s)
            s = re_appname.sub(lambda m: m.group(1) + APP_NAME + m.group(2), s)
            if s != orig:
                total_subs += 1
                open(p, 'w', encoding='utf-8').write(s)
                changed_files += 1
                print('  fixed', os.path.relpath(p, ROOT))

print('[res] cleaning text nodes ...')
walk_xml(os.path.join(ROOT, 'res'))

# lottie/json cosmetic "nm" names under assets
print('[assets] lottie names ...')
adir = os.path.join(ROOT, 'assets')
for dp, _, fns in os.walk(adir):
    for fn in fns:
        if not fn.endswith('.json'):
            continue
        p = os.path.join(dp, fn)
        try:
            s = open(p, encoding='utf-8').read()
        except Exception:
            continue
        ns = re_lottie_nm.sub(lambda m: m.group(1) +
                              m.group(2).replace('Uber', 'Qolari') + m.group(3), s)
        if ns != s:
            open(p, 'w', encoding='utf-8').write(ns)
            changed_files += 1
            print('  fixed', os.path.relpath(p, ROOT))

# apktool.yml apkFileName
yml = os.path.join(ROOT, 'apktool.yml')
s = open(yml, encoding='utf-8').read()
s = s.replace('apkFileName: uber-driver-4.599.10004.apk',
              'apkFileName: qolari-drive.apk')
open(yml, 'w', encoding='utf-8').write(s)

print('DONE. files changed:', changed_files)
