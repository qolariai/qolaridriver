# -*- coding: utf-8 -*-
"""Login das 3 apps tal como a APK o faz (biblioteca uauth / "USL" da Uber).

O ecra de login das APKs e uma pagina servida pelo dominio auth (em producao auth.uber.com/v2), aberta
pela app numa WebView (`com.qolari.identity.api.uauth.internal.helper.USLActivity`):

    GET /v2?firstPartyClientID=..&codeChallenge=<PKCE S256>&app_url=..&isEmbedded=true&x-uber-*=..

Aqui serve-se essa pagina (replica do fluxo original: telemovel -> codigo de 4 digitos -> nome, se a
conta for nova). No fim a pagina navega para `<uauth_dl_scheme>://...?session=<id>&authCode=<codigo>`
(`UAuthWebViewClient.a(Uri)`: esquema = string `uauth_dl_scheme` = "qolarilogin" nas 3 APKs, le os
parametros `session` e `authCode`). A app confirma com POST /rt/silk-screen/submit-form
(`ad1.q.g`: OnboardingFormContainerAnswer, ecra "TypeVerifySession", com o CODE_VERIFIER guardado)
e espera um OnboardingFormContainer com `oAuthInfo` (OAuthInfo: accessToken, refreshToken, tokenType,
expiresIn/refreshTokenExpiresIn = Duration -> numero, idToken, sessionID).
"""
import html
import json

from fastapi.responses import HTMLResponse, JSONResponse

import config
from apps.identity import APPS, _register, find_subject, normalize_phone, open_session, pkce_ok, redeem_login
from apps.rtapi import Call, handles
from core.security import random_code
from domain.models import LoginAttempt

DL_SCHEME = "qolarilogin"  # res/values/strings.xml -> uauth_dl_scheme (igual nas 3 APKs)
APP_NAME = {"rider": "Qolari", "driver": "Qolari Driver", "fleet": "Qolari Fleet"}


# ---- pagina /v2 ------------------------------------------------------------------------------
PAGE = """<!doctype html>
<html lang="pt-PT"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<title>__TITLE__</title>
<link rel="manifest" href="/v2/_static/manifests/manifest.json">
<style>
*{box-sizing:border-box;margin:0;padding:0}
html,body{background:#fff;color:#000;font-family:"Uber Move Text",system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;-webkit-font-smoothing:antialiased}
body{min-height:100vh;display:flex;flex-direction:column}
header{height:64px;display:flex;align-items:center;padding:0 16px;background:#000}
header b{color:#fff;font-size:24px;font-weight:500;letter-spacing:-.5px}
main{flex:1;padding:32px 16px 24px;max-width:560px;width:100%;margin:0 auto;display:flex;flex-direction:column}
h1{font-size:24px;line-height:32px;font-weight:500;margin-bottom:24px}
.sub{font-size:16px;line-height:24px;color:#5e5e5e;margin:-16px 0 24px}
.row{display:flex;gap:8px}
.cc{display:flex;align-items:center;gap:6px;background:#f3f3f3;border-radius:8px;padding:0 12px;height:56px;font-size:16px;white-space:nowrap}
input{width:100%;height:56px;border:2px solid transparent;background:#f3f3f3;border-radius:8px;padding:0 16px;font-size:16px;color:#000;outline:none;font-family:inherit}
input:focus{border-color:#000;background:#fff}
.btn{display:flex;align-items:center;justify-content:center;width:100%;height:56px;border:0;border-radius:8px;background:#000;color:#fff;font-size:18px;font-weight:500;margin-top:16px;font-family:inherit}
.btn:disabled{background:#e8e8e8;color:#afafaf}
.fine{font-size:14px;line-height:20px;color:#5e5e5e;margin-top:16px}
.err{color:#de1135;font-size:14px;line-height:20px;margin-top:8px;min-height:20px}
.otp{display:flex;gap:12px}
.otp input{width:56px;text-align:center;font-size:24px;padding:0}
.chip{display:inline-block;background:#f3f3f3;border-radius:500px;padding:10px 14px;font-size:14px;font-weight:500;margin-top:24px;border:0;color:#000;font-family:inherit}
.chip:disabled{color:#afafaf}
.nav{display:flex;justify-content:space-between;align-items:center;margin-top:auto;padding-top:24px}
.back{width:56px;height:56px;border-radius:50%;background:#f3f3f3;border:0;font-size:24px}
.next{width:auto;padding:0 24px;margin:0;border-radius:500px}
.step{display:none;flex-direction:column;flex:1}.step.on{display:flex}
label{display:block;font-size:14px;font-weight:500;margin:16px 0 8px}
</style></head>
<body>
<header><b>Qolari</b></header>
<main>
 <section class="step on" id="s-phone">
  <h1>Qual é o seu número de telemóvel ou e-mail?</h1>
  <div class="row"><div class="cc">🇵🇹 +351</div>
   <input id="phone" type="tel" inputmode="tel" autocomplete="tel" placeholder="Número de telemóvel"></div>
  <div class="err" id="e-phone"></div>
  <button class="btn" id="b-phone" disabled>Continuar</button>
  <p class="fine">Ao continuar, aceita receber chamadas, incluindo por marcadores automáticos, WhatsApp ou mensagens de texto da Qolari e das suas afiliadas.</p>
 </section>
 <section class="step" id="s-otp">
  <h1 id="otp-title">Introduza o código de 4 dígitos enviado para:</h1>
  <div class="otp"><input inputmode="numeric" maxlength="1"><input inputmode="numeric" maxlength="1"><input inputmode="numeric" maxlength="1"><input inputmode="numeric" maxlength="1"></div>
  <div class="err" id="e-otp"></div>
  <div><button class="chip" id="resend" disabled>Não recebi o código (0:30)</button></div>
  <div class="nav"><button class="back" data-back="s-phone">←</button><button class="btn next" id="b-otp" disabled>Seguinte →</button></div>
 </section>
 <section class="step" id="s-name">
  <h1>Qual é o seu nome?</h1>
  <p class="sub">Diga-nos como devemos chamar-lhe</p>
  <label for="fn">Nome</label><input id="fn" autocomplete="given-name">
  <label for="ln">Apelido</label><input id="ln" autocomplete="family-name">
  <div class="err" id="e-name"></div>
  <div class="nav"><button class="back" data-back="s-otp">←</button><button class="btn next" id="b-name" disabled>Seguinte →</button></div>
 </section>
</main>
<script>
const Q = Object.fromEntries(new URLSearchParams(location.search));
const $ = id => document.getElementById(id);
let phone = "", code = "";
function show(id){document.querySelectorAll(".step").forEach(s=>s.classList.toggle("on", s.id===id));
  const f = document.querySelector("#"+id+" input"); if (f) setTimeout(()=>f.focus(), 50);}
async function api(path, body){
  const r = await fetch("/v2/api/"+path, {method:"POST", headers:{"content-type":"application/json"},
    body: JSON.stringify(Object.assign({query: Q}, body))});
  return r.json();
}
document.querySelectorAll("[data-back]").forEach(b=>b.onclick=()=>show(b.dataset.back));
$("phone").oninput = e => { $("b-phone").disabled = e.target.value.replace(/\\D/g,"").length < 9; $("e-phone").textContent=""; };
$("b-phone").onclick = async () => {
  $("b-phone").disabled = true;
  const r = await api("phone", {phone: $("phone").value});
  $("b-phone").disabled = false;
  if (r.error) { $("e-phone").textContent = r.error; return; }
  phone = r.phone;
  $("otp-title").textContent = "Introduza o código de 4 dígitos enviado para: " + r.display;
  otp.forEach(i=>i.value=""); $("b-otp").disabled = true; timer(); show("s-otp");
};
const otp = [...document.querySelectorAll(".otp input")];
otp.forEach((inp, k) => {
  inp.oninput = () => { inp.value = inp.value.replace(/\\D/g,"").slice(-1); $("e-otp").textContent="";
    if (inp.value && k < 3) otp[k+1].focus();
    code = otp.map(i=>i.value).join(""); $("b-otp").disabled = code.length < 4;
    if (code.length === 4) verify(); };
  inp.onkeydown = e => { if (e.key === "Backspace" && !inp.value && k > 0) otp[k-1].focus(); };
});
let tm;
function timer(){ let s = 30; const b = $("resend"); b.disabled = true; clearInterval(tm);
  tm = setInterval(()=>{ s--; b.textContent = s > 0 ? "Não recebi o código (0:"+String(s).padStart(2,"0")+")" : "Reenviar código por SMS";
    if (s <= 0) { b.disabled = false; clearInterval(tm); } }, 1000); }
$("resend").onclick = () => timer();
$("b-otp").onclick = () => verify();
async function verify(extra){
  $("b-otp").disabled = true;
  const r = await api("verify", Object.assign({phone, code}, extra || {}));
  if (r.error) { $("e-otp").textContent = r.error; $("e-name").textContent = r.error; $("b-otp").disabled = false; return; }
  if (r.needName) { show("s-name"); return; }
  if (r.redirect) location.href = r.redirect;
}
const nameOk = () => { $("b-name").disabled = !$("fn").value.trim(); };
$("fn").oninput = nameOk; $("ln").oninput = nameOk;
$("b-name").onclick = () => verify({firstName: $("fn").value.trim(), lastName: $("ln").value.trim()});
$("phone").focus();
</script>
</body></html>"""


def _display(phone: str) -> str:
    if phone.startswith("+351") and len(phone) == 13:
        return f"+351 {phone[4:7]} {phone[7:10]} {phone[10:]}"
    return phone


@handles(APPS, "GET", "/v2", "/v2/")
def login_page(call: Call):
    return HTMLResponse(PAGE.replace("__TITLE__", html.escape(APP_NAME[call.app])),
                        headers={"Cache-Control": "no-store"})


@handles(APPS, "GET", "/v2/_static/manifests/manifest.json")
def manifest(call: Call):
    return JSONResponse({"name": APP_NAME[call.app], "short_name": APP_NAME[call.app], "start_url": "/v2",
                         "display": "standalone", "background_color": "#ffffff", "theme_color": "#000000"})


@handles(APPS, "POST", "/v2/api/phone")
def login_phone(call: Call):
    phone = normalize_phone(str(call.get("phone", default="")))
    if len(phone) < 12:
        return {"error": "Introduza um número de telemóvel válido."}
    subj = find_subject(call.db, call.app, phone)
    if subj is None and call.app == "fleet":
        return {"error": "Não encontrámos uma conta com este número."}
    if subj is not None and _blocked(subj):
        return {"error": "Esta conta está bloqueada. Contacte o apoio."}
    return {"phone": phone, "display": _display(phone), "exists": subj is not None}


def _blocked(subj) -> bool:
    return getattr(subj, "status", "active") in ("blocked", "rejected") or getattr(subj, "active", True) is False


@handles(APPS, "POST", "/v2/api/verify")
def login_verify(call: Call):
    db, app = call.db, call.app
    phone = normalize_phone(str(call.get("phone", default="")))
    if str(call.get("code", default="")).strip() != config.OTP_CODE:
        return {"error": "O código introduzido está incorreto."}
    subj = find_subject(db, app, phone)
    signup = subj is None
    if signup:
        first = str(call.get("firstName", default="")).strip()
        if not first and app != "fleet":
            return {"needName": True}
        subj, err = _register(db, app, phone, first, str(call.get("lastName", default="")).strip())
        if err:
            return {"error": err}
    if _blocked(subj):
        return {"error": "Esta conta está bloqueada. Contacte o apoio."}
    query = call.body.get("query") if isinstance(call.body.get("query"), dict) else {}
    att = LoginAttempt(app=app, subject_uuid=subj.uuid, auth_code=random_code(32),
                       code_challenge=str(query.get("codeChallenge", "")), is_signup=signup)
    db.add(att)
    db.flush()
    return {"redirect": f"{DL_SCHEME}://auth?session={att.id}&authCode={att.auth_code}"}


# ---- confirmacao pela app --------------------------------------------------------------------
def _strings(obj):
    """Todas as strings de um JSON (o formato exato das respostas do ecra TypeVerifySession ve-se no
    trafego; aqui procura-se o id da sessao, o authCode e o code_verifier onde quer que venham)."""
    if isinstance(obj, str):
        yield obj
        if obj[:1] in "{[":
            try:
                yield from _strings(json.loads(obj))
            except ValueError:
                pass
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _strings(v)


@handles(APPS, "POST", "/rt/silk-screen/submit-form")
def submit_form(call: Call):
    db, app = call.db, call.app
    values = [s for s in _strings(call.body) if s]
    pending = db.query(LoginAttempt).filter_by(app=app, used=False).all()
    att = next((a for a in pending if a.id in values or a.auth_code in values), None)
    verifier = next((v for v in values if att and att.code_challenge and pkce_ok(att.code_challenge, v)), "")
    att, subj = redeem_login(db, app, session_id=att.id if att else "", verifier=verifier)
    tok = open_session(db, app, subj, call.ip, call.headers.get("user-agent", ""))
    return {
        "inAuthSessionID": att.id,
        "userUUID": subj.uuid,
        "isSignup": att.is_signup,
        "oAuthInfo": {"accessToken": tok["accessToken"], "refreshToken": tok["refreshToken"],
                      "tokenType": tok["tokenType"], "expiresIn": tok["expiresIn"],
                      "refreshTokenExpiresIn": tok["refreshTokenExpiresIn"], "idToken": tok["idToken"],
                      "sessionID": tok["sessionID"]},
        "userProfile": {"firstName": subj.first_name, "lastName": subj.last_name or ""},
    }
