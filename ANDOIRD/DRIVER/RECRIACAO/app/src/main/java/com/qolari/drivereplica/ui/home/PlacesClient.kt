package com.qolari.drivereplica.ui.home

import android.content.Context
import com.qolari.drivereplica.config.AppConfig
import okhttp3.Dns
import okhttp3.OkHttpClient
import okhttp3.Request
import org.json.JSONObject
import java.net.Inet4Address
import java.net.InetAddress
import java.net.URLEncoder
import java.util.concurrent.TimeUnit

/** Um local devolvido pelo Places Autocomplete. */
data class Place(val description: String, val latitude: Double, val longitude: Double)

/**
 * Pesquisa de locais (Places Autocomplete + Place Details) para o Modo Destino.
 *
 * Corre em modo síncrono dentro de uma corrotina do fragment (o chamador usa `delay` para
 * fazer debounce). Usa IPv4, como o [DirectionsClient], para funcionar também no Honor.
 *
 * Devolve lista vazia quando o Google não responde: o ecrã mostra "sem resultados" em vez de
 * inventar locais.
 */
object PlacesClient {

    private fun apiKey(context: Context): String = runCatching {
        val info = context.packageManager.getApplicationInfo(
            context.packageName,
            android.content.pm.PackageManager.GET_META_DATA,
        )
        info.metaData?.getString("com.google.android.geo.API_KEY").orEmpty()
    }.getOrDefault("")

    private fun client(): OkHttpClient {
        val dns = object : Dns {
            override fun lookup(hostname: String): List<InetAddress> {
                val all = Dns.SYSTEM.lookup(hostname)
                return all.filterIsInstance<Inet4Address>().ifEmpty { all }
            }
        }
        return OkHttpClient.Builder()
            .dns(dns)
            .connectTimeout(6, TimeUnit.SECONDS)
            .readTimeout(10, TimeUnit.SECONDS)
            .build()
    }

    /** Sugestões para [query] (mínimo 3 caracteres). Bloqueia: chamar fora do main thread. */
    fun search(context: Context, query: String): List<Place> {
        val key = apiKey(context)
        if (key.isBlank() || query.isBlank()) return emptyList()
        return runCatching {
            val q = URLEncoder.encode(query, "UTF-8")
            val url = AppConfig.PLACES_HOST + "/maps/api/place/autocomplete/json" +
                "?input=$q&language=pt&components=country:pt&key=$key"
            val body = client().newCall(Request.Builder().url(url).build()).execute().use { r ->
                if (!r.isSuccessful) return@use null
                r.body?.string()
            } ?: return emptyList()
            val json = JSONObject(body)
            if (json.optString("status") != "OK") return emptyList()
            val preds = json.optJSONArray("predictions") ?: return emptyList()
            (0 until minOf(preds.length(), 6)).mapNotNull { i ->
                val p = preds.getJSONObject(i)
                val id = p.optString("place_id")
                val desc = p.optString("description")
                if (id.isBlank() || desc.isBlank()) return@mapNotNull null
                // O autocomplete só dá o texto; as coordenadas vêm do Place Details.
                val loc = details(key, id) ?: return@mapNotNull null
                Place(desc, loc.first, loc.second)
            }
        }.getOrDefault(emptyList())
    }

    /** Coordenadas de um `place_id` (Place Details, só o campo `geometry`). */
    private fun details(key: String, placeId: String): Pair<Double, Double>? = runCatching {
        val id = URLEncoder.encode(placeId, "UTF-8")
        val url = AppConfig.PLACES_HOST + "/maps/api/place/details/json" +
            "?place_id=$id&fields=geometry&language=pt&key=$key"
        val body = client().newCall(Request.Builder().url(url).build()).execute().use { r ->
            if (!r.isSuccessful) return@use null
            r.body?.string()
        } ?: return null
        val loc = JSONObject(body).optJSONObject("result")?.optJSONObject("geometry")?.optJSONObject("location")
            ?: return null
        val lat = loc.optDouble("lat", Double.NaN)
        val lng = loc.optDouble("lng", Double.NaN)
        if (lat.isNaN() || lng.isNaN()) null else lat to lng
    }.getOrNull()
}
