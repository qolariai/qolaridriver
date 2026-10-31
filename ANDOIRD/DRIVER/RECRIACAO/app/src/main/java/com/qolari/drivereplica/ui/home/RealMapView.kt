package com.qolari.drivereplica.ui.home

import android.content.Context
import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.RadialGradient
import android.graphics.RectF
import android.graphics.Shader
import android.util.AttributeSet
import android.widget.FrameLayout
import com.google.android.gms.maps.CameraUpdateFactory
import com.google.android.gms.maps.GoogleMap
import com.google.android.gms.maps.MapView
import com.google.android.gms.maps.OnMapReadyCallback
import com.google.android.gms.maps.model.BitmapDescriptorFactory
import com.google.android.gms.maps.model.GroundOverlay
import com.google.android.gms.maps.model.GroundOverlayOptions
import com.google.android.gms.maps.model.LatLng
import com.google.android.gms.maps.model.LatLngBounds
import com.google.android.gms.maps.model.MapStyleOptions
import com.google.android.gms.maps.model.Marker
import com.google.android.gms.maps.model.MarkerOptions
import com.google.android.gms.maps.model.Polyline
import com.google.android.gms.maps.model.PolylineOptions

/**
 * Mapa real (Google Maps, Maps SDK for Android) com o estilo do ecrã original:
 * fundo azul-cinza (#EDF0F5), vias brancas, vias rápidas azul-acinzentado, água (#BAD8FB)
 * e um heatmap laranja difuso da procura, sem pontos de interesse nem transportes.
 * A chave vem de local.properties e entra no manifest; sem chave o mapa não carrega.
 */
class RealMapView @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null,
) : FrameLayout(context, attrs), OnMapReadyCallback {

    private val mapView = MapView(context)
    private var map: GoogleMap? = null
    private var routeCasing: Polyline? = null
    private var routeLine: Polyline? = null
    /** Balão branco com o nome da rua atual (navegação, vídeo 2026-10-30). */
    private var streetLabel: Marker? = null
    private var heat: GroundOverlay? = null
    private val pills = mutableListOf<Marker>()
    private var driverMarker: Marker? = null
    private var pickupMarker: Marker? = null
    private var dropoffMarker: Marker? = null

    /** Desenho progressivo do traço da proposta (0..1), como na Uber. */
    private var routeProgress = 1f
    private var routeAnimator: android.animation.ValueAnimator? = null

    private var routeData: List<Pair<Double, Double>> = emptyList()
    private var showDemandData = true
    private var bottomPaddingPx = 0
    private var topPaddingPx = 0
    /** Offset extra em baixo para a seta do motorista ficar a ~2/3 da altura (modo navegação). */
    private var driverBottomPad = 0

    /** Traço grosso preto+cinzento (proposta) vs. fino escuro (viagem, como a navegação da Uber). */
    private var thickRoute = false

    // ---- Proposta: troço motorista->recolha + recolha->destino, com o efeito que percorre a linha ----
    private var pickupRoute: List<Pair<Double, Double>> = emptyList()
    private var tripRoute: List<Pair<Double, Double>> = emptyList()
    private var offerCasing: Polyline? = null
    private var offerFill: Polyline? = null
    private var pickupCasing: Polyline? = null
    private var pickupFill: Polyline? = null
    /** Segmento escuro que percorre a linha (efeito de "varrimento" da Uber). */
    private var sweepCasing: Polyline? = null
    private var sweepFill: Polyline? = null
    private var sweepProgress = 1f
    private var sweepHandler: android.os.Handler? = null

    /** Mostra as zonas de procura e os marcadores de tempo (como o mapa da Página inicial). */
    var showDemand: Boolean
        get() = showDemandData
        set(value) { showDemandData = value; drawDemand() }

    /** Mostra os marcadores de recolha/destino (só durante a proposta, como na referência). */
    var showOfferMarkers: Boolean = false
        set(value) { field = value; drawOfferMarkers() }

    /** Ângulo do veículo (graus, 0 = norte) para rodar a seta do motorista. */
    var bearing: Float? = null
        set(value) { field = value; driverMarker?.rotation = value ?: 0f }


    /** Posição real do telemóvel (GPS): move o marcador do motorista e segue-o em navegação. */
    var deviceLocation: Pair<Double, Double>? = null
        set(value) {
            field = value
            val p = value?.let { LatLng(it.first, it.second) } ?: return
            driverMarker?.position = p
            // Durante o cartão do pedido a câmara fica em plano amplo e NÃO segue o GPS:
            // o traço inteiro tem de ficar visível até aceitar/recusar.
            if (showOfferMarkers) return
            if (navigating) followDriver()
            else if (routeData.isEmpty()) map?.moveCamera(CameraUpdateFactory.newLatLngZoom(p, 15f))
        }

    /**
     * Rota (lat, lng) a desenhar por cima do mapa.
     * [animate] = true desenha o traço da origem para o destino como na Uber (proposta);
     * [frameToRoute] = false deixa a câmara em paz (as viagens já seguem o GPS).
     */
    /** Rota (lat, lng) a desenhar por cima do mapa. */
    var route: List<Pair<Double, Double>>
        get() = routeData
        set(value) {
            if (value == routeData) return
            thickRoute = false
            setRoute(value, animate = false, frameToRoute = false)
            focusedLatLng = value.lastOrNull()?.let { LatLng(it.first, it.second) }
            // Com o cartão do pedido aberto, a câmara manda em reframe(): não se mexe aqui.
            if (showOfferMarkers) return
            if (navigating) followDriver() else wideView()
        }

    /** Pontos da proposta (recolha e destino) para os marcadores, mesmo antes de haver traço. */
    var offerEndpoints: Pair<Pair<Double, Double>, Pair<Double, Double>>? = null
        set(value) { field = value; drawOfferMarkers() }

    fun routeToPickup(): List<Pair<Double, Double>> = pickupRoute

    fun routeToDropoff(): List<Pair<Double, Double>> = tripRoute

    /**
     * Plano amplo: enquadra as duas pernas + motorista, com margem para o cartão em baixo
     * e para o painel em cima. É este o enquadramento do cartão do pedido (vídeo 2026-10-29):
     * o traço inteiro fica visível até o cartão desaparecer (aceitar/recusar).
     */
    fun reframe() {
        val googleMap = map ?: return
        if (routeData.size < 2) return
        runCatching {
            val builder = LatLngBounds.Builder()
            routeData.forEach { builder.include(LatLng(it.first, it.second)) }
            deviceLocation?.let { builder.include(LatLng(it.first, it.second)) }
            val bounds = builder.build()

            // ATENÇÃO: o setPadding() JÁ reserva a área do cartão e do painel. Passar essa
            // altura outra vez ao newLatLngBounds desconta-a duas vezes e o mapa afasta-se
            // até ao país inteiro. Aqui só entra a margem visual.
            val d = resources.displayMetrics.density
            val margem = (28 * d).toInt()
            googleMap.moveCamera(CameraUpdateFactory.newLatLngBounds(bounds, margem))
        }
    }

    /**
     * Proposta completa, como no vídeo de 2026-10-29: dois troços na mesma linha —
     * motorista -> recolha (`toPickup`, cinza-mais-escuro) e recolha -> destino (`trip`, cinza-claro),
     * ambos com contorno preto e um segmento escuro que percorre a linha (efeito de varrimento).
     */
    fun setOfferRoutes(
        toPickup: List<Pair<Double, Double>>,
        trip: List<Pair<Double, Double>>,
        cardHeightPx: Int,
        animate: Boolean = true,
    ) {
        thickRoute = true
        setBottomPadding(cardHeightPx + (16 * resources.displayMetrics.density).toInt())
        routeAnimator?.cancel()
        pickupRoute = toPickup
        tripRoute = trip
        routeData = toPickup + trip.drop(1)
        // Desenha SEM reenquadrar: o enquadramento é feito a seguir, depois de o padding
        // estar aplicado. Enquadrar antes do padding dá a câmara errada e corta o traço.
        drawOfferRoutes(frameToRoute = false)
        drawOfferMarkers()
        // Plano amplo com as duas pernas + motorista, respeitando a altura do cartão.
        reframe()
        postDelayed({ reframe() }, 300)
        if (animate) startSweep()
    }

    /** Traço da proposta (compatibilidade): só o percurso recolha -> destino. */
    fun setOfferRoute(points: List<Pair<Double, Double>>, cardHeightPx: Int, animate: Boolean = true) {
        setOfferRoutes(emptyList(), points, cardHeightPx, animate)
    }

    /** Limpa os troços da proposta (ao sair do ecrã de pedido). */
    fun clearOfferRoutes() {
        stopSweep()
        routeAnimator?.cancel()
        listOfNotNull(offerCasing, offerFill, pickupCasing, pickupFill).forEach { it.remove() }
        offerCasing = null
        offerFill = null
        pickupCasing = null
        pickupFill = null
        pickupRoute = emptyList()
        tripRoute = emptyList()
        // Limpar também a rota de navegação: sem isto o traço da viagem cancelada ficava no mapa
        // (o setter não redesenhava porque `routeData` já estava vazio).
        routeData = emptyList()
        routeCasing?.remove()
        routeLine?.remove()
        routeCasing = null
        routeLine = null
        streetLabel?.remove()
        streetLabel = null
    }

    /** O efeito que percorre a linha: um segmento escuro que avança e deixa o cinza-claro atrás. */
    private fun startSweep() {
        stopSweep()
        sweepProgress = 0f
        drawSweep()
        // Relógio próprio (não o ValueAnimator): funciona mesmo com as animações do sistema
        // desligadas (Honor com animator_duration_scale=0), onde o ValueAnimator não corre.
        val handler = android.os.Handler(android.os.Looper.getMainLooper())
        sweepHandler = handler
        val start = android.os.SystemClock.elapsedRealtime()
        val step = object : Runnable {
            override fun run() {
                if (sweepHandler !== handler) return
                val elapsed = android.os.SystemClock.elapsedRealtime() - start
                sweepProgress = ((elapsed % SWEEP_MS).toFloat() / SWEEP_MS)
                drawSweep()
                handler.postDelayed(this, SWEEP_FRAME_MS)
            }
        }
        handler.post(step)
    }

    private fun stopSweep() {
        sweepHandler?.removeCallbacksAndMessages(null)
        sweepHandler = null
        sweepCasing?.remove()
        sweepFill?.remove()
        sweepCasing = null
        sweepFill = null
    }

    /** Segmento escuro que percorre a linha completa da proposta (recolha -> destino). */
    private fun drawSweep() {
        val googleMap = map ?: return
        sweepCasing?.remove()
        sweepFill?.remove()
        sweepCasing = null
        sweepFill = null
        val all = routeData
        if (all.size < 2) return
        // O varrimento percorre a linha completa: motorista -> recolha -> destino.
        val total = all.size
        val head = (sweepProgress * (total + SWEEP_TAIL)).toInt()
        val from = (head - SWEEP_TAIL).coerceAtLeast(0)
        val to = head.coerceAtMost(total)
        if (to - from < 2) return
        val slice = all.subList(from, to).map { LatLng(it.first, it.second) }
        val d = resources.displayMetrics.density
        sweepCasing = googleMap.addPolyline(
            PolylineOptions().addAll(slice).width(13.5f * d).color(Color.rgb(17, 17, 17)).zIndex(1.9f),
        )
        sweepFill = googleMap.addPolyline(
            PolylineOptions().addAll(slice).width(7f * d).color(Color.rgb(87, 87, 87)).zIndex(2f),
        )
    }

    /** Contorno preto + interior: recolha->destino a cinza-claro, motorista->recolha mais escuro. */
    private fun drawOfferRoutes(frameToRoute: Boolean) {
        val googleMap = map ?: return
        listOfNotNull(offerCasing, offerFill, pickupCasing, pickupFill).forEach { it.remove() }
        offerCasing = null
        offerFill = null
        pickupCasing = null
        pickupFill = null
        val d = resources.displayMetrics.density
        fun draw(points: List<Pair<Double, Double>>, fillColor: Int): Pair<Polyline, Polyline>? {
            if (points.size < 2) return null
            val latlngs = points.map { LatLng(it.first, it.second) }
            val casing = googleMap.addPolyline(
                PolylineOptions().addAll(latlngs).width(13.5f * d).color(Color.rgb(17, 17, 17)).zIndex(1.5f),
            )
            val fill = googleMap.addPolyline(
                PolylineOptions().addAll(latlngs).width(7f * d).color(fillColor).zIndex(1.6f),
            )
            return casing to fill
        }
        draw(tripRoute, Color.rgb(165, 165, 165))?.let { (c, f) -> offerCasing = c; offerFill = f }
        draw(pickupRoute, Color.rgb(165, 165, 165))?.let { (c, f) -> pickupCasing = c; pickupFill = f }
        if (frameToRoute && routeData.size > 1) {
            runCatching {
                val bounds = LatLngBounds.Builder().apply {
                    routeData.forEach { include(LatLng(it.first, it.second)) }
                }.build()
                val pad = (32 * d).toInt()
                googleMap.moveCamera(CameraUpdateFactory.newLatLngBounds(bounds, pad))
            }
        }
    }

    private fun setRoute(
        points: List<Pair<Double, Double>>,
        animate: Boolean,
        frameToRoute: Boolean,
    ) {
        routeAnimator?.cancel()
        routeData = points
        routeProgress = if (animate) 0f else 1f
        drawRoute(frameToRoute)
        if (animate && points.size > 1) {
            routeAnimator = android.animation.ValueAnimator.ofFloat(0f, 1f).apply {
                duration = ROUTE_ANIM_MS
                interpolator = android.view.animation.DecelerateInterpolator(1.4f)
                addUpdateListener {
                    routeProgress = it.animatedValue as Float
                    drawRoute(false)
                }
                start()
            }
        }
        drawOfferMarkers()
    }


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
        googleMap.uiSettings.isIndoorLevelPickerEnabled = false
        // Padding já pedido antes do mapa estar pronto (ex.: cartão da proposta aberto).
        if (bottomPaddingPx > 0) googleMap.setPadding(0, 0, 0, bottomPaddingPx)
        runCatching { googleMap.setMapStyle(MapStyleOptions(if (navigating) NAV_STYLE else MAP_STYLE)) }
        // Sem volumes 3D também no arranque (vídeo 2026-10-30: o 3D "só prejudica").
        runCatching { googleMap.setBuildingsEnabled(false) }
        // Enquadramento da captura 120: Oeiras em baixo à esquerda, Lisboa à direita,
        // Amadora e o aeroporto em cima.
        googleMap.moveCamera(
            CameraUpdateFactory.newLatLngZoom(CENTER, ZOOM),
        )
        driverMarker = googleMap.addMarker(
            MarkerOptions().position(deviceLocation?.let { LatLng(it.first, it.second) } ?: LISBOA)
                .icon(BitmapDescriptorFactory.fromBitmap(driverPin()))
                .anchor(0.5f, 0.5f)
                .zIndex(2f)
                // flat(false): a seta fica sempre direita no ecrã (a apontar para cima), como no
                // Maps. Com flat(true) rodava com o mapa e ficava de lado.
                .flat(false),
        )
        drawDemand()
        drawRoute()
        drawOfferMarkers()
    }

    /** Círculo branco com anel preto e seta: posição do motorista (vídeo 2026-10-30, maior). */
    private fun driverPin(): Bitmap {
        val d = resources.displayMetrics.density
        val size = (62 * d).toInt()
        val bitmap = Bitmap.createBitmap(size, size, Bitmap.Config.ARGB_8888)
        val canvas = Canvas(bitmap)
        val cx = size / 2f
        val cy = size / 2f
        val black = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = Color.rgb(17, 17, 17) }
        val white = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = Color.WHITE }
        val halo = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = Color.argb(32, 0, 0, 0) }

        // Pino INTEIRO deitado no mapa (pedido de 2026-10-30): bola, anel e seta são comprimidos
        // na vertical, como um objeto no chão visto com o mapa inclinado. Deixa de ser um círculo
        // e passa a ser uma elipse — é a perspetiva toda, não só a seta.
        canvas.save()
        canvas.scale(1f, PIN_FLATTEN, cx, cy)

        canvas.drawCircle(cx, cy, size / 2f, halo)
        canvas.drawCircle(cx, cy, size / 2f - 2 * d, black)
        canvas.drawCircle(cx, cy, size / 2f - 7 * d, white)

        val arrow = android.graphics.Path().apply {
            moveTo(cx, cy - 11.5f * d)
            lineTo(cx + 10f * d, cy + 10.5f * d)
            lineTo(cx, cy + 4f * d)
            lineTo(cx - 10f * d, cy + 10.5f * d)
            close()
        }
        canvas.drawPath(arrow, black)
        canvas.restore()
        return bitmap
    }

    /** Bolha verde de recolha: círculo com quadrado branco e haste (vídeo 2026-10-30). */
    private fun pickupPin(): Bitmap {
        val d = resources.displayMetrics.density
        val w = (44 * d).toInt()
        val h = (58 * d).toInt()
        val bitmap = Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888)
        val canvas = Canvas(bitmap)
        val green = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = Color.rgb(14, 131, 69) }
        val white = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = Color.WHITE }
        val black = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = Color.rgb(17, 17, 17) }
        val cx = w / 2f
        val r = 17 * d
        val cy = r + 1 * d
        // Haste VERDE ate ao ponto de recolha, com a base escura (video 2026-10-30).
        // No original a haste acompanha a cor da bolha, nao e preta.
        canvas.drawRect(cx - 1.6f * d, cy, cx + 1.6f * d, h - 5.5f * d, green)
        canvas.drawCircle(cx, h - 5.5f * d, 4.8f * d, black)
        canvas.drawCircle(cx, h - 5.5f * d, 2.2f * d, white)
        // Bolha verde com quadrado branco.
        canvas.drawCircle(cx, cy, r, green)
        val sq = RectF(cx - 4.5f * d, cy - 4.5f * d, cx + 4.5f * d, cy + 4.5f * d)
        canvas.drawRect(sq, white)
        return bitmap
    }

    /** Bolha vermelha de destino: círculo com quadrado branco e haste (vídeo 2026-10-30). */
    private fun dropoffPin(): Bitmap {
        val d = resources.displayMetrics.density
        val w = (44 * d).toInt()
        val h = (58 * d).toInt()
        val bitmap = Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888)
        val canvas = Canvas(bitmap)
        val red = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = Color.rgb(222, 17, 53) }
        val white = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = Color.WHITE }
        val black = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = Color.rgb(17, 17, 17) }
        val cx = w / 2f
        val r = 17 * d
        val cy = r + 1 * d
        canvas.drawRect(cx - 1.5f * d, cy, cx + 1.5f * d, h - 6 * d, black)
        // Haste com ponto branco na coordenada.
        canvas.drawCircle(cx, h - 6 * d, 4.5f * d, white)
        canvas.drawCircle(cx, h - 6 * d, 2.6f * d, black)
        // Bolha vermelha com quadrado branco.
        canvas.drawCircle(cx, cy, r, red)
        val sq = RectF(cx - 4.5f * d, cy - 4.5f * d, cx + 4.5f * d, cy + 4.5f * d)
        canvas.drawRect(sq, white)
        return bitmap
    }


    private fun drawDemand() {
        val googleMap = map ?: return
        heat?.remove()
        heat = null
        pills.forEach { it.remove() }
        pills.clear()
        // O marcador do motorista fica sempre visível (vídeo 2026-10-29: mantém-se no pedido);
        // só as zonas de procura e as pills é que saem.
        driverMarker?.isVisible = true
        if (!showDemandData) return

        // Heatmap da procura: mancha laranja difusa sobre a área metropolitana.
        heat = googleMap.addGroundOverlay(
            GroundOverlayOptions()
                .image(BitmapDescriptorFactory.fromBitmap(heatBitmap()))
                .positionFromBounds(HEAT_BOUNDS)
                .zIndex(1f),
        )

        // Densidade de propostas como na captura 120: pills espalhadas, algumas cortadas nos bordos.
        PILLS.forEach { (lat, lng, label) ->
            googleMap.addMarker(
                MarkerOptions().position(LatLng(lat, lng))
                    .icon(BitmapDescriptorFactory.fromBitmap(pill(label)))
                    .anchor(0.5f, 0.5f)
                    .zIndex(2f),
            )?.also { pills += it }
        }
    }

    /** Mancha de calor desenhada num bitmap (gradientes radiais laranja com alfa). */
    private fun heatBitmap(): Bitmap {
        val w = 640
        val h = 560
        val bitmap = Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888)
        val canvas = Canvas(bitmap)
        val warm = Color.rgb(205, 132, 92)
        val deep = Color.rgb(178, 105, 70)
        // (fx, fy, raio em fração da largura, cor, alfa)
        val blobs = listOf(
            floatArrayOf(0.30f, 0.34f, 0.30f, 0f, 120f),
            floatArrayOf(0.44f, 0.46f, 0.26f, 1f, 130f),
            floatArrayOf(0.56f, 0.56f, 0.24f, 0f, 125f),
            floatArrayOf(0.40f, 0.66f, 0.22f, 0f, 110f),
            floatArrayOf(0.64f, 0.36f, 0.20f, 1f, 105f),
            floatArrayOf(0.22f, 0.56f, 0.20f, 1f, 95f),
            floatArrayOf(0.50f, 0.24f, 0.18f, 0f, 90f),
            floatArrayOf(0.72f, 0.62f, 0.16f, 1f, 85f),
            floatArrayOf(0.34f, 0.80f, 0.16f, 0f, 80f),
        )
        val paint = Paint(Paint.ANTI_ALIAS_FLAG)
        blobs.forEach { b ->
            val cx = w * b[0]
            val cy = h * b[1]
            val r = w * b[2]
            val base = if (b[3] == 1f) deep else warm
            val a = b[4].toInt()
            paint.shader = RadialGradient(
                cx, cy, r,
                intArrayOf(
                    Color.argb(a, Color.red(base), Color.green(base), Color.blue(base)),
                    Color.argb((a * 0.55f).toInt(), Color.red(base), Color.green(base), Color.blue(base)),
                    Color.argb(0, Color.red(base), Color.green(base), Color.blue(base)),
                ),
                floatArrayOf(0f, 0.45f, 1f),
                Shader.TileMode.CLAMP,
            )
            canvas.drawCircle(cx, cy, r, paint)
        }
        paint.shader = null
        return bitmap
    }

    private fun drawRoute(frameToRoute: Boolean = true) {
        val googleMap = map ?: return
        routeCasing?.remove()
        routeLine?.remove()
        routeCasing = null
        routeLine = null
        clearChevrons()
        if (routeData.size < 2) return
        val points = routeData.map { LatLng(it.first, it.second) }
        val d = resources.displayMetrics.density
        // Navegação: traço grosso como na Uber (contorno preto + interior escuro), 20% mais fino.
        val casingW = if (thickNavigation) 12f * d else if (thickRoute) 13.5f * d else 6f * d
        val innerW = if (thickNavigation) 8f * d else if (thickRoute) 7f * d else 4f * d
        // Navegacao: carmim como no video de 2026-10-30 (medido #E62042 no original).
        // A proposta continua cinza claro; o traco fino de repouso mantem-se escuro.
        val innerColor = when {
            thickNavigation -> NAV_ROUTE_RED
            thickRoute -> Color.rgb(165, 165, 165)
            else -> Color.rgb(17, 17, 17)
        }
        routeCasing = googleMap.addPolyline(
            PolylineOptions().addAll(points)
                .width(casingW)
                .color(Color.rgb(17, 17, 17))
                .zIndex(1.5f),
        )
        routeLine = googleMap.addPolyline(
            PolylineOptions().addAll(points)
                .width(innerW)
                .color(innerColor)
                .zIndex(1.6f),
        )
        // Setas brancas a marcar o sentido da marcha (video 2026-10-30). So em navegacao: na
        // vista geral nao fazem sentido e o `thickNavigation` continua ligado (e uma propriedade
        // diferente do modo da camara), por isso era o `navigating` que faltava aqui. Era a causa
        // dos chevrons que apareciam na vista geral (reportado a 2026-10-31).
        if (thickNavigation && navigating) drawChevrons(googleMap)
        if (frameToRoute && routeProgress >= 1f) {
            runCatching {
                val bounds = LatLngBounds.Builder().apply {
                    routeData.forEach { include(LatLng(it.first, it.second)) }
                }.build()
                // O padding do mapa (setPadding) já reserva a área do cartão; aqui só sobra a margem.
                val pad = (32 * resources.displayMetrics.density).toInt()
                googleMap.moveCamera(CameraUpdateFactory.newLatLngBounds(bounds, pad))
            }
        }
    }

    // ---- Chevrons brancos sobre o traco de navegacao (video 2026-10-30) ----
    private val chevrons = mutableListOf<Marker>()

    private fun clearChevrons() {
        chevrons.forEach { it.remove() }
        chevrons.clear()
    }

    /**
     * Po e uma seta branca a cada [CHEVRON_STEP_M] metros ao longo da rota, rodada com o
     * rumo do troco. Como no original, a seta aponta para o sentido de marcha.
     */
    private fun drawChevrons(googleMap: GoogleMap) {
        if (routeData.size < 2) return
        val icon = BitmapDescriptorFactory.fromBitmap(chevronBitmap())
        var walked = CHEVRON_START_M
        var placed = 0
        for (i in 0 until routeData.size - 1) {
            val a = LatLng(routeData[i].first, routeData[i].second)
            val b = LatLng(routeData[i + 1].first, routeData[i + 1].second)
            val seg = distance(a, b)
            if (seg <= 0.0) continue
            while (walked <= seg && placed < CHEVRON_MAX) {
                val f = walked / seg
                val p = LatLng(
                    a.latitude + (b.latitude - a.latitude) * f,
                    a.longitude + (b.longitude - a.longitude) * f,
                )
                googleMap.addMarker(
                    MarkerOptions().position(p)
                        .icon(icon)
                        .anchor(0.5f, 0.5f)
                        .rotation(bearingBetween(a, b))
                        .flat(true)
                        .zIndex(1.7f),
                )?.let { chevrons += it }
                placed++
                walked += CHEVRON_STEP_M
            }
            walked -= seg
        }
    }

    /** Seta branca cheia; o contorno carmim vem do traco por baixo. */
    private fun chevronBitmap(): Bitmap {
        val d = resources.displayMetrics.density
        val size = (13 * d).toInt()
        val bitmap = Bitmap.createBitmap(size, size, Bitmap.Config.ARGB_8888)
        val canvas = Canvas(bitmap)
        val paint = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = Color.WHITE }
        val w = size.toFloat()
        val path = android.graphics.Path().apply {
            moveTo(w * 0.5f, w * 0.16f)
            lineTo(w * 0.86f, w * 0.78f)
            lineTo(w * 0.5f, w * 0.58f)
            lineTo(w * 0.14f, w * 0.78f)
            close()
        }
        canvas.drawPath(path, paint)
        return bitmap
    }

    /** Reserva a área do cartão em baixo: o traço e os marcadores nunca ficam por baixo dele. */
    fun setBottomPadding(px: Int) {
        bottomPaddingPx = px.coerceAtLeast(0)
        applyPadding()
    }

    /**
     * Espessura do traço de navegação (vídeo 2026-10-30 15:16: grosso, com setas de sentido).
     * Usa o mesmo mecanismo da proposta (contorno + interior) mas mais largo.
     */
    var thickNavigation: Boolean = false
        set(value) { field = value; drawRoute() }

    /**
     * Balão branco com o nome da rua atual, encostado à seta (vídeo 2026-10-30 15:16:
     * "Avenida Sidónio Pais" por baixo do motorista).
     */
    fun setStreetLabel(text: String?) {
        streetLabel?.remove()
        streetLabel = null
        if (text.isNullOrBlank()) return
        val googleMap = map ?: return
        val here = deviceLocation?.let { LatLng(it.first, it.second) } ?: return
        streetLabel = googleMap.addMarker(
            MarkerOptions().position(here)
                .icon(BitmapDescriptorFactory.fromBitmap(streetLabelBitmap(text)))
                .anchor(0.5f, -0.45f)
                .zIndex(3f)
                .flat(false),
        )
    }

    /** Desenha o balão branco com o nome da rua (fonte escura, raio 6dp). */
    private fun streetLabelBitmap(text: String): Bitmap {
        val d = resources.displayMetrics.density
        val paint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            color = Color.rgb(32, 32, 32)
            textSize = 13f * d
            typeface = android.graphics.Typeface.create("sans-serif", android.graphics.Typeface.NORMAL)
        }
        val padH = 9f * d
        val padV = 6f * d
        val w = paint.measureText(text) + padH * 2
        val h = 13f * d + padV * 2
        val bitmap = Bitmap.createBitmap(w.toInt() + 8, h.toInt() + 8, Bitmap.Config.ARGB_8888)
        val canvas = Canvas(bitmap)
        val bg = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            color = Color.WHITE
            setShadowLayer(3f * d, 0f, 1f * d, Color.argb(60, 0, 0, 0))
        }
        val rect = RectF(4f, 4f, 4f + w, 4f + h)
        canvas.drawRoundRect(rect, 6f * d, 6f * d, bg)
        val baseline = 4f + h / 2f - (paint.descent() + paint.ascent()) / 2f
        canvas.drawText(text, 4f + padH, baseline, paint)
        return bitmap
    }

    /** Reserva a área do painel de manobras em cima (o marcador desce para a zona livre). */
    fun setTopPadding(px: Int) {
        topPaddingPx = px.coerceAtLeast(0)
        applyPadding()
    }

    /** Aplica o padding efetivo: painel em cima, barra em baixo e o offset da seta em navegação. */
    private fun applyPadding() {
        val extra = if (navigating) driverBottomPad else 0
        map?.setPadding(0, topPaddingPx, 0, bottomPaddingPx + extra)
    }

    /**
     * Modo da câmara, como o botão "Navegar" da Uber (vídeo 2026-10-30):
     *  - `navigating = true`  -> câmara colada ao motorista, inclinada (navegação) e mapa com
     *    o estilo do Google Maps (ruas e nomes visíveis).
     *  - `navigating = false` -> vista ampla: enquadra a rota toda (perspetiva do percurso).
     * Sem rota, a vista ampla fica no motorista com zoom afastado.
     */
    var navigating: Boolean = true
        set(value) {
            field = value
            applyMapStyle()
            // As setas de sentido so fazem sentido de perto; na vista geral saem.
            if (!value) clearChevrons() else drawRoute()
            if (value) followDriver() else wideView()
        }

    /** Estilo conforme o modo: navegação = ruas e nomes (Google Maps), repouso = mapa limpo. */
    private fun applyMapStyle() {
        val googleMap = map ?: return
        runCatching { googleMap.setMapStyle(MapStyleOptions(if (navigating) NAV_STYLE else MAP_STYLE)) }
        // Blocos das casas SEM 3D (pedido de 2026-10-30): sem volumes extrudidos no mapa.
        runCatching { googleMap.setBuildingsEnabled(false) }
    }

    /**
     * Câmara de navegação, igual ao Google Maps/Bolt do vídeo (2026-10-30 15:16):
     * o alvo da câmara **não** é o motorista — é um ponto ~70 m à frente na rota. Com a inclinação,
     * isso põe a seta do motorista em baixo (~78% da altura) e a rota a subir à frente.
     */
    private fun followDriver() {
        val googleMap = map ?: return
        val here = deviceLocation?.let { LatLng(it.first, it.second) }
            ?: routeData.firstOrNull()?.let { LatLng(it.first, it.second) }
            ?: return

        // Alvo: ponto à frente na rota (é o truque do Maps para a seta ficar em baixo).
        val target = pointAhead(here, AHEAD_TARGET_M) ?: here
        val course = bearingBetween(here, target).takeIf { target != here } ?: (bearing ?: 0f)

        // Sem padding extra: o enquadramento vem do alvo à frente + inclinação.
        driverBottomPad = 0
        applyPadding()

        googleMap.animateCamera(
            CameraUpdateFactory.newCameraPosition(
                com.google.android.gms.maps.model.CameraPosition.Builder()
                    .target(target)
                    .zoom(NAV_ZOOM)
                    .tilt(NAV_TILT)
                    .bearing(course)
                    .build(),
            ),
            NAV_ANIM_MS,
            null,
        )
        // A seta aponta sempre para cima (o mapa é que roda).
        driverMarker?.rotation = 0f
    }

    /** Ponto da rota a [meters] à frente da posição atual (para calcular o rumo de marcha). */
    private fun pointAhead(here: LatLng, meters: Double): LatLng? {
        if (routeData.size < 2) return null
        var walked = 0.0
        var prev = here
        for (i in routeData.indices) {
            val p = LatLng(routeData[i].first, routeData[i].second)
            walked += distance(prev, p)
            if (walked >= meters) return p
            prev = p
        }
        return routeData.lastOrNull()?.let { LatLng(it.first, it.second) }
    }

    private fun bearingBetween(a: LatLng, b: LatLng): Float {
        val p1 = Math.toRadians(a.latitude)
        val p2 = Math.toRadians(b.latitude)
        val dl = Math.toRadians(b.longitude - a.longitude)
        val x = Math.sin(dl) * Math.cos(p2)
        val y = Math.cos(p1) * Math.sin(p2) - Math.sin(p1) * Math.cos(p2) * Math.cos(dl)
        return ((Math.toDegrees(Math.atan2(x, y)) + 360) % 360).toFloat()
    }

    private fun distance(a: LatLng, b: LatLng): Double {
        val r = 6371000.0
        val p1 = Math.toRadians(a.latitude)
        val p2 = Math.toRadians(b.latitude)
        val dp = p2 - p1
        val dl = Math.toRadians(b.longitude - a.longitude)
        val h = Math.sin(dp / 2) * Math.sin(dp / 2) +
            Math.cos(p1) * Math.cos(p2) * Math.sin(dl / 2) * Math.sin(dl / 2)
        return 2 * r * Math.asin(Math.sqrt(h))
    }

    /** Vista ampla: enquadra a rota toda, para o motorista ver o percurso. */
    private fun wideView() {
        val googleMap = map ?: return
        driverBottomPad = 0
        applyPadding()
        if (routeData.size >= 2) {
            runCatching {
                val bounds = LatLngBounds.Builder().apply {
                    routeData.forEach { include(LatLng(it.first, it.second)) }
                }.build()
                val pad = (48 * resources.displayMetrics.density).toInt()
                googleMap.animateCamera(CameraUpdateFactory.newLatLngBounds(bounds, pad))
            }
            return
        }
        val p = deviceLocation?.let { LatLng(it.first, it.second) } ?: return
        googleMap.animateCamera(
            CameraUpdateFactory.newCameraPosition(
                com.google.android.gms.maps.model.CameraPosition.Builder()
                    .target(p).zoom(14f).tilt(0f).bearing(0f).build(),
            ),
        )
    }

    /** Destino da navegação atual (último ponto da rota), para a câmara o manter à vista. */
    private var focusedLatLng: LatLng? = null

    /** Recentra no motorista respeitando o padding (mapa com painéis). */
    private fun recenterOnDevice() {
        val p = deviceLocation?.let { LatLng(it.first, it.second) } ?: return
        map?.moveCamera(CameraUpdateFactory.newLatLngZoom(p, 15.5f))
    }

    /** Marcadores de recolha (azul) e destino (preto) da proposta. Sem ação ao toque. */
    private fun drawOfferMarkers() {
        val googleMap = map ?: return
        pickupMarker?.remove()
        dropoffMarker?.remove()
        pickupMarker = null
        dropoffMarker = null
        if (!showOfferMarkers) return
        val ends = offerEndpoints
        val start = ends?.first ?: routeData.firstOrNull() ?: return
        val end = ends?.second ?: routeData.lastOrNull() ?: return
        pickupMarker = googleMap.addMarker(
            MarkerOptions().position(LatLng(start.first, start.second))
                .icon(BitmapDescriptorFactory.fromBitmap(pickupPin()))
                .anchor(0.5f, 1f)
                .zIndex(3f),
        )
        dropoffMarker = googleMap.addMarker(
            MarkerOptions().position(LatLng(end.first, end.second))
                .icon(BitmapDescriptorFactory.fromBitmap(dropoffPin()))
                .anchor(0.5f, 1f)
                .zIndex(3f),
        )
    }

    /**
     * Marcador da paragem durante a navegação (vídeo 2026-10-30): um só pino.
     * Verde na recolha (fase 1), vermelho no destino (fase 2). O mapa de navegação
     * não mostra o outro extremo — é a diferença entre "ir buscar" e "levar".
     */
    var navStopKind: String? = null
        set(value) {
            if (field == value) return
            field = value
            drawNavStopMarker()
        }

    private var navStopPoint: Pair<Double, Double>? = null
        set(value) {
            field = value
            drawNavStopMarker()
        }

    private var navStopMarker: Marker? = null

    fun setNavStop(point: Pair<Double, Double>?, kind: String?) {
        navStopPoint = point
        navStopKind = kind
        drawNavStopMarker()
    }

    private fun drawNavStopMarker() {
        val googleMap = map ?: return
        navStopMarker?.remove()
        navStopMarker = null
        val p = navStopPoint ?: return
        val k = navStopKind ?: return
        val icon = if (k == "dropoff") dropoffPin() else pickupPin()
        navStopMarker = googleMap.addMarker(
            MarkerOptions().position(LatLng(p.first, p.second))
                .icon(BitmapDescriptorFactory.fromBitmap(icon))
                .anchor(0.5f, 1f)
                .zIndex(4f),
        )
    }

    /** Pill laranja com o chevron duplo de expansão e o tempo de espera (captura 120: "1-9 min"). */
    private fun pill(text: String): Bitmap {
        val d = resources.displayMetrics.density
        val textPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            color = Color.WHITE
            textSize = 12.5f * d
            typeface = android.graphics.Typeface.create(
                android.graphics.Typeface.create("sans-serif", android.graphics.Typeface.NORMAL),
                android.graphics.Typeface.NORMAL,
            )
        }
        val chevronW = 9f * d
        val padStart = 11f * d
        val padEnd = 12f * d
        val gap = 6f * d
        val height = 22 * d
        val width = padStart + chevronW + gap + textPaint.measureText(text) + padEnd
        val pad = 3 * d
        val bitmap = Bitmap.createBitmap(
            (width + pad * 2).toInt(), (height + pad * 2).toInt(), Bitmap.Config.ARGB_8888,
        )
        val canvas = Canvas(bitmap)
        val bg = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            color = Color.rgb(213, 93, 38)
            setShadowLayer(3f * d, 0f, 1.5f * d, Color.argb(70, 0, 0, 0))
        }
        canvas.drawRoundRect(
            RectF(pad, pad, pad + width, pad + height),
            height / 2f, height / 2f, bg,
        )
        val stroke = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            color = Color.argb(235, 255, 255, 255)
            style = Paint.Style.STROKE
            strokeWidth = 1.7f * d
            strokeCap = Paint.Cap.ROUND
            strokeJoin = Paint.Join.ROUND
        }
        // Chevron duplo ⌃⌃
        val left = pad + padStart
        val midY = pad + height / 2f
        listOf(0f, 3.2f * d).forEach { dy ->
            val path = android.graphics.Path().apply {
                moveTo(left, midY - 3.2f * d + dy)
                lineTo(left + chevronW / 2f, midY - 6.4f * d + dy)
                lineTo(left + chevronW, midY - 3.2f * d + dy)
            }
            canvas.drawPath(path, stroke)
        }
        val baseline = pad + height / 2f - (textPaint.descent() + textPaint.ascent()) / 2f
        canvas.drawText(text, left + chevronW + gap, baseline, textPaint)
        return bitmap
    }

    override fun onAttachedToWindow() {
        super.onAttachedToWindow()
        mapView.onResume()
    }

    override fun onDetachedFromWindow() {
        routeAnimator?.cancel()
        stopSweep()
        mapView.onPause()
        super.onDetachedFromWindow()
    }

    private companion object {
        /** Carmim do traco de navegacao, medido no video de 2026-10-30 (#E62042). */
        val NAV_ROUTE_RED = Color.rgb(230, 32, 66)

        /** Espacamento entre chevrons e quantos no maximo (para nao encher o mapa). */
        const val CHEVRON_STEP_M = 55.0
        const val CHEVRON_START_M = 25.0
        const val CHEVRON_MAX = 40

        /**
         * Pino do motorista: 1 = circulo perfeito. O original NAO e uma elipse (medi
         * 71x71 px no video de 2026-10-30), por isso deixou de se achatar o pino.
         */
        const val PIN_FLATTEN = 1.0f

        /** Duração do traço progressivo da proposta (a Uber desenha em ~1,2 s). */
        const val ROUTE_ANIM_MS = 1200L

        /** Efeito que percorre a linha: duração do ciclo e cauda escura (pontos da polilinha). */
        const val SWEEP_MS = 3200L
        const val SWEEP_TAIL = 40
        /** Intervalo entre redesenhos do varrimento (60 fps). */
        const val SWEEP_FRAME_MS = 16L

        val LISBOA = LatLng(38.7223, -9.1393)

        /** Centro e zoom medidos na captura 120 (área metropolitana de Lisboa). */
        val CENTER = LatLng(38.7225, -9.2330)
        const val ZOOM = 11.05f

        val HEAT_BOUNDS: LatLngBounds = LatLngBounds(
            LatLng(38.640, -9.375), LatLng(38.800, -9.090),
        )

        /** Pills de tempo de espera espalhadas pela área visível. */
        val PILLS = listOf(
            Triple(38.7440, -9.2200, "2-4 min"),
            Triple(38.7350, -9.2600, "4-6 min"),
            Triple(38.7180, -9.1750, "1-6 min"),
            Triple(38.7660, -9.1500, "1-9 min"),
            Triple(38.7130, -9.2290, "3-5 min"),
            Triple(38.7540, -9.1000, "2-7 min"),
            Triple(38.7040, -9.1200, "5-9 min"),
            Triple(38.7560, -9.2850, "6-11 min"),
            Triple(38.7280, -9.3100, "8-14 min"),
        )

        /**
         * Estilo de **navegação** (vídeo 2026-10-30): igual à experiência do Google Maps.
         * Ruas com nomes, quarteirões e parques visíveis, POIs discretos. É o estilo aplicado
         * sempre que o motorista está a navegar (recolha ou viagem).
         */
        val NAV_STYLE = """
        [
          {"elementType":"geometry","stylers":[{"color":"#F2F3F5"}]},
          {"elementType":"labels.text.fill","stylers":[{"color":"#5F6368"}]},
          {"elementType":"labels.text.stroke","stylers":[{"color":"#FFFFFF"}]},
          {"featureType":"administrative","elementType":"geometry","stylers":[{"visibility":"off"}]},
          {"featureType":"administrative.locality","elementType":"labels.text","stylers":[{"color":"#3C4043"},{"weight":1}]},
          {"featureType":"landscape.man_made","elementType":"geometry","stylers":[{"color":"#DDE0E5"},{"visibility":"on"}]},
          {"featureType":"landscape.man_made","elementType":"geometry.stroke","stylers":[{"color":"#CBD0D6"},{"visibility":"on"}]},
          {"featureType":"landscape.man_made","elementType":"labels","stylers":[{"visibility":"off"}]},
          {"featureType":"poi","stylers":[{"visibility":"off"}]},
          {"featureType":"poi.park","elementType":"geometry","stylers":[{"color":"#B7DFA8"},{"visibility":"on"}]},
          {"featureType":"poi.park","elementType":"labels","stylers":[{"visibility":"off"}]},
          {"featureType":"road","elementType":"geometry","stylers":[{"color":"#FFFFFF"}]},
          {"featureType":"road","elementType":"geometry.stroke","stylers":[{"color":"#D5D8DD"}]},
          {"featureType":"road","elementType":"labels","stylers":[{"visibility":"on"}]},
          {"featureType":"road","elementType":"labels.text.fill","stylers":[{"color":"#4A4F55"}]},
          {"featureType":"road.arterial","elementType":"geometry","stylers":[{"color":"#FFFFFF"}]},
          {"featureType":"road.arterial","elementType":"labels.text.fill","stylers":[{"color":"#4A4F55"}]},
          {"featureType":"road.highway","elementType":"geometry","stylers":[{"color":"#FDD663"}]},
          {"featureType":"road.highway","elementType":"geometry.stroke","stylers":[{"color":"#E8C34A"}]},
          {"featureType":"road.highway","elementType":"labels.text.fill","stylers":[{"color":"#5F4B00"}]},
          {"featureType":"transit","stylers":[{"visibility":"off"}]},
          {"featureType":"water","elementType":"geometry","stylers":[{"color":"#C3DCF5"}]},
          {"featureType":"water","elementType":"labels","stylers":[{"visibility":"off"}]}
        ]
        """.trimIndent()

        /** Zoom e inclinação do modo navegação (vídeo 2026-10-30 15:16: bem deitado, tipo Maps). */
        const val NAV_ZOOM = 18.3f
        const val NAV_TILT = 66f
        const val NAV_ANIM_MS = 700
        /** Ponto à frente usado como alvo da câmara (m). Define a altura da seta no ecrã. */
        const val AHEAD_TARGET_M = 120.0
        /** Distância à frente usada para o rumo de marcha (m). */
        const val AHEAD_M = 45.0

        /** Estilo do mapa do original: fundo azul-cinza, vias brancas, rápidas azuladas, sem POIs. */
        val MAP_STYLE = """
        [
          {"elementType":"geometry","stylers":[{"color":"#EDF0F5"}]},
          {"elementType":"labels.icon","stylers":[{"visibility":"off"}]},
          {"elementType":"labels.text.fill","stylers":[{"color":"#6E7580"}]},
          {"elementType":"labels.text.stroke","stylers":[{"color":"#FFFFFF"}]},
          {"featureType":"administrative","elementType":"geometry","stylers":[{"visibility":"off"}]},
          {"featureType":"administrative.locality","elementType":"labels.text","stylers":[{"color":"#5F6672"},{"visibility":"on"},{"weight":0.6}]},
          {"featureType":"landscape.man_made","elementType":"geometry","stylers":[{"color":"#E9ECF1"}]},
          {"featureType":"poi","stylers":[{"visibility":"off"}]},
          {"featureType":"poi.park","elementType":"geometry","stylers":[{"color":"#EFF3EB"},{"visibility":"on"}]},
          {"featureType":"poi.park","elementType":"labels","stylers":[{"visibility":"off"}]},
          {"featureType":"road","elementType":"geometry","stylers":[{"color":"#FFFFFF"}]},
          {"featureType":"road","elementType":"geometry.stroke","stylers":[{"color":"#E4E8EF"}]},
          {"featureType":"road","elementType":"labels","stylers":[{"visibility":"off"}]},
          {"featureType":"road.arterial","elementType":"geometry","stylers":[{"color":"#FFFFFF"}]},
          {"featureType":"road.highway","elementType":"geometry","stylers":[{"color":"#98A6CE"}]},
          {"featureType":"road.highway","elementType":"geometry.stroke","stylers":[{"color":"#98A6CE"}]},
          {"featureType":"road.highway.controlled_access","elementType":"geometry","stylers":[{"color":"#8E9CC9"}]},
          {"featureType":"transit","stylers":[{"visibility":"off"}]},
          {"featureType":"water","elementType":"geometry","stylers":[{"color":"#BAD8FB"}]},
          {"featureType":"water","elementType":"labels","stylers":[{"visibility":"off"}]}
        ]
        """.trimIndent()
    }
}
