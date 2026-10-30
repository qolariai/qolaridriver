package com.qolari.drivereplica.ui.home

import android.content.Context
import android.os.Handler
import android.os.Looper
import com.qolari.drivereplica.config.AppConfig
import okhttp3.Dns
import okhttp3.OkHttpClient
import okhttp3.Request
import org.json.JSONObject
import java.net.Inet4Address
import java.net.InetAddress
import java.util.concurrent.TimeUnit

/**
 * Rota real (Google Directions) entre dois pontos. Desenha a polilinha que segue as estradas,
 * em vez da linha reta entre recolha e destino. Usa IPv4 para funcionar também no Honor.
 */
object DirectionsClient {

    fun fetch(
        context: Context,
        fromLat: Double,
        fromLng: Double,
        toLat: Double,
        toLng: Double,
        onResult: (List<Pair<Double, Double>>) -> Unit,
    ) {
        val key = runCatching {
            val info = context.packageManager.getApplicationInfo(
                context.packageName,
                android.content.pm.PackageManager.GET_META_DATA,
            )
            info.metaData?.getString("com.google.android.geo.API_KEY").orEmpty()
        }.getOrDefault("")
        if (key.isBlank()) return

        Thread {
            val points = runCatching {
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
                val url = AppConfig.DIRECTIONS_HOST + "/maps/api/directions/json" +
                    "?origin=$fromLat,$fromLng&destination=$toLat,$toLng&mode=driving&overview=full&key=$key"
                client.newCall(Request.Builder().url(url).build()).execute().use { resp ->
                    val body = resp.body?.string()
                    if (!resp.isSuccessful || body.isNullOrBlank()) return@use null
                    val json = JSONObject(body)
                    if (json.optString("status") != "OK") return@use null
                    val routes = json.optJSONArray("routes") ?: return@use null
                    if (routes.length() == 0) return@use null
                    val encoded = routes.getJSONObject(0)
                        .optJSONObject("overview_polyline")?.optString("points").orEmpty()
                    decode(encoded)
                }
            }.getOrNull()
            if (!points.isNullOrEmpty() && points.size > 1) {
                Handler(Looper.getMainLooper()).post { onResult(points) }
            }
        }.apply { isDaemon = true }.start()
    }

    /** Descodifica a polilinha do Google (precisão 1e5). */
    fun decode(encoded: String): List<Pair<Double, Double>> {
        val out = ArrayList<Pair<Double, Double>>()
        var index = 0
        var lat = 0
        var lng = 0
        while (index < encoded.length) {
            var shift = 0
            var result = 0
            var b: Int
            do {
                b = encoded[index++].code - 63
                result = result or ((b and 0x1f) shl shift)
                shift += 5
            } while (b >= 0x20)
            lat += if (result and 1 != 0) (result shr 1).inv() else (result shr 1)

            shift = 0
            result = 0
            do {
                b = encoded[index++].code - 63
                result = result or ((b and 0x1f) shl shift)
                shift += 5
            } while (b >= 0x20)
            lng += if (result and 1 != 0) (result shr 1).inv() else (result shr 1)

            out.add(lat / 1e5 to lng / 1e5)
        }
        return out
    }
}
