package com.qolari.userlite.data

import android.app.Application

data class SessionSnapshot(val baseUrl: String, val token: String?, val phone: String)

/** Ligações partilhadas (DI manual, app pequena). Inicializado em [com.qolari.userlite.QolariApp]. */
object AppGraph {
    private lateinit var app: Application

    fun init(application: Application) {
        app = application
    }

    val context: Application get() = app

    val session by lazy { SessionStore(app) }
    val network by lazy { NetworkMonitor(app) }
    val repository by lazy { UserRepository(session) }
}
