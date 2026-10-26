package com.qolari.userlite.data

import android.content.Context
import android.net.ConnectivityManager
import android.net.Network
import android.net.NetworkCapabilities
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow

/** Estado da ligação, para o banner "Sem conexão de rede" (capturas 050/051). */
class NetworkMonitor(context: Context) {
    private val manager = context.getSystemService(ConnectivityManager::class.java)
    private val _connected = MutableStateFlow(hasInternet(manager.getNetworkCapabilities(manager.activeNetwork)))
    val connected: StateFlow<Boolean> = _connected

    init {
        manager.registerDefaultNetworkCallback(object : ConnectivityManager.NetworkCallback() {
            override fun onCapabilitiesChanged(network: Network, caps: NetworkCapabilities) {
                _connected.value = hasInternet(caps)
            }

            override fun onLost(network: Network) {
                _connected.value = false
            }

            override fun onUnavailable() {
                _connected.value = false
            }
        })
    }

    private fun hasInternet(caps: NetworkCapabilities?): Boolean =
        caps != null &&
            caps.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET) &&
            caps.hasCapability(NetworkCapabilities.NET_CAPABILITY_VALIDATED)
}
