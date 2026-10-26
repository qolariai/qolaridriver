package com.qolari.shared.map

import android.content.Context
import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.Path
import android.graphics.RectF
import android.util.AttributeSet
import android.widget.FrameLayout
import com.google.android.gms.maps.CameraUpdateFactory
import com.google.android.gms.maps.GoogleMap
import com.google.android.gms.maps.MapView
import com.google.android.gms.maps.model.BitmapDescriptor
import com.google.android.gms.maps.model.BitmapDescriptorFactory
import com.google.android.gms.maps.model.Circle
import com.google.android.gms.maps.model.CircleOptions
import com.google.android.gms.maps.model.LatLng
import com.google.android.gms.maps.model.LatLngBounds
import com.google.android.gms.maps.model.Marker
import com.google.android.gms.maps.model.MarkerOptions
import com.google.android.gms.maps.model.Polyline
import com.google.android.gms.maps.model.PolylineOptions

/**
 * Mapa Google partilhado pelo Driver e pelo Rider.
 *
 * API estável para os Fragments: rota, motorista, posição do aparelho, procura,
 * zoom/recentragem, foco de pesquisa e padding inferior (cartões do Driver).
 * O ciclo de vida do [MapView] é delegado pelos Fragments.
 */
class GoogleMapView @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null,
) : FrameLayout(context, attrs) {

    private val mapView = MapView(context)
    private var map: GoogleMap? = null
    private var ready = false

    private var pendingRoute: List<Pair<Double, Double>> = emptyList()
    private var pendingDriver: Pair<Double, Double>? = null
    private var pendingUser: Pair<Double, Double>? = null
    private var showDemandFlag = true
    private var showUserFlag = true
    private var bottomPaddingDp = 0

    private var polyline: Polyline? = null
    private val routeMarkers = mutableListOf<Marker>()
    private var driverMarker: Marker? = null
    private var userMarker: Marker? = null
    private var focusMarker: Marker? = null
    private val demandCircles = mutableListOf<Circle>()

    private var lastRoute: List<Pair<Double, Double>>? = null
    private var lastDriver: Pair<Double, Double>? = null
    private var lastUser: Pair<Double, Double>? = null

    var showDemand: Boolean = true
        set(value) {
            field = value
            showDemandFlag = value
            render()
        }

    var route: List<Pair<Double, Double>> = emptyList()
        set(value) {
            if (field == value) return
            field = value
            pendingRoute = value
            render(forceFit = true)
        }

    var driver: Pair<Double, Double>? = null
        set(value) {
            if (field == value) return
            field = value
            pendingDriver = value
            render(forceFit = pendingRoute.isEmpty() && value != null)
        }

    var driverHeading: Float = 0f
        set(value) {
            field = value
            driverMarker?.rotation = value
            driverMarker?.isFlat = true
        }

    var userLocation: Pair<Double, Double>? = null
        set(value) {
            pendingUser = value
            render()
        }

    var showUser: Boolean = true
        set(value) {
            showUserFlag = value
            render()
        }

    init {
        addView(mapView, LayoutParams(LayoutParams.MATCH_PARENT, LayoutParams.MATCH_PARENT))
        mapView.onCreate(null)
        mapView.getMapAsync { g ->
            map = g
            ready = true
            g.mapType = GoogleMap.MAP_TYPE_NORMAL
            g.uiSettings.isZoomControlsEnabled = false
            g.uiSettings.isCompassEnabled = false
            g.uiSettings.isMapToolbarEnabled = false
            g.uiSettings.isRotateGesturesEnabled = false
            g.uiSettings.isTiltGesturesEnabled = false
            applyPadding()
            render(forceFit = true)
        }
    }

    fun zoomIn() {
        map?.animateCamera(CameraUpdateFactory.zoomIn())
    }

    fun zoomOut() {
        map?.animateCamera(CameraUpdateFactory.zoomOut())
    }

    fun recenter() {
        val g = map ?: return
        val p = pendingUser
        if (p != null) {
            g.animateCamera(CameraUpdateFactory.newLatLngZoom(latLng(p), ZOOM_USER))
        } else {
            g.animateCamera(CameraUpdateFactory.newLatLngZoom(LISBON, ZOOM_CITY))
        }
    }

    /** Move o mapa para um local escolhido na pesquisa e deixa um marcador temporário. */
    fun focus(lat: Double, lng: Double, title: String? = null) {
        val g = map ?: return
        focusMarker?.remove()
        focusMarker = g.addMarker(
            MarkerOptions().position(LatLng(lat, lng)).title(title).icon(dotIcon()).anchor(0.5f, 0.5f),
        )
        g.animateCamera(CameraUpdateFactory.newLatLngZoom(LatLng(lat, lng), ZOOM_TRIP))
    }

    /** Espaço por baixo do mapa ocupado pelo cartão da proposta/viagem. */
    fun setBottomPaddingDp(value: Int) {
        if (bottomPaddingDp == value) return
        bottomPaddingDp = value
        applyPadding()
        render(forceFit = true)
    }

    fun onResume() = mapView.onResume()

    fun onPause() = mapView.onPause()

    fun onDestroy() {
        map = null
        ready = false
        mapView.onDestroy()
    }

    private fun applyPadding() {
        map?.setPadding(0, 0, 0, (bottomPaddingDp * resources.displayMetrics.density).toInt())
    }

    private fun render(forceFit: Boolean = false) {
        val g = map ?: return
        if (!ready) return

        val routeChanged = pendingRoute != lastRoute
        val driverChanged = pendingDriver != lastDriver
        val userChanged = pendingUser != lastUser

        if (routeChanged || forceFit) {
            polyline?.remove()
            routeMarkers.forEach { it.remove() }
            routeMarkers.clear()
            polyline = null
            if (pendingRoute.isNotEmpty()) {
                focusMarker?.remove()
                focusMarker = null
            }

            if (pendingRoute.size >= 2) {
                val points = pendingRoute.map { latLng(it) }
                polyline = g.addPolyline(
                    PolylineOptions().addAll(points).color(Color.BLACK).width(10f).geodesic(true),
                )
                g.addMarker(
                    MarkerOptions().position(points.first()).icon(dotIcon()).anchor(0.5f, 0.5f),
                )?.let { routeMarkers += it }
                g.addMarker(
                    MarkerOptions().position(points.last()).icon(squareIcon()).anchor(0.5f, 0.5f),
                )?.let { routeMarkers += it }
            } else if (pendingRoute.size == 1) {
                g.addMarker(
                    MarkerOptions().position(latLng(pendingRoute.first())).icon(squareIcon()).anchor(0.5f, 0.5f),
                )?.let { routeMarkers += it }
            }
            renderDemand(g)
            if (pendingRoute.isNotEmpty()) fitRoute(g)
        }

        if (driverChanged || forceFit) {
            driverMarker?.remove()
            driverMarker = pendingDriver?.let {
                g.addMarker(
                    MarkerOptions().position(latLng(it)).icon(carIcon()).anchor(0.5f, 0.5f)
                        .rotation(driverHeading).flat(true),
                )
            }
            if (pendingRoute.isEmpty() && pendingDriver != null) {
                g.animateCamera(CameraUpdateFactory.newLatLngZoom(latLng(pendingDriver!!), ZOOM_DRIVER))
            }
        }

        if (userChanged || forceFit) {
            userMarker?.remove()
            userMarker = if (showUserFlag && pendingUser != null) {
                g.addMarker(MarkerOptions().position(latLng(pendingUser!!)).icon(userIcon()).anchor(0.5f, 0.5f))
            } else {
                null
            }
            if (pendingRoute.isEmpty() && pendingDriver == null && pendingUser != null && forceFit) {
                g.animateCamera(CameraUpdateFactory.newLatLngZoom(latLng(pendingUser!!), ZOOM_USER))
            }
        }

        if (forceFit && pendingRoute.isEmpty() && pendingDriver == null && pendingUser == null) {
            g.moveCamera(CameraUpdateFactory.newLatLngZoom(LISBON, ZOOM_CITY))
        }

        lastRoute = pendingRoute
        lastDriver = pendingDriver
        lastUser = pendingUser
    }

    private fun fitRoute(g: GoogleMap) {
        val points = pendingRoute.map { latLng(it) }
        if (points.size == 1) {
            g.animateCamera(CameraUpdateFactory.newLatLngZoom(points.first(), ZOOM_TRIP))
            return
        }
        val builder = LatLngBounds.Builder()
        points.forEach { builder.include(it) }
        val padding = (72 * resources.displayMetrics.density).toInt()
        runCatching { g.animateCamera(CameraUpdateFactory.newLatLngBounds(builder.build(), padding)) }
            .onFailure { g.animateCamera(CameraUpdateFactory.newLatLngZoom(points.first(), ZOOM_TRIP)) }
    }

    private fun renderDemand(g: GoogleMap) {
        demandCircles.forEach { it.remove() }
        demandCircles.clear()
        if (!showDemandFlag || pendingRoute.isNotEmpty()) return
        DEMAND.forEach { (lat, lng, radius) ->
            demandCircles += g.addCircle(
                CircleOptions().center(LatLng(lat, lng)).radius(radius).fillColor(0x33D98BB8).strokeWidth(0f),
            )
        }
    }

    private fun latLng(p: Pair<Double, Double>) = LatLng(p.first, p.second)

    private fun dotIcon(): BitmapDescriptor = BitmapDescriptorFactory.fromBitmap(
        circleBitmap(22, Color.BLACK, Color.WHITE, 2f),
    )

    private fun squareIcon(): BitmapDescriptor {
        val size = 34
        val bmp = Bitmap.createBitmap(size, size, Bitmap.Config.ARGB_8888)
        val c = Canvas(bmp)
        c.drawRect(RectF(2f, 2f, size - 2f, size - 2f), Paint(Paint.ANTI_ALIAS_FLAG).apply { color = Color.WHITE })
        c.drawRect(RectF(8f, 8f, size - 8f, size - 8f), Paint(Paint.ANTI_ALIAS_FLAG).apply { color = Color.BLACK })
        return BitmapDescriptorFactory.fromBitmap(bmp)
    }

    private fun userIcon(): BitmapDescriptor = BitmapDescriptorFactory.fromBitmap(
        circleBitmap(26, 0xFF3B6CE9.toInt(), Color.WHITE, 3f),
    )

    private fun carIcon(): BitmapDescriptor {
        val size = 44
        val bmp = Bitmap.createBitmap(size, size, Bitmap.Config.ARGB_8888)
        val c = Canvas(bmp)
        c.drawCircle(size / 2f, size / 2f, size / 2f - 1f, Paint(Paint.ANTI_ALIAS_FLAG).apply { color = Color.WHITE })
        c.drawCircle(size / 2f, size / 2f, size / 2f - 4f, Paint(Paint.ANTI_ALIAS_FLAG).apply { color = Color.BLACK })
        val d = resources.displayMetrics.density
        val cx = size / 2f
        val cy = size / 2f
        val car = Path().apply {
            moveTo(cx - 8 * d, cy + 2 * d)
            lineTo(cx - 5 * d, cy - 4 * d)
            lineTo(cx + 4 * d, cy - 4 * d)
            lineTo(cx + 8 * d, cy + 2 * d)
            lineTo(cx + 8 * d, cy + 5 * d)
            lineTo(cx - 8 * d, cy + 5 * d)
            close()
        }
        c.drawPath(car, Paint(Paint.ANTI_ALIAS_FLAG).apply {
            color = Color.WHITE
            style = Paint.Style.STROKE
            strokeWidth = 1.8f * d
            strokeCap = Paint.Cap.ROUND
            strokeJoin = Paint.Join.ROUND
        })
        c.drawCircle(cx - 4.5f * d, cy + 5 * d, 2 * d, Paint(Paint.ANTI_ALIAS_FLAG).apply { color = Color.WHITE })
        c.drawCircle(cx + 4.5f * d, cy + 5 * d, 2 * d, Paint(Paint.ANTI_ALIAS_FLAG).apply { color = Color.WHITE })
        return BitmapDescriptorFactory.fromBitmap(bmp)
    }

    private fun circleBitmap(size: Int, fill: Int, ring: Int, ringDp: Float): Bitmap {
        val bmp = Bitmap.createBitmap(size, size, Bitmap.Config.ARGB_8888)
        val c = Canvas(bmp)
        val r = size / 2f - 1f
        c.drawCircle(size / 2f, size / 2f, r, Paint(Paint.ANTI_ALIAS_FLAG).apply { color = ring })
        c.drawCircle(
            size / 2f, size / 2f, r - ringDp * resources.displayMetrics.density,
            Paint(Paint.ANTI_ALIAS_FLAG).apply { color = fill },
        )
        return bmp
    }

    private companion object {
        val LISBON = LatLng(38.7223, -9.1393)
        const val ZOOM_CITY = 12.5f
        const val ZOOM_USER = 15f
        const val ZOOM_DRIVER = 15.5f
        const val ZOOM_TRIP = 14f
        val DEMAND = listOf(
            Triple(38.735, -9.145, 900.0),
            Triple(38.716, -9.142, 700.0),
            Triple(38.750, -9.160, 800.0),
            Triple(38.707, -9.170, 650.0),
        )
    }
}
