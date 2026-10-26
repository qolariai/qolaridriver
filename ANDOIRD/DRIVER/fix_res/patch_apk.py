# -*- coding: utf-8 -*-
# Substitui entradas de drawable partidas (android:src="@null" / drawable="@null")
# dentro da APK por bytes de drawables validos da propria APK. Nao toca em codigo.
import zipfile, sys

APK = r"C:\xampp\htdocs\QOLARI\PROJETOS OFICIAIS\QOLARI DRIVER\DRIVER\qolari-drive.apk"
OUT = r"C:\xampp\htdocs\QOLARI\PROJETOS OFICIAIS\QOLARI DRIVER\DRIVER\qolari-drive-resfix.apk"

DARK  = "res/drawable/divider_horizontal_dark.xml"                  # shape solid cinza80
WHITE = "res/drawable/abc_cab_background_internal_bg.xml"           # shape solid branca
TRANS = "res/drawable/common_google_signin_btn_icon_dark_focused.xml"  # shape transparente

PATCH = {
    # escuro: botoes primarios, splash, seekbar, checkbox/radio/switch, tab indicator
    "res/drawable/ub__button_primary.xml": DARK,
    "res/drawable/ub__carbon_app_splash.xml": DARK,
    "res/drawable/ub__carbon_app_splash_no_top_padding.xml": DARK,
    "res/drawable/ub__splash.xml": DARK,
    "res/drawable-v31/ub__splash.xml": DARK,
    "res/drawable/abc_seekbar_thumb_material.xml": DARK,
    "res/drawable/abc_seekbar_track_material.xml": DARK,
    "res/drawable/abc_tab_indicator_material.xml": DARK,
    "res/drawable/abc_btn_check_material.xml": DARK,
    "res/drawable/abc_btn_radio_material.xml": DARK,
    "res/drawable/abc_switch_thumb_material.xml": DARK,
    # branco: botoes secundarios/split, botao google sign-in
    "res/drawable/ub__button_secondary.xml": WHITE,
    "res/drawable/ub__button_split_left.xml": WHITE,
    "res/drawable/ub__button_split_right.xml": WHITE,
    "res/drawable/common_google_signin_btn_text_dark_normal.xml": WHITE,
    "res/drawable/common_google_signin_btn_text_disabled.xml": WHITE,
    "res/drawable/common_google_signin_btn_text_light_normal.xml": WHITE,
    "res/drawable-watch/common_google_signin_btn_text_dark_normal.xml": WHITE,
    "res/drawable-watch/common_google_signin_btn_text_disabled.xml": WHITE,
    "res/drawable-watch/common_google_signin_btn_text_light_normal.xml": WHITE,
    # transparente: inputs, spinners, highlight selectors, notifications, icones google
    "res/drawable/abc_edit_text_material.xml": TRANS,
    "res/drawable/ub__edit_text_background.xml": TRANS,
    "res/drawable/abc_textfield_search_material.xml": TRANS,
    "res/drawable/abc_spinner_textfield_background_material.xml": TRANS,
    "res/drawable/ub__spinner_background.xml": TRANS,
    "res/drawable/ub__spinner_no_line_background.xml": TRANS,
    "res/drawable/ub__button_supporting.xml": TRANS,
    "res/drawable/abc_item_background_holo_dark.xml": TRANS,
    "res/drawable/abc_item_background_holo_light.xml": TRANS,
    "res/drawable/abc_list_selector_background_transition_holo_dark.xml": TRANS,
    "res/drawable/abc_list_selector_background_transition_holo_light.xml": TRANS,
    "res/drawable/abc_list_selector_holo_dark.xml": TRANS,
    "res/drawable/abc_list_selector_holo_light.xml": TRANS,
    "res/drawable/notification_bg.xml": TRANS,
    "res/drawable/notification_bg_low.xml": TRANS,
    "res/drawable/notification_tile_bg.xml": TRANS,
    "res/drawable/common_google_signin_btn_icon_dark_normal.xml": TRANS,
    "res/drawable/common_google_signin_btn_icon_disabled.xml": TRANS,
    "res/drawable/common_google_signin_btn_icon_light_normal.xml": TRANS,
}

zin = zipfile.ZipFile(APK, "r")
names = set(zin.namelist())
donors = {DARK, WHITE, TRANS}
missing = [p for p in list(PATCH) + list(donors) if p not in names]
if missing:
    print("FALTAM entradas na APK:", missing); sys.exit(1)
donor_bytes = {d: zin.read(d) for d in donors}

zout = zipfile.ZipFile(OUT, "w")
for info in zin.infolist():
    data = PATCH.get(info.filename) and donor_bytes[PATCH[info.filename]] or zin.read(info.filename)
    zi = zipfile.ZipInfo(info.filename, date_time=info.date_time)
    zi.compress_type = info.compress_type
    zi.external_attr = info.external_attr
    zi.internal_attr = info.internal_attr
    zi.create_system = info.create_system
    zout.writestr(zi, data)
zout.close(); zin.close()
print("OK ->", OUT)
