package com.qolari.userlite.data

import android.Manifest
import android.annotation.SuppressLint
import android.content.Context
import android.content.pm.PackageManager
import android.location.LocationManager
import androidx.core.content.ContextCompat

/**
 * Ultima posicao conhecida do aparelho. O botao "a minha localizacao" usa-a para o ponto de
 * recolha e envia-a ao backend (`/rt/lite/location`). Sem permissao devolve nulo e a app continua.
 */
class LocationSource(private val context: Context) {

    val hasPermission: Boolean
        get() = ContextCompat.checkSelfPermission(
            context, Manifest.permission.ACCESS_FINE_LOCATION
        ) == PackageManager.PERMISSION_GRANTED ||
            ContextCompat.checkSelfPermission(
                context, Manifest.permission.ACCESS_COARSE_LOCATION
            ) == PackageManager.PERMISSION_GRANTED

    @SuppressLint("MissingPermission")
    fun lastKnown(): Pair<Double, Double>? {
        if (!hasPermission) return null
        val manager = context.getSystemService(LocationManager::class.java)
        val best = listOf(
            LocationManager.GPS_PROVIDER,
            LocationManager.NETWORK_PROVIDER,
            LocationManager.PASSIVE_PROVIDER,
        )
            .mapNotNull { runCatching { manager.getLastKnownLocation(it) }.getOrNull() }
            .maxByOrNull { it.time } ?: return null
        return best.latitude to best.longitude
    }
}
