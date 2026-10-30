package com.qolari.userlite.ui.map

import android.content.Context
import android.graphics.Color
import android.util.AttributeSet
import android.widget.FrameLayout
import com.google.android.gms.maps.CameraUpdateFactory
import com.google.android.gms.maps.GoogleMap
import com.google.android.gms.maps.MapView
import com.google.android.gms.maps.OnMapReadyCallback
import com.google.android.gms.maps.model.LatLng
import com.google.android.gms.maps.model.LatLngBounds
import com.google.android.gms.maps.model.Marker
import com.google.android.gms.maps.model.MarkerOptions
import com.google.android.gms.maps.model.Polyline
import com.google.android.gms.maps.model.PolylineOptions

/**
 * Mapa real (Google Maps, Maps SDK for Android) do passageiro.
 * A chave vem de local.properties e entra no manifest; sem chave o mapa não carrega.
 */
class RealMapView @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null,
) : FrameLayout(context, attrs), OnMapReadyCallback {

    private val mapView = MapView(context)
    private var map: GoogleMap? = null
    private var routeLine: Polyline? = null
    private var pickupMarker: Marker? = null
    private var dropoffMarker: Marker? = null
    private var driverMarker: Marker? = null

    private var routeData: List<Pair<Double, Double>> = emptyList()
    private var camera = MapCamera()

    var route: List<Pair<Double, Double>>
        get() = routeData
        set(value) { routeData = value; drawRoute() }

    var pickup: Pair<Double, Double>? = null
        set(value) { field = value; drawRoute() }

    var dropoff: Pair<Double, Double>? = null
        set(value) { field = value; drawRoute() }

    var driver: Pair<Double, Double>? = null
        set(value) { field = value; drawRoute() }

    var showUser: Boolean = true
        set(value) { field = value; drawRoute() }

    var userLocation: Pair<Double, Double>? = null
        set(value) {
            field = value
            drawCars()
            drawRoute()
            // A Página inicial centra-se no ponto de recolha (Praça Marquês), não em Lisboa.
            if (value != null && showCars && routeData.isEmpty()) {
                map?.moveCamera(CameraUpdateFactory.newLatLngZoom(LatLng(value.first, value.second), 15f))
            }
        }

    /** Carros disponiveis a volta do ponto de recolha (mapa da pagina inicial, captura 030). */
    var showCars: Boolean = false
        set(value) { field = value; drawCars() }

    private val cars = mutableListOf<Marker>()

    init {
        addView(mapView, LayoutParams(LayoutParams.MATCH_PARENT, LayoutParams.MATCH_PARENT))
        mapView.onCreate(null)
        mapView.getMapAsync(this)
    }

    override fun onMapReady(googleMap: GoogleMap) {
        map = googleMap
        googleMap.uiSettings.isMyLocationButtonEnabled = false
        googleMap.uiSettings.isCompassEnabled = false
        googleMap.uiSettings.isMapToolbarEnabled = false
        googleMap.uiSettings.isZoomControlsEnabled = false
        // Paleta clara e pouco saturada, como o mapa da app original.
        googleMap.setMapStyle(
            com.google.android.gms.maps.model.MapStyleOptions(
                """[
                  {"elementType":"geometry","stylers":[{"color":"#f2f3f5"}]},
                  {"elementType":"labels.icon","stylers":[{"visibility":"off"}]},
                  {"elementType":"labels.text.fill","stylers":[{"color":"#8a8f98"}]},
                  {"elementType":"labels.text.stroke","stylers":[{"color":"#f2f3f5"}]},
                  {"featureType":"administrative","elementType":"geometry","stylers":[{"color":"#e8eaee"}]},
                  {"featureType":"poi","elementType":"geometry","stylers":[{"color":"#e6eadf"}]},
                  {"featureType":"poi.park","elementType":"geometry","stylers":[{"color":"#d7e6cf"}]},
                  {"featureType":"road","elementType":"geometry.fill","stylers":[{"color":"#ffffff"}]},
                  {"featureType":"road","elementType":"geometry.stroke","stylers":[{"color":"#e3e6ea"}]},
                  {"featureType":"road.arterial","elementType":"geometry.fill","stylers":[{"color":"#ffffff"}]},
                  {"featureType":"road.highway","elementType":"geometry.fill","stylers":[{"color":"#f7e6b8"}]},
                  {"featureType":"transit","elementType":"geometry","stylers":[{"color":"#e9ebee"}]},
                  {"featureType":"water","elementType":"geometry.fill","stylers":[{"color":"#cddff1"}]}
                ]""",
            ),
        )
        val start = userLocation?.let { LatLng(it.first, it.second) } ?: Lisboa
        googleMap.moveCamera(CameraUpdateFactory.newLatLngZoom(start, 15f))
        googleMap.setPadding(0, 0, 0, (56 * resources.displayMetrics.density).toInt())
        drawCars()
        drawRoute()
    }

    fun zoomIn() {
        camera = camera.zoomIn()
        map?.animateCamera(CameraUpdateFactory.zoomTo(BASE_ZOOM + (camera.zoom - 1f) * 4f))
    }

    fun zoomOut() {
        camera = camera.zoomOut()
        map?.animateCamera(CameraUpdateFactory.zoomTo(BASE_ZOOM + (camera.zoom - 1f) * 4f))
    }

    fun recenter() {
        camera = camera.recenter()
        val target = userLocation?.let { LatLng(it.first, it.second) } ?: routeData.firstOrNull()?.let { LatLng(it.first, it.second) } ?: Lisboa
        map?.animateCamera(CameraUpdateFactory.newLatLngZoom(target, 14.5f))
    }

    /** Sete carros disponiveis a volta do centro (mapa da captura 030). */
    private fun drawCars() {
        val googleMap = map ?: return
        cars.forEach { it.remove() }
        cars.clear()
        if (!showCars) return
        val center = userLocation ?: return
        val offsets = listOf(
            -0.0016 to 0.0012, 0.0011 to 0.0022, 0.0027 to -0.0009,
            0.0014 to 0.0031, -0.0022 to -0.0018, 0.0032 to 0.0016, -0.0006 to 0.0026,
        )
        val icon = com.google.android.gms.maps.model.BitmapDescriptorFactory.fromBitmap(carBitmap())
        offsets.forEach { (dLat, dLng) ->
            googleMap.addMarker(
                MarkerOptions()
                    .position(LatLng(center.first + dLat, center.second + dLng))
                    .icon(icon)
                    .anchor(0.5f, 0.5f)
                    .zIndex(2f)
                    .flat(true),
            )?.let { cars += it }
        }
    }

    /** Carro pequeno visto de cima, escuro com contorno branco (captura 030). */
    private fun carBitmap(): android.graphics.Bitmap {
        val d = resources.displayMetrics.density
        val w = (15 * d).toInt()
        val h = (24 * d).toInt()
        val bmp = android.graphics.Bitmap.createBitmap(w, h, android.graphics.Bitmap.Config.ARGB_8888)
        val c = android.graphics.Canvas(bmp)
        val body = android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG).apply { color = Color.rgb(28, 28, 28) }
        val outline = android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG).apply {
            color = Color.WHITE
            style = android.graphics.Paint.Style.STROKE
            strokeWidth = 1.2f * d
        }
        val glass = android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG).apply { color = Color.rgb(150, 155, 165) }
        val rect = android.graphics.RectF(1.2f * d, 1.2f * d, w - 1.2f * d, h - 1.2f * d)
        val r = 3.4f * d
        c.drawRoundRect(rect, r, r, body)
        c.drawRoundRect(rect, r, r, outline)
        // vidros frente/trás
        c.drawRoundRect(android.graphics.RectF(3.6f * d, 4.4f * d, w - 3.6f * d, 7f * d), 1f * d, 1f * d, glass)
        c.drawRoundRect(android.graphics.RectF(3.6f * d, h - 7f * d, w - 3.6f * d, h - 4.4f * d), 1f * d, 1f * d, glass)
        return bmp
    }

    private fun drawRoute() {
        val googleMap = map ?: return
        routeLine?.remove()
        pickupMarker?.remove()
        dropoffMarker?.remove()
        driverMarker?.remove()
        if (routeData.size >= 2) {
            routeLine = googleMap.addPolyline(
                PolylineOptions()
                    .addAll(routeData.map { LatLng(it.first, it.second) })
                    .zIndex(2f)
                    .width(5f * resources.displayMetrics.density)
                    .color(Color.rgb(39, 110, 241)),
            )
        }
        pickup?.let {
            pickupMarker = googleMap.addMarker(
                MarkerOptions().position(LatLng(it.first, it.second)).title("Recolha"),
            )
        }
        dropoff?.let {
            dropoffMarker = googleMap.addMarker(
                MarkerOptions().position(LatLng(it.first, it.second)).title("Destino"),
            )
        }
        driver?.let {
            driverMarker = googleMap.addMarker(
                MarkerOptions().position(LatLng(it.first, it.second)).title("Motorista"),
            )
        }
        if (routeData.size >= 2 && pickup == null) {
            val bounds = LatLngBounds.Builder().apply {
                routeData.forEach { include(LatLng(it.first, it.second)) }
            }.build()
            // Desloca o trajeto para baixo, para não ficar escondido atrás dos cartões de
            // recolha/destino que flutuam no topo do mapa (captura 032).
            val d = resources.displayMetrics.density
            googleMap.setPadding(0, (112 * d).toInt(), 0, (56 * d).toInt())
            val pad = (44 * d).toInt()
            googleMap.moveCamera(CameraUpdateFactory.newLatLngBounds(bounds, pad))
        }
    }

    override fun onAttachedToWindow() {
        super.onAttachedToWindow()
        mapView.onResume()
    }

    override fun onDetachedFromWindow() {
        mapView.onPause()
        super.onDetachedFromWindow()
    }

    private companion object {
        const val BASE_ZOOM = 13.4f
        val Lisboa = LatLng(38.7223, -9.1393)
    }
}
