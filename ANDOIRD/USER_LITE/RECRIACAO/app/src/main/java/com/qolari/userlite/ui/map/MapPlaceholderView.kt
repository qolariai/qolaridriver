package com.qolari.userlite.ui.map

import android.content.Context
import android.graphics.Canvas
import android.graphics.Paint
import android.graphics.Path
import android.graphics.RectF
import android.util.AttributeSet
import android.view.View
import kotlin.random.Random

/**
 * Mapa desenhado (espaço reservado): quarteirões irregulares sobre fundo de ruas, água, parques e a etiqueta da A37.
 * Determinístico (mesma semente = mesmo mapa), sem rede nem chave de API.
 */
class MapPlaceholderView @JvmOverloads constructor(context: Context, attrs: AttributeSet? = null) : View(context, attrs) {

    /** Rota a desenhar por cima do mapa (lista de lat/lng). Vazia = sem traço. */
    var route: List<Pair<Double, Double>> = emptyList()
        set(value) { field = value; invalidate() }

    /** Ponto de recolha e destino (lat/lng), marcados quando existem. */
    var pickup: Pair<Double, Double>? = null
        set(value) { field = value; invalidate() }
    var dropoff: Pair<Double, Double>? = null
        set(value) { field = value; invalidate() }

    /** Motorista a caminho (captura de viagem a caminho). */
    var driver: Pair<Double, Double>? = null
        set(value) { field = value; invalidate() }

    /** Mostra o ponto do utilizador (escondido quando o mapa é só da rota). */
    var showUser: Boolean = true
        set(value) { field = value; invalidate() }

    /** Última localização conhecida; o "recentrar" apenas volta a desenhar com o ponto ao centro. */
    var userLocation: Pair<Double, Double>? = null
        set(value) { field = value; invalidate() }

    private var zoom = 1f

    fun zoomIn() { zoom = (zoom + 0.2f).coerceAtMost(1.8f); invalidate() }
    fun zoomOut() { zoom = (zoom - 0.2f).coerceAtLeast(0.7f); invalidate() }
    fun recenter() { invalidate() }

    private val d = resources.displayMetrics.density
    private val street = fill(0xFFFFFFFF.toInt())
    private val block = fill(0xFFE8EDF3.toInt())
    private val blockAlt = fill(0xFFEEF2F7.toInt())
    private val water = fill(0xFFC6DBEF.toInt())
    private val park = fill(0xFFD3E7CB.toInt())
    private val avenue = stroke(0xFFFFFFFF.toInt(), 13f)
    private val avenueLine = stroke(0xFFE0E6ED.toInt(), 1f)
    private val routePaint = stroke(0xFF222222.toInt(), 4f)
    private val me = fill(0xFF111111.toInt())
    private val meRing = fill(0xFFFFFFFF.toInt())
    private val label = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = 0xFF7C8794.toInt()
        typeface = android.graphics.Typeface.DEFAULT_BOLD
    }
    private val labelHalo = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = 0xFFFFFFFF.toInt()
        style = Paint.Style.STROKE
    }
    private val highway = stroke(ColorA37, 7f)
    private val highwayLabel = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = ColorA37
        textAlign = Paint.Align.CENTER
        typeface = android.graphics.Typeface.DEFAULT_BOLD
    }

    private fun fill(color: Int) = Paint(Paint.ANTI_ALIAS_FLAG).apply { this.color = color }
    private fun stroke(color: Int, widthDp: Float) = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        this.color = color
        style = Paint.Style.STROKE
        strokeWidth = widthDp * resources.displayMetrics.density
        strokeCap = Paint.Cap.ROUND
        strokeJoin = Paint.Join.ROUND
    }

    private fun dp(v: Float) = v * d

    override fun onDraw(canvas: Canvas) {
        val w = width.toFloat()
        val h = height.toFloat()
        canvas.drawColor(0xFFFFFFFF.toInt())
        canvas.save()
        canvas.scale(zoom, zoom, w / 2f, h / 2f)
        val rnd = Random(11)

        drawWater(canvas, w, h)
        drawBlocks(canvas, w, h, rnd)
        drawParks(canvas, w, h)
        drawAvenue(canvas, w, h, rnd)
        drawLabels(canvas, w, h)

        drawRoute(canvas, w, h)
        if (showUser) {
            canvas.drawCircle(w * 0.52f, h * 0.48f, dp(9f), meRing)
            canvas.drawCircle(w * 0.52f, h * 0.48f, dp(6f), me)
        }
        driver?.let {
            val (x, y) = routePos(it, w, h, route)
            canvas.drawCircle(x, y, dp(8f), meRing)
            canvas.drawCircle(x, y, dp(5f), highway)
        }
        canvas.restore()
    }

    private fun drawWater(canvas: Canvas, w: Float, h: Float) {
        val sea = Path().apply {
            moveTo(w * 0.90f, -dp(2f))
            cubicTo(w * 0.84f, h * 0.30f, w * 0.94f, h * 0.62f, w * 0.86f, h)
            lineTo(w, h); lineTo(w, -dp(2f)); close()
        }
        canvas.drawPath(sea, water)
    }

    /** Quarteirões com desvio e tamanhos diferentes; a folga branca entre eles são as ruas. */
    private fun drawBlocks(canvas: Canvas, w: Float, h: Float, rnd: Random) {
        val cellsX = 10
        val cellsY = 16
        val cw = w / cellsX
        val ch = h / cellsY
        for (cx in 0 until cellsX) for (cy in 0 until cellsY) {
            val jx = (rnd.nextFloat() - 0.5f) * cw * 0.22f
            val jy = (rnd.nextFloat() - 0.5f) * ch * 0.22f
            val left = cx * cw + dp(3f) + jx
            val top = cy * ch + dp(3f) + jy
            val right = (cx + 1) * cw - dp(3f) + jx * 0.35f
            val bottom = (cy + 1) * ch - dp(3f) + jy * 0.35f
            if (right - left < dp(12f) || bottom - top < dp(12f)) continue
            if (rnd.nextFloat() < 0.42f && right - left > dp(40f)) {
                val mid = left + (right - left) * (0.38f + rnd.nextFloat() * 0.24f)
                canvas.drawRoundRect(RectF(left, top, mid - dp(2f), bottom), dp(3f), dp(3f), block)
                canvas.drawRoundRect(RectF(mid + dp(2f), top, right, bottom), dp(3f), dp(3f), blockAlt)
            } else {
                canvas.drawRoundRect(
                    RectF(left, top, right, bottom), dp(3f), dp(3f),
                    if (rnd.nextFloat() < 0.5f) block else blockAlt,
                )
            }
        }
    }

    private fun drawParks(canvas: Canvas, w: Float, h: Float) {
        canvas.drawRoundRect(RectF(w * 0.03f, h * 0.56f, w * 0.30f, h * 0.84f), dp(12f), dp(12f), park)
        canvas.drawRoundRect(RectF(w * 0.60f, h * 0.08f, w * 0.76f, h * 0.24f), dp(10f), dp(10f), park)
    }

    private fun drawAvenue(canvas: Canvas, w: Float, h: Float, rnd: Random) {
        val path = Path().apply {
            moveTo(-dp(8f), h * (0.62f + rnd.nextFloat() * 0.08f))
            cubicTo(w * 0.32f, h * 0.5f, w * 0.62f, h * 0.36f, w + dp(8f), h * 0.30f)
        }
        canvas.drawPath(path, avenue)
        canvas.drawPath(path, avenueLine)

        val a37 = Path().apply {
            moveTo(-dp(6f), h * 0.20f)
            cubicTo(w * 0.38f, h * 0.10f, w * 0.64f, h * 0.36f, w + dp(6f), h * 0.18f)
        }
        canvas.drawPath(a37, highway)
    }

    private fun drawLabels(canvas: Canvas, w: Float, h: Float) {
        label.textSize = dp(10f)
        labelHalo.textSize = dp(10f)
        labelHalo.strokeWidth = dp(3f)
        fun text(t: String, x: Float, y: Float, p: Paint) {
            canvas.drawText(t, x, y, labelHalo)
            canvas.drawText(t, x, y, p)
        }
        text("Campo Grande", w * 0.04f, h * 0.54f, label)
        text("Lisboa", w * 0.64f, h * 0.70f, label)
        highwayLabel.textSize = dp(10f)
        text("A37", w * 0.47f, h * 0.24f, highwayLabel)
    }

    private fun drawRoute(canvas: Canvas, w: Float, h: Float) {
        if (route.size < 2) return
        val path = Path()
        route.forEachIndexed { i, p ->
            val (x, y) = routePos(p, w, h, route)
            if (i == 0) path.moveTo(x, y) else path.lineTo(x, y)
        }
        canvas.drawPath(path, routePaint)
        pickup?.let { val (x, y) = routePos(it, w, h, route); canvas.drawCircle(x, y, dp(6f), meRing); canvas.drawCircle(x, y, dp(4f), me) }
        dropoff?.let { val (x, y) = routePos(it, w, h, route); canvas.drawRect(x - dp(6f), y - dp(6f), x + dp(6f), y + dp(6f), me) }
    }

    /** Converte um par lat/lng para coordenadas do ecrã (área ajustada ao tamanho da vista). */
    private fun routePos(p: Pair<Double, Double>, w: Float, h: Float, points: List<Pair<Double, Double>>): Pair<Float, Float> {
        val all = if (points.size >= 2) points else listOfNotNull(userLocation, p)
        val minLat = all.minOf { it.first }; val maxLat = all.maxOf { it.first }
        val minLng = all.minOf { it.second }; val maxLng = all.maxOf { it.second }
        val pad = dp(24f)
        val spanLat = (maxLat - minLat).coerceAtLeast(1e-5)
        val spanLng = (maxLng - minLng).coerceAtLeast(1e-5)
        val scale = minOf((w - 2 * pad) / spanLng, (h - 2 * pad) / spanLat).toFloat()
        val ox = (w - spanLng.toFloat() * scale) / 2f
        val oy = (h - spanLat.toFloat() * scale) / 2f
        return ox + ((p.second - minLng) * scale).toFloat() to oy + ((maxLat - p.first) * scale).toFloat()
    }

    private companion object {
        val ColorA37 = 0xFF4C93F7.toInt()
    }
}
