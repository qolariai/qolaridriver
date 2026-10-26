package com.qolari.drivereplica.data

import android.content.Context
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import com.qolari.drivereplica.config.AppConfig
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map

private val Context.dataStore by preferencesDataStore(name = AppConfig.SESSION_STORE_NAME)

/** Sessão local (token e telefone) e URL guardado pelo utilizador. O URL por omissão vem de [AppConfig]. */
class SessionStore(private val context: Context) {

    companion object {
        private val KEY_BASE_URL = stringPreferencesKey("base_url")
        private val KEY_TOKEN = stringPreferencesKey("access_token")
        private val KEY_REFRESH = stringPreferencesKey("refresh_token")
        private val KEY_PHONE = stringPreferencesKey("phone")
    }

    val baseUrl = context.dataStore.data.map { AppConfig.resolveBaseUrl(it[KEY_BASE_URL]) }
    val token = context.dataStore.data.map { it[KEY_TOKEN] }
    val refreshToken = context.dataStore.data.map { it[KEY_REFRESH] }
    val phone = context.dataStore.data.map { it[KEY_PHONE] ?: "" }

    suspend fun snapshot() = context.dataStore.data.first()

    /** Estado da sessão numa só leitura: URL efetivo, token e telefone. */
    suspend fun current(): SessionSnapshot {
        val p = snapshot()
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
        context.dataStore.edit {
            it.remove(KEY_TOKEN); it.remove(KEY_REFRESH)
        }
    }
}
