# -*- coding: utf-8 -*-
"""Ficheiros smali com caminho >= 260 caracteres que o rebrand da Driver nao conseguiu abrir.

No Windows o apktool nao le esses ficheiros (as classes nao entram no dex -> NoClassDefFoundError) e o
DRIVER/tools/deep_rename.py tambem nao os editou (ficaram com com/uber, com/ubercab por dentro).

    python fix_long_smali.py <raiz-decoded> scan|apply

`apply` aplica a esses ficheiros as mesmas regras do deep_rename (pacotes -> com.qolari, 'ubercab' ->
'qolari', dominios da Uber/terceiros -> backend local) com o endereco atual do backend da Driver.
Para os montar: `subst X: <raiz-decoded>` e `java -jar apktool.jar b X:\\` (caminhos ~63 caracteres mais curtos).
"""
import os, re, sys, collections
from pathlib import Path


BACKEND = "127.0.0.1:8091"
BACKEND_URL = "http://" + BACKEND
LIMIT = 250  # margem abaixo de 260

# regras copiadas de DRIVER/tools/deep_rename.py (o import executaria esse script, por isso ficam aqui)
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
re_url = re.compile(r'https?://[A-Za-z0-9.-]*' + r'(?:' + ANYDOM + r')' + BOUND)
re_host = re.compile(r'(?<![A-Za-z0-9-])(?:[A-Za-z0-9-]+\.)*(?:' + ANYDOM + r')' + BOUND)
re_pkgslash = re.compile(r'com/ubercab(?![\w/])|com/ubercab/|com/uber(?![\w/])|com/uber/')
re_pkgdot = re.compile(r'com\.ubercab(?![\w.])|com\.ubercab\.|com\.uber(?![\w.])|com\.uber\.')
re_ubercab = re.compile(r'ubercab')


def fix_pkg(m):
    s = m.group(0)
    return 'com/qolari' + ('/' if s.endswith('/') else '') if '/' in s \
        else 'com.qolari' + ('.' if s.endswith('.') else '')


def transform(txt: str) -> str:
    txt = re_url.sub(BACKEND_URL, txt)
    txt = re_host.sub(BACKEND, txt)
    txt = re_pkgdot.sub(fix_pkg, txt)
    txt = re_pkgslash.sub(fix_pkg, txt)
    txt = re_ubercab.sub('qolari', txt)
    return txt.replace("192.168.1.204", BACKEND)


def main():
    root, mode = os.path.abspath(sys.argv[1]), sys.argv[2]
    stats = collections.Counter()
    for d in sorted(x for x in os.listdir(root) if x.startswith("smali")):
        for dp, dn, fn in os.walk("\\\\?\\" + os.path.join(root, d)):
            for f in fn:
                p = os.path.join(dp, f)
                if len(p) - 4 < LIMIT:
                    continue
                stats["longos"] += 1
                stats[d] += 1
                txt = open(p, encoding="utf-8").read()
                new = transform(txt)
                if new != txt:
                    stats["alterados"] += 1
                    if mode == "apply":
                        open(p, "w", encoding="utf-8", newline="").write(new)
                elif mode == "apply":
                    os.utime(p)  # para o apktool remontar a pasta
    print(dict(stats))


if __name__ == "__main__":
    main()
