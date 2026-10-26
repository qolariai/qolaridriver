package com.qolari.drivereplica.data

import android.content.Context
import android.net.ConnectivityManager
import android.net.Network
import android.net.NetworkCapabilities
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow

/**
 * Estado da ligação à Internet, para o banner "Nenhuma rede detetada" (capturas 110/115/120: aparece em todos os
 * separadores sem rede e desaparece quando volta). `true` = há ligação validada.
 *
 * O estado vem só dos argumentos das chamadas da rede por omissão: ler `activeNetwork` dentro de `onLost` pode ainda
 * devolver a rede que acabou de cair (corrida), e o banner ficava escondido sem dados móveis.
 */
class NetworkMonitor(context: Context) {
    private val manager = context.getSystemService(ConnectivityManager::class.java)
    private val _connected = MutableStateFlow(hasInternet(manager.getNetworkCapabilities(manager.activeNetwork)))
    val connected: StateFlow<Boolean> = _connected

    init {
        manager.registerDefaultNetworkCallback(object : ConnectivityManager.NetworkCallback() {
            override fun onCapabilitiesChanged(network: Network, caps: NetworkCapabilities) { _connected.value = hasInternet(caps) }
            override fun onLost(network: Network) { _connected.value = false }
            override fun onUnavailable() { _connected.value = false }
        })
    }

    private fun hasInternet(caps: NetworkCapabilities?): Boolean =
        caps != null &&
            caps.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET) &&
            caps.hasCapability(NetworkCapabilities.NET_CAPABILITY_VALIDATED)
}
