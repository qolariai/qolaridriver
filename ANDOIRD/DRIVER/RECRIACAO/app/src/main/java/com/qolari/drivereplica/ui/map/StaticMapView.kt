package com.qolari.drivereplica.ui.map

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.util.AttributeSet
import android.util.LruCache
import android.view.View
import android.widget.FrameLayout
import android.widget.ImageView
import androidx.core.view.isVisible
import com.qolari.drivereplica.BuildConfig
import com.qolari.drivereplica.config.AppConfig
import com.qolari.drivereplica.ui.home.MapPlaceholderView
import okhttp3.Call
import okhttp3.Callback
import okhttp3.HttpUrl.Companion.toHttpUrl
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.Response
import java.io.IOException

/**
 * Miniatura de mapa real via Google Static Maps.
 *
 * Usada nos cartões de oportunidades/promoções. Se a chave faltar, a rede falhar ou a
 * API recusar, fica o [MapPlaceholderView] desenhado por baixo — nunca um espaço vazio.
 */
class StaticMapView @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null,
) : FrameLayout(context, attrs) {

    private val fallback = MapPlaceholderView(context).apply {
        importantForAccessibility = IMPORTANT_FOR_ACCESSIBILITY_NO
    }
    private val image = ImageView(context).apply {
        scaleType = ImageView.ScaleType.CENTER_CROP
        isVisible = false
        importantForAccessibility = IMPORTANT_FOR_ACCESSIBILITY_NO
    }

    private var call: Call? = null
    private var lastUrl: String? = null
    private var centerValue: Pair<Double, Double> = LISBON

    var center: Pair<Double, Double>
        get() = centerValue
        set(value) {
            if (centerValue == value) return
            centerValue = value
            lastUrl = null
            load()
        }

    var zoom: Int = 13
        set(value) {
            if (field == value) return
            field = value
            lastUrl = null
            load()
        }

    var marker: Boolean = true

    var showDemand: Boolean = true
        set(value) {
            field = value
            fallback.showDemand = value
        }

    init {
        addView(fallback, LayoutParams(LayoutParams.MATCH_PARENT, LayoutParams.MATCH_PARENT))
        addView(image, LayoutParams(LayoutParams.MATCH_PARENT, LayoutParams.MATCH_PARENT))
    }

    override fun onSizeChanged(w: Int, h: Int, oldw: Int, oldh: Int) {
        super.onSizeChanged(w, h, oldw, oldh)
        if (w > 0 && h > 0) load()
    }

    override fun onDetachedFromWindow() {
        call?.cancel()
        super.onDetachedFromWindow()
    }

    private fun load() {
        val key = BuildConfig.MAPS_API_KEY
        if (key.isBlank() || width <= 0 || height <= 0) return
        val w = (width / 2).coerceIn(120, 640)
        val h = (height / 2).coerceIn(90, 640)
        val url = AppConfig.MAPS_STATIC_URL.toHttpUrl().newBuilder()
            .addQueryParameter("center", "${centerValue.first},${centerValue.second}")
            .addQueryParameter("zoom", zoom.toString())
            .addQueryParameter("size", "${w}x${h}")
            .addQueryParameter("scale", "2")
            .addQueryParameter("maptype", "roadmap")
            .addQueryParameter("key", key)
            .apply {
                if (marker) {
                    addQueryParameter(
                        "markers",
                        "color:0x111111|${centerValue.first},${centerValue.second}",
                    )
                }
            }
            .build()
            .toString()
        if (url == lastUrl) return
        lastUrl = url
        CACHE.get(url)?.let { cached ->
            show(cached)
            return
        }
        call?.cancel()
        call = CLIENT.newCall(Request.Builder().url(url).build()).also { c ->
            c.enqueue(object : Callback {
                override fun onFailure(call: Call, e: IOException) = Unit
                override fun onResponse(call: Call, response: Response) {
                    response.use { r ->
                        if (!r.isSuccessful) return
                        val bytes = r.body?.bytes() ?: return
                        val bmp = BitmapFactory.decodeByteArray(bytes, 0, bytes.size) ?: return
                        CACHE.put(url, bmp)
                        image.post { show(bmp) }
                    }
                }
            })
        }
    }

    private fun show(bmp: Bitmap) {
        image.setImageBitmap(bmp)
        image.isVisible = true
        fallback.isVisible = false
    }

    private companion object {
        val LISBON = 38.7223 to -9.1393
        val CLIENT = OkHttpClient()
        val CACHE = object : LruCache<String, Bitmap>(8 * 1024 * 1024) {
            override fun sizeOf(key: String, value: Bitmap) = value.byteCount
        }
    }
}
