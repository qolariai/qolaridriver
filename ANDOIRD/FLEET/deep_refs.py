#!/usr/bin/env python3
# Deep rename: neutralize 3rd-party credentials/endpoints (local learning use)
import os, re

ROOT = r"qolarifleet_src"
BACKEND = "192.168.1.204:3000"

# ---- 1) credentials -> valid-format placeholders ----
RSA_PLACEHOLDER = ("MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAqSw0oRAPtq99mTCaj5B/jQKgaZ8wUN1BeoMpCrouOjFx"
                   "aTQH7oMd26OJkeYX0ex8n/QwIe/hmJGsR7K9MAqIS+g+Nemt6SRnLq5zrYoKewcDLkIFNlKd6IdTuEQ9CMxx5s7Ugc"
                   "1t1dpNYmH3fF+0Q1lZXRbrD4tXaVzsBtIj4tXo1BjTOMeMO2XRJ6mnVAA3ENDjwCdLjKvzFqdn7AWCS/1KA0qd2MNO"
                   "ztm8XtKbl7T/Jbc43GNUlrMckjQB/duYyjjXA0NpWuVWAkx5N2zESpDKalDoR+lTZu+ghQENRxFg/KHdGXzLhjfebS+n"
                   "VsUbxmZ/eFDfzkfO7J5wjTAF+QIDAQAB")

EXACT = {
    'AIzaSyCXaCHZYOnYtrfwsHy8slkK-jXlRGUMnAE': 'AIzaSy00000000000000000000000000000000',
    'AIzaSyCjC6UUy1kPNoIFVx_-cYj19YsrK6YqSyQ': 'AIzaSy00000000000000000000000000000000',
    'c539e979e5ca22fe420a5e6c91687d3b22b04e50': '0000000000000000000000000000000000000000',
    '1:1002470700242:android:93a7a24fc9406620e2290b': '1:000000000000:android:0000000000000000000000',
    '1002470700242': '000000000000',
    '89939265457-enilmfbsacgcj2b7qq3sc7jc51u5b3ge': '000000000000-00000000000000000000000000000000',
    'qolari-fleet-19b91': 'qolari-fleet-local',
    'production_s4sq9dp3_27m9gvdh2fdm8t4x': 'production_00000000_0000000000000000',
    'sandbox_674xh35c_rcrbx3drr2p62gdp': 'sandbox_00000000_0000000000000000',
}
RE_RSA = re.compile(r'MIIB[A-Za-z0-9+/=]{200,}')

# ---- 2) third-party service endpoints -> local backend ----
TP_HOSTS = (r'(?:[a-zA-Z0-9*-]+\.)*(?:'
            r'app-measurement\.com'
            r'|googleadservices\.com'
            r'|googlesyndication\.com'
            r'|googleapis\.com'
            r'|grab\.com'
            r'|ifood\.com\.br'
            r'|fleetmatch\.com'
            r'|riamoneytransfer\.com'
            r'|tesla\.com'
            r'|amazon\.com'
            r'|firebase\.google\.com'
            r'|accounts\.google\.com'
            r'|earth\.google\.com'
            r')')
RE_TP_SCHEME = re.compile(r'https?://(?:' + TP_HOSTS + r')')
RE_TP_HOST = re.compile(TP_HOSTS)

# ---- 3) residual brand prefix in resource names ----
BRAND_REPS = [('ub__', 'qq__')]

stats = {'files': 0, 'creds': 0, 'hosts': 0}

def xp(p):
    p = os.path.abspath(p)
    if len(p) > 240 and not p.startswith('\\\\?\\'):
        return '\\\\?\\' + p
    return p

def transform(s):
    for a, b in EXACT.items():
        if a in s:
            stats['creds'] += s.count(a)
            s = s.replace(a, b)
    s = RE_RSA.sub(RSA_PLACEHOLDER, s)
    n = len(RE_TP_SCHEME.findall(s))
    s = RE_TP_SCHEME.sub('http://' + BACKEND, s)
    n += len(RE_TP_HOST.findall(s))
    s = RE_TP_HOST.sub(BACKEND, s)
    stats['hosts'] += n
    for a, b in BRAND_REPS:
        s = s.replace(a, b)
    return s

for dp, dn, fn in os.walk(ROOT):
    if '\\build' in dp or '/build' in dp:
        continue
    for f in fn:
        p = os.path.join(dp, f)
        try:
            raw = open(xp(p), 'rb').read()
            s = raw.decode('utf-8')
        except (UnicodeDecodeError, OSError):
            continue
        ns = transform(s)
        if ns != s:
            open(xp(p), 'w', encoding='utf-8').write(ns)
            stats['files'] += 1

# ---- 4) manifest: strip store/bundle provenance meta-data ----
mpath = os.path.join(ROOT, 'AndroidManifest.xml')
m = open(mpath, encoding='utf-8').read()
for name in ['com.android.vending.splits.required', 'com.android.stamp.source',
             'com.android.stamp.type', 'com.android.vending.derived.apk.id',
             'delivery_metrics_exported_to_big_query_enabled']:
    m = re.sub(r'\s*<meta-data android:name="' + re.escape(name) + r'"[^/]*/>', '', m)
open(mpath, 'w', encoding='utf-8').write(m)

print('files modified :', stats['files'])
print('credentials hit:', stats['creds'])
print('3rd-party hosts:', stats['hosts'])
