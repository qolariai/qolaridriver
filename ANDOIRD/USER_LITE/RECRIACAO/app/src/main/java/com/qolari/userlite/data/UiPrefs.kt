package com.qolari.userlite.data

import android.content.Context
import androidx.appcompat.app.AppCompatDelegate
import androidx.core.os.LocaleListCompat

/** Preferências de interface: idioma, modo escuro e modo simples. */
object UiPrefs {
    private const val FILE = "qolari_ui"
    const val LANG_PT = "pt"
    const val LANG_EN = "en"

    private fun prefs(c: Context) = c.getSharedPreferences(FILE, Context.MODE_PRIVATE)

    fun language(c: Context): String = prefs(c).getString("language", LANG_PT) ?: LANG_PT
    fun dark(c: Context): Boolean = prefs(c).getBoolean("dark", false)
    fun simple(c: Context): Boolean = prefs(c).getBoolean("simple", false)

    fun setLanguage(c: Context, value: String) {
        prefs(c).edit().putString("language", value).apply()
        apply(c)
    }

    fun setDark(c: Context, value: Boolean) {
        prefs(c).edit().putBoolean("dark", value).apply()
        apply(c)
    }

    fun setSimple(c: Context, value: Boolean) {
        prefs(c).edit().putBoolean("simple", value).apply()
    }

    fun apply(c: Context) {
        AppCompatDelegate.setDefaultNightMode(
            if (dark(c)) AppCompatDelegate.MODE_NIGHT_YES else AppCompatDelegate.MODE_NIGHT_NO,
        )
        AppCompatDelegate.setApplicationLocales(LocaleListCompat.forLanguageTags(language(c)))
    }
}
