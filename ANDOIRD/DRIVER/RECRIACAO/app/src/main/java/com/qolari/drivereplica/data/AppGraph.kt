package com.qolari.drivereplica.data

import android.app.Application

/** Sessão local lida de uma vez: URL efetivo, token de acesso (nulo sem sessão) e telefone. */
data class SessionSnapshot(val baseUrl: String, val token: String?, val phone: String)

/**
 * Ligações partilhadas da app (D5: DI manual, a app é pequena). Inicializado em [com.qolari.drivereplica.QolariApp].
 * Os ViewModels e a atividade vão buscar daqui o repositório e o monitor de rede.
 */
object AppGraph {
    private lateinit var app: Application

    fun init(application: Application) {
        app = application
    }

    val session by lazy { SessionStore(app) }
    val network by lazy { NetworkMonitor(app) }
    val repository by lazy { DriverRepository(session) }
    val location by lazy { com.qolari.drivereplica.drive.LocationSource(app) }
}
