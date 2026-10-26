package com.qolari.userlite.data

import android.content.Context
import com.google.gson.Gson
import com.qolari.userlite.net.RoutePoint

/** Pedido guardado quando a rede falha no momento de pedir a viagem. */
data class PendingTrip(
    val pickup: RoutePoint,
    val dropoff: RoutePoint,
    val productId: Int,
    val payment: String,
    val promoCode: String?,
    val scheduledAt: Long?,
    val stops: List<RoutePoint> = emptyList(),
)

object PendingTripStore {
    private const val FILE = "qolari_pending"
    private const val KEY = "trip"
    private val gson = Gson()

    fun save(context: Context, trip: PendingTrip) {
        context.getSharedPreferences(FILE, Context.MODE_PRIVATE)
            .edit().putString(KEY, gson.toJson(trip)).apply()
    }

    fun load(context: Context): PendingTrip? {
        val raw = context.getSharedPreferences(FILE, Context.MODE_PRIVATE).getString(KEY, null)
            ?: return null
        return runCatching { gson.fromJson(raw, PendingTrip::class.java) }.getOrNull()
    }

    fun clear(context: Context) {
        context.getSharedPreferences(FILE, Context.MODE_PRIVATE).edit().remove(KEY).apply()
    }
}
