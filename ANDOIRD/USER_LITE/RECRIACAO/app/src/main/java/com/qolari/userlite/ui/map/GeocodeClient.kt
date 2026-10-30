package com.qolari.userlite.ui.map

import android.content.Context
import android.os.Handler
import android.os.Looper
import okhttp3.Dns
import okhttp3.OkHttpClient
import okhttp3.Request
import org.json.JSONObject
import java.net.Inet4Address
import java.net.InetAddress
import java.util.concurrent.TimeUnit

/** Endereço legível para a localização atual (reverse geocoding do Google, IPv4). */
object GeocodeClient {

    fun reverse(context: Context, lat: Double, lng: Double, onResult: (String) -> Unit) {
        val key = runCatching {
            val info = context.packageManager.getApplicationInfo(
                context.packageName,
                android.content.pm.PackageManager.GET_META_DATA,
            )
            info.metaData?.getString("com.google.android.geo.API_KEY").orEmpty()
        }.getOrDefault("")
        if (key.isBlank()) return

        Thread {
            val address = runCatching {
                val dns = object : Dns {
                    override fun lookup(hostname: String): List<InetAddress> {
                        val all = Dns.SYSTEM.lookup(hostname)
                        return all.filterIsInstance<Inet4Address>().ifEmpty { all }
                    }
                }
                val client = OkHttpClient.Builder()
                    .dns(dns)
                    .connectTimeout(6, TimeUnit.SECONDS)
                    .readTimeout(10, TimeUnit.SECONDS)
                    .build()
                val url = com.qolari.userlite.config.AppConfig.GOOGLE_MAPS_HOST +
                    "/maps/api/geocode/json" +
                    "?latlng=$lat,$lng&language=pt&key=$key"
                client.newCall(Request.Builder().url(url).build()).execute().use { resp ->
                    val body = resp.body?.string()
                    if (!resp.isSuccessful || body.isNullOrBlank()) return@use null
                    val json = JSONObject(body)
                    if (json.optString("status") != "OK") return@use null
                    val results = json.optJSONArray("results") ?: return@use null
                    if (results.length() == 0) return@use null
                    val first = results.getJSONObject(0)
                    val full = first.optString("formatted_address")
                    // Prefere "Rua X, Cidade" em vez da morada completa com país.
                    val parts = full.split(",").map { it.trim() }.filter { it.isNotEmpty() }
                    when {
                        parts.size >= 3 -> "${parts[0]}, ${parts[1]}"
                        parts.isNotEmpty() -> parts.joinToString(", ")
                        else -> null
                    }
                }
            }.getOrNull()
            if (!address.isNullOrBlank()) {
                Handler(Looper.getMainLooper()).post { onResult(address) }
            }
        }.apply { isDaemon = true }.start()
    }
}
