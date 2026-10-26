package com.qolari.drivereplica.ui.home

import android.content.Context
import android.graphics.Canvas
import android.graphics.Paint
import android.graphics.Path
import android.graphics.RectF
import android.util.AttributeSet
import android.view.View
import androidx.core.content.ContextCompat
import com.qolari.drivereplica.R
import kotlin.random.Random

/**
 * Miniatura de mapa desenhada (cartões de oportunidades/promoções). O mapa interativo dos ecrãs
 * principais é o [GoogleMapView] (Google Maps SDK). Desenho próprio e determinístico; não usa
 * assets da app original.
 */
class MapPlaceholderView @JvmOverloads constructor(context: Context, attrs: AttributeSet? = null) : View(context, attrs) {

    /** Mostra as zonas de procura a cor-de-rosa e os marcadores (o mapa da Página inicial tem-nos; o de fundo também). */
    var showDemand = true
        set(value) { field = value; invalidate() }

    /** Rota (lat, lng) a desenhar por cima do mapa, ajustada à metade de cima do ecrã. Vazia = sem traço. */
    var route: List<Pair<Double, Double>> = emptyList()
        set(value) { field = value; invalidate() }

    private val routePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = 0xFF222222.toInt(); style = Paint.Style.STROKE; strokeCap = Paint.Cap.ROUND; strokeJoin = Paint.Join.ROUND
    }
    private val seed = 7
    private val land = paint(0xFFEDF0F5.toInt())
    private val water = paint(0xFFC4D8EE.toInt())
    private val park = paint(0xFFD3E8CF.toInt())
    private val road = paint(0xFFFFFFFF.toInt(), Paint.Style.STROKE, 3f)
    private val roadMinor = paint(0xFFDDE3EC.toInt(), Paint.Style.STROKE, 1.5f)
    private val heat = paint(0x66D98BB8)
    private val pill = paint(ContextCompat.getColor(context, R.color.qd_core_dark_red400))
    private val pillText = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = 0xFFFFFFFF.toInt(); textAlign = Paint.Align.CENTER }
    private val boltBg = paint(ContextCompat.getColor(context, R.color.qd_core_purple800))
    private val boltFg = paint(0xFFFFFFFF.toInt())
    private val me = paint(0xFF111111.toInt())
    private val meRing = paint(0xFFFFFFFF.toInt())
    private val label = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = 0xFF5E6672.toInt(); typeface = android.graphics.Typeface.DEFAULT_BOLD }

    private fun paint(color: Int, style: Paint.Style = Paint.Style.FILL, strokeDp: Float = 0f) = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        this.color = color
        this.style = style
        strokeWidth = strokeDp * resources.displayMetrics.density
        strokeCap = Paint.Cap.ROUND
        strokeJoin = Paint.Join.ROUND
    }

    private fun dp(v: Float) = v * resources.displayMetrics.density

    override fun onDraw(canvas: Canvas) {
        val w = width.toFloat()
        val h = height.toFloat()
        canvas.drawRect(0f, 0f, w, h, land)
        val rnd = Random(seed)

        // Água: faixa sinuosa em baixo e uma mancha à direita (estuário).
        val sea = Path().apply {
            moveTo(0f, h * 0.88f)
            cubicTo(w * 0.25f, h * 0.80f, w * 0.5f, h * 0.97f, w * 0.75f, h * 0.85f)
            cubicTo(w * 0.88f, h * 0.80f, w * 0.95f, h * 0.78f, w, h * 0.80f)
            lineTo(w, h); lineTo(0f, h); close()
        }
        canvas.drawPath(sea, water)
        canvas.drawOval(RectF(w * 0.78f, h * 0.18f, w * 1.15f, h * 0.55f), water)

        // Parques.
        repeat(5) {
            val cx = w * (0.1f + 0.8f * rnd.nextFloat())
            val cy = h * (0.15f + 0.6f * rnd.nextFloat())
            canvas.drawOval(RectF(cx - dp(26f), cy - dp(16f), cx + dp(26f), cy + dp(16f)), park)
        }

        // Estradas: rede irregular de segmentos finos e algumas vias principais.
        repeat(34) {
            val x1 = w * rnd.nextFloat(); val y1 = h * rnd.nextFloat()
            canvas.drawLine(x1, y1, x1 + (rnd.nextFloat() - 0.5f) * w * 0.5f, y1 + (rnd.nextFloat() - 0.5f) * h * 0.5f, roadMinor)
        }
        repeat(6) {
            val x1 = w * rnd.nextFloat(); val y1 = h * rnd.nextFloat()
            canvas.drawLine(x1, y1, x1 + (rnd.nextFloat() - 0.5f) * w * 0.9f, y1 + (rnd.nextFloat() - 0.5f) * h * 0.9f, road)
        }

        label.textSize = dp(13f)
        canvas.drawText("Lisboa", w * 0.68f, h * 0.76f, label)
        canvas.drawText("Oeiras", w * 0.04f, h * 0.88f, label)

        if (showDemand) {
            repeat(4) {
                val cx = w * (0.15f + 0.7f * rnd.nextFloat())
                val cy = h * (0.15f + 0.6f * rnd.nextFloat())
                canvas.drawCircle(cx, cy, dp(44f + 20f * rnd.nextFloat()), heat)
            }
            repeat(3) { bolt(canvas, w * (0.18f + 0.64f * rnd.nextFloat()), h * (0.2f + 0.55f * rnd.nextFloat())) }
            pill(canvas, "1-4 min", w * 0.30f, h * 0.27f)
            pill(canvas, "1-6 min", w * 0.46f, h * 0.55f)
            pill(canvas, "1-5 min", w * 0.80f, h * 0.38f)
            pill(canvas, "1-9 min", w * 0.14f, h * 0.62f)
        }

        drawRoute(canvas, w, h)

        // Posição do motorista.
        val cx = w * 0.5f; val cy = h * 0.46f
        canvas.drawCircle(cx, cy, dp(15f), meRing)
        canvas.drawCircle(cx, cy, dp(11f), me)
        val arrow = Path().apply {
            moveTo(cx, cy - dp(6f)); lineTo(cx + dp(5f), cy + dp(5f)); lineTo(cx, cy + dp(2f)); lineTo(cx - dp(5f), cy + dp(5f)); close()
        }
        canvas.drawPath(arrow, boltFg)
    }

    /** Traço da rota com marcadores de recolha (círculo) e destino (quadrado), como nas capturas 100_online_*. */
    private fun drawRoute(canvas: Canvas, w: Float, h: Float) {
        if (route.size < 2) return
        val minLat = route.minOf { it.first }; val maxLat = route.maxOf { it.first }
        val minLng = route.minOf { it.second }; val maxLng = route.maxOf { it.second }
        val pad = dp(32f)
        val areaH = h * 0.45f
        val spanLat = (maxLat - minLat).coerceAtLeast(1e-5); val spanLng = (maxLng - minLng).coerceAtLeast(1e-5)
        val scale = minOf((w - 2 * pad) / spanLng, (areaH - pad) / spanLat).toFloat()
        val ox = (w - spanLng.toFloat() * scale) / 2f
        val oy = dp(110f)
        fun px(p: Pair<Double, Double>) = ox + ((p.second - minLng) * scale).toFloat() to oy + ((maxLat - p.first) * scale).toFloat()
        routePaint.strokeWidth = dp(4f)
        val path = Path()
        route.forEachIndexed { i, p -> val (x, y) = px(p); if (i == 0) path.moveTo(x, y) else path.lineTo(x, y) }
        canvas.drawPath(path, routePaint)
        val (sx, sy) = px(route.first()); val (ex, ey) = px(route.last())
        canvas.drawCircle(sx, sy, dp(8f), meRing); canvas.drawCircle(sx, sy, dp(5f), me)
        canvas.drawRect(ex - dp(8f), ey - dp(8f), ex + dp(8f), ey + dp(8f), me)
        canvas.drawRect(ex - dp(4f), ey - dp(4f), ex + dp(4f), ey + dp(4f), meRing)
    }

    private fun pill(canvas: Canvas, text: String, cx: Float, cy: Float) {
        pillText.textSize = dp(12f)
        val tw = pillText.measureText(text)
        val rect = RectF(cx - tw / 2 - dp(9f), cy - dp(10f), cx + tw / 2 + dp(9f), cy + dp(10f))
        canvas.drawRoundRect(rect, dp(10f), dp(10f), pill)
        canvas.drawText(text, cx, cy + dp(4f), pillText)
    }

    private fun bolt(canvas: Canvas, cx: Float, cy: Float) {
        canvas.drawCircle(cx, cy, dp(14f), boltBg)
        val p = Path().apply {
            moveTo(cx + dp(2f), cy - dp(8f)); lineTo(cx - dp(5f), cy + dp(1f)); lineTo(cx, cy + dp(1f))
            lineTo(cx - dp(2f), cy + dp(8f)); lineTo(cx + dp(5f), cy - dp(1f)); lineTo(cx, cy - dp(1f)); close()
        }
        canvas.drawPath(p, boltFg)
    }
}
