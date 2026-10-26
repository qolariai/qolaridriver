# -*- coding: utf-8 -*-
# Pass 2 — deep rename + third-party neutralization
#  com.ubercab.* / com.uber.*  -> com.qolari.*   (smali dirs + all text refs)
#  vendor domains (fb/paypal/twilio/braintree/firebase-gapis/cdn/analytics) -> 192.168.1.204
#  leftover uber domains in manifest + skipped locale strings -> backend / qolari
import os, re, shutil

ROOT = r"C:\xampp\htdocs\QOLARI\PROJETOS OFICIAIS\QOLARI DRIVER\DRIVER\decoded"
BACKEND = "192.168.1.204"
BACKEND_URL = "http://192.168.1.204"
BRAND_DOM = "qolari.com"

# ---- domains to dead-end into the local backend ----
KILL_TLDS = (r'(?:facebook\.com|facebook\.net|fbcdn\.net|fb\.me|'
             r'twilio\.com|paypal\.com|paypalobjects\.com|paypal\.me|'
             r'braintreegateway\.com|braintree-api\.com|adyen\.com|'
             r'crashlytics\.com|app-measurement\.com|google-analytics\.com|'
             r'doubleclick\.net|googletagmanager\.com|'
             r'appsflyer\.com|appsflyersdk\.com|onelink\.me|app\.link|'
             r'adjust\.com|adjust\.io|sentry\.io|amplitude\.com|mixpanel\.com|'
             r'veriff\.com|veriff\.me|jumio\.com|jumio\.ai|hyperwallet\.com|'
             r'nauto\.com|ubercarshare\.com|uber\.org|uber\.app|'
             r'cloudfront\.net|stripe\.com|onesignal\.com|datadoghq\.com|'
             r'segment\.com|segment\.io|braze\.com|intercom\.io|sng\.link)')
FIREBASE_HOSTS = (r'(?:firebaseinstallations|firebaseremoteconfig|'
                  r'firebaseremoteconfigrealtime|firebaselogging|fcm|'
                  r'firebasedynamiclinks|firebaseinappmessaging|'
                  r'firebasedatabase)\.googleapis\.com|'
                  r'(?:[a-zA-Z0-9-]+\.)*firebaseio\.com|'
                  r'(?:[a-zA-Z0-9-]+\.)*firebasedatabase\.app|'
                  r'(?:[a-zA-Z0-9-]+\.)*firebase\.com')
UBER_LEFTOVER = (r'(?:uber\.com|uberinternal\.com|ubereats\.com|geixahba\.com|'
                 r'shaipeeg\.net|oojoovae\.org|ooshahwa\.biz|naevooda\.co)')
ANYDOM = KILL_TLDS[:-1] + '|' + FIREBASE_HOSTS + '|' + UBER_LEFTOVER[3:]
BOUND = r'(?![a-zA-Z0-9-]|\.[a-zA-Z0-9-])'
re_url  = re.compile(r'https?://[A-Za-z0-9.-]*' + r'(?:' + ANYDOM + r')' + BOUND)
re_host = re.compile(r'(?<![A-Za-z0-9-])(?:[A-Za-z0-9-]+\.)*(?:' + ANYDOM + r')' + BOUND)
re_wild = re.compile(r'\*\.' + UBER_LEFTOVER)   # manifest app-link wildcards

re_pkgslash = re.compile(r'com/ubercab(?![\w/])|com/ubercab/|com/uber(?![\w/])|com/uber/')
re_pkgdot   = re.compile(r'com\.ubercab(?![\w.])|com\.ubercab\.|com\.uber(?![\w.])|com\.uber\.')
re_ubercab  = re.compile(r'ubercab')

def fix_pkg(m):
    s = m.group(0)
    return 'com/qolari' + ('/' if s.endswith('/') else '') if '/' in s \
           else 'com.qolari' + ('.' if s.endswith('.') else '')

def is_text(path):
    try:
        with open(path, 'rb') as f:
            b = f.read()
        if b'\x00' in b[:8192]:
            return False
        b.decode('utf-8')          # must be fully valid utf-8
        return True
    except Exception:
        return False

re_val = re.compile(r'>([^<>]+)<')
def brandify(v):
    v = re.sub(r'\bUBER\b', 'QOLARI', v)
    v = re.sub(r'\bUber\b', 'Qolari', v)
    v = re.sub(r'(?<![\w.])uber(?=\.| )', 'qolari', v)
    return v

stats = {"files":0,"dom":0,"pkg":0}
for dirpath, _, files in os.walk(ROOT):
    for fn in files:
        p = os.path.join(dirpath, fn)
        rel = os.path.relpath(p, ROOT).replace('\\','/')
        if rel.startswith('build/'):      # stale artifacts, rebuilt anyway
            continue
        if not is_text(p):
            continue
        txt = open(p, encoding='utf-8').read()
        orig = txt
        # 0) wildcard uber hosts -> brand domain (manifest app-links)
        txt = re_wild.sub('*.' + BRAND_DOM, txt)
        # 1) endpoints -> backend
        txt = re_url.sub(BACKEND_URL, txt)
        txt = re_host.sub(BACKEND, txt)
        stats["dom"] += 1
        # 2) package renames (dot + slash)
        txt = re_pkgdot.sub(fix_pkg, txt)
        txt = re_pkgslash.sub(fix_pkg, txt)
        # 3) leftover 'ubercab' tokens (schemes, names)
        txt = re_ubercab.sub('qolari', txt)
        # 4) strings.xml: brandify values (idempotent, catches skipped locales)
        if rel.endswith('strings.xml') and '/values' in '/' + rel:
            txt = re_val.sub(lambda m: '>'+brandify(m.group(1))+'<', txt)
        if txt != orig:
            open(p, 'w', encoding='utf-8').write(txt)
            stats["files"] += 1

# ---- PHASE B: move smali/unknown package dirs ----
moved = 0
for d in os.listdir(ROOT):
    comdir = os.path.join(ROOT, d, 'com')
    if not (d.startswith('smali') and os.path.isdir(comdir)):
        continue
    dst = os.path.join(comdir, 'qolari')
    for src in ('uber', 'ubercab'):
        sp = os.path.join(comdir, src)
        if os.path.isdir(sp):
            os.makedirs(dst, exist_ok=True)
            for item in os.listdir(sp):
                shutil.move(os.path.join(sp, item), os.path.join(dst, item))
            os.rmdir(sp); moved += 1
# unknown/com blobs
ucom = os.path.join(ROOT, 'unknown', 'com')
if os.path.isdir(ucom):
    dst = os.path.join(ucom, 'qolari'); os.makedirs(dst, exist_ok=True)
    for src in ('uber', 'ubercab'):
        sp = os.path.join(ucom, src)
        if os.path.isdir(sp):
            for item in os.listdir(sp):
                shutil.move(os.path.join(sp, item), os.path.join(dst, item))
            os.rmdir(sp); moved += 1
print("moved package roots:", moved)
print("DONE:", stats)
