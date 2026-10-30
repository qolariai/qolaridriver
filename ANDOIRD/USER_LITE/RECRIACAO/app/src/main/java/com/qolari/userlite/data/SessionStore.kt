package com.qolari.userlite.data

import android.content.Context
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import com.qolari.userlite.config.AppConfig
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map

private val Context.dataStore by preferencesDataStore(name = AppConfig.SESSION_STORE_NAME)

/** Sessão local (token, telefone e URL guardado). O URL por omissão vem de [AppConfig]. */
class SessionStore(private val context: Context) {

    companion object {
        private val KEY_BASE_URL = stringPreferencesKey("base_url")
        private val KEY_TOKEN = stringPreferencesKey("access_token")
        private val KEY_REFRESH = stringPreferencesKey("refresh_token")
        private val KEY_PHONE = stringPreferencesKey("phone")
    }

    val token = context.dataStore.data.map { it[KEY_TOKEN] }
    val phone = context.dataStore.data.map { it[KEY_PHONE] ?: "" }

    suspend fun current(): SessionSnapshot {
        val p = context.dataStore.data.first()
        return SessionSnapshot(AppConfig.resolveBaseUrl(p[KEY_BASE_URL]), p[KEY_TOKEN], p[KEY_PHONE].orEmpty())
    }

    suspend fun saveSession(token: String, refresh: String?, phone: String) {
        context.dataStore.edit {
            it[KEY_TOKEN] = token
            if (refresh != null) it[KEY_REFRESH] = refresh
            it[KEY_PHONE] = phone
        }
    }

    suspend fun setBaseUrl(url: String) {
        context.dataStore.edit { it[KEY_BASE_URL] = url.trim().trimEnd('/') }
    }

    suspend fun clear() {
        context.dataStore.edit { it.remove(KEY_TOKEN); it.remove(KEY_REFRESH) }
    }
}
