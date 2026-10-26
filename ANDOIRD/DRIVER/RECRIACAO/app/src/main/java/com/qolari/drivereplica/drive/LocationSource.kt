package com.qolari.drivereplica.drive

import android.Manifest
import android.annotation.SuppressLint
import android.content.Context
import android.content.pm.PackageManager
import android.location.LocationManager
import androidx.core.content.ContextCompat

/**
 * Última posição conhecida do aparelho, para o servidor saber onde está o motorista (uploadpositions) enquanto está online.
 * Sem permissão devolve nulo: a app continua a funcionar, só não envia a posição.
 */
class LocationSource(private val context: Context) {

    val hasPermission: Boolean
        get() = ContextCompat.checkSelfPermission(context, Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED

    @SuppressLint("MissingPermission")
    fun lastKnown(): Pair<Double, Double>? {
        if (!hasPermission) return null
        val manager = context.getSystemService(LocationManager::class.java)
        val best = listOf(LocationManager.GPS_PROVIDER, LocationManager.NETWORK_PROVIDER, LocationManager.PASSIVE_PROVIDER)
            .mapNotNull { runCatching { manager.getLastKnownLocation(it) }.getOrNull() }
            .maxByOrNull { it.time } ?: return null
        return best.latitude to best.longitude
    }
}
