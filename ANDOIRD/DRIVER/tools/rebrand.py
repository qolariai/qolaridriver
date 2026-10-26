# -*- coding: utf-8 -*-
# Pass 1 — manifest + network security + API keys + brand strings
import os, re

ROOT = r"C:\xampp\htdocs\QOLARI\PROJETOS OFICIAIS\QOLARI DRIVER\DRIVER\decoded"
OLD_PKG = "com.ubercab.driver"
NEW_PKG = "com.qolari.driver"

# ---------- 1. AndroidManifest ----------
mp = os.path.join(ROOT, "AndroidManifest.xml")
m = open(mp, encoding="utf-8").read()
m = m.replace(' android:requiredSplitTypes="base__abi,base__density"', '')
m = m.replace(' android:splitTypes=""', '')
m = m.replace(' xmlns:dist="http://schemas.android.com/apk/distribution"', '')
for md in ['com.android.vending.splits.required', 'com.android.stamp.source',
           'com.android.stamp.type', 'com.android.vending.splits',
           'com.android.vending.derived.apk.id']:
    m = re.sub(r'\s*<meta-data android:name="%s"[^>]*/>' % re.escape(md), '', m)
m = re.sub(r'\s*<package android:name="com\.ubercab\.rider[^"]*"/>', '', m)
m = m.replace(OLD_PKG, NEW_PKG)
m = re.sub(r'(android:name="com\.crashlytics\.ApiKey" android:value=")[^"]*"',
           r'\g<1>0000000000000000000000000000000000000000"', m)
m = m.replace('<application android:allowBackup',
              '<application android:usesCleartextTraffic="true" android:allowBackup')
open(mp, "w", encoding="utf-8").write(m)
print("[manifest] done")

# ---------- 2. cleartext ----------
nsc = os.path.join(ROOT, "res", "xml", "network_security_config.xml")
s = open(nsc, encoding="utf-8").read()
s = s.replace('<base-config>', '<base-config cleartextTrafficPermitted="true">')
open(nsc, "w", encoding="utf-8").write(s)
print("[nsc] done")

# ---------- 3. API keys + brand in strings.xml (all locales) ----------
KEY_PLACEHOLDERS = {
    'google_api_key': 'AIzaSyAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA',
    'google_crash_reporting_api_key': 'AIzaSyAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA',
    'maps_api_key': 'AIzaSyAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA',
    'google_app_id': '1:000000000000:android:0000000000000000',
    'gcm_defaultSenderId': '000000000000',
    'ub__config_google_senderid': '000000000000',
    'project_id': 'qolari-driver-dev',
    'google_storage_bucket': 'qolari-driver-dev.appspot.com',
    'firebase_database_url': 'https://qolari-driver-dev.firebaseio.com',
    'default_web_client_id': '000000000000-placeholder.apps.googleusercontent.com',
    'default_google_web_client_id': '000000000000-placeholder.apps.googleusercontent.com',
    'ub__facebook_app_id': '0000000000000000',
    'ub__payment_braintree_tokenization_key_production': 'sandbox_00000000_0000000000000000',
    'ub__payment_braintree_tokenization_key_sandbox':   'sandbox_00000000_0000000000000000',
}
def brandify(t):
    t = re.sub(r'\bUBER\b', 'QOLARI', t)
    t = re.sub(r'\bUber\b', 'Qolari', t)
    t = re.sub(r'(?<![\w.])uber(?=\.| )', 'qolari', t)
    return t

nstr = 0
resdir = os.path.join(ROOT, "res")
for d in os.listdir(resdir):
    p = os.path.join(resdir, d, "strings.xml")
    if not os.path.isfile(p):
        continue
    orig = open(p, encoding="utf-8").read()
    t = orig
    for k, pv in KEY_PLACEHOLDERS.items():
        t = re.sub(r'(<string name="%s"[^>]*>)[^<]*' % re.escape(k),
                   lambda mm: mm.group(1) + pv, t)
    t = brandify(t)          # whole file: resource names can't contain Uber/./caps
    if t != orig:
        open(p, "w", encoding="utf-8").write(t)
        nstr += 1
print("[strings]", nstr, "files")
