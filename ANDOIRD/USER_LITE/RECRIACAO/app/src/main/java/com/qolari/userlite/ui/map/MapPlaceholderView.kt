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
 * Miniatura de mapa desenhada. O mapa interativo dos ecrãs principais é o [GoogleMapView]
 * (Google Maps SDK); este desenho fica para composições decorativas. Sem assets da app original.
 */
class MapPlaceholderView @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null,
) : View(context, attrs) {

    var route: List<Pair<Double, Double>> = emptyList()
        set(value) { field = value; invalidate() }

    var driver: Pair<Double, Double>? = null
        set(value) { field = value; invalidate() }

    var showUser: Boolean = true
        set(value) { field = value; invalidate() }

    /** Zoom e recentragem do mapa desenhado (botoes do ecra inicial). */
    var camera: MapCamera = MapCamera()
        set(value) { field = value; invalidate() }

    /** Posicao obtida do aparelho; quando existe, o marcador muda de cor. */
    var userLocation: Pair<Double, Double>? = null
        set(value) { field = value; invalidate() }

    fun zoomIn() { camera = camera.zoomIn() }

    fun zoomOut() { camera = camera.zoomOut() }

    fun recenter() { camera = camera.recenter() }

    private val seed = 11
    private val land = paint(0xFFF2F2F2.toInt())
    private val water = paint(0xFFC9DDF0.toInt())
    private val park = paint(0xFFCBE6C8.toInt())
    private val road = paint(0xFFFFFFFF.toInt(), Paint.Style.STROKE, 4f)
    private val roadMinor = paint(0xFFE2E6EC.toInt(), Paint.Style.STROKE, 1.2f)
    private val blueRoad = paint(0xFFB8C9F2.toInt(), Paint.Style.STROKE, 8f)
    private val routePaint = paint(0xFF111111.toInt(), Paint.Style.STROKE, 4f)
    private val label = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = 0xFF6B7280.toInt()
        textSize = dp(12f)
        typeface = android.graphics.Typeface.DEFAULT_BOLD
        letterSpacing = 0.08f
    }
    private val userFill = paint(0xFF3B6CE9.toInt())
    private val userFix = paint(0xFF0E8A4A.toInt())
    private val white = paint(0xFFFFFFFF.toInt())
    private val black = paint(0xFF111111.toInt())

    private fun paint(color: Int, style: Paint.Style = Paint.Style.FILL, widthDp: Float = 0f) =
        Paint(Paint.ANTI_ALIAS_FLAG).apply {
            this.color = color
            this.style = style
            strokeWidth = dp(widthDp)
            strokeCap = Paint.Cap.ROUND
            strokeJoin = Paint.Join.ROUND
        }

    private fun dp(v: Float) = v * resources.displayMetrics.density

    override fun onDraw(canvas: Canvas) {
        val w = width.toFloat()
        val h = height.toFloat()
        canvas.drawRect(0f, 0f, w, h, land)

        canvas.save()
        canvas.scale(camera.scale, camera.scale, w * 0.5f, h * 0.43f)

        // Água a sudeste (Tejo).
        val sea = Path().apply {
            moveTo(w * 0.52f, h)
            cubicTo(w * 0.62f, h * 0.82f, w * 0.82f, h * 0.86f, w, h * 0.72f)
            lineTo(w, h)
            close()
        }
        canvas.drawPath(sea, water)

        // Parques.
        val rnd = Random(seed)
        repeat(5) {
            val cx = w * (0.10f + 0.78f * rnd.nextFloat())
            val cy = h * (0.10f + 0.55f * rnd.nextFloat())
            canvas.drawOval(RectF(cx - dp(34f), cy - dp(20f), cx + dp(34f), cy + dp(20f)), park)
        }

        // Rede de ruas.
        repeat(38) {
            val x1 = w * rnd.nextFloat()
            val y1 = h * rnd.nextFloat()
            canvas.drawLine(x1, y1, x1 + (rnd.nextFloat() - 0.5f) * w * 0.55f,
                y1 + (rnd.nextFloat() - 0.5f) * h * 0.55f, roadMinor)
        }
        repeat(7) {
            val x1 = w * rnd.nextFloat()
            val y1 = h * rnd.nextFloat()
            canvas.drawLine(x1, y1, x1 + (rnd.nextFloat() - 0.5f) * w, y1 + (rnd.nextFloat() - 0.5f) * h, road)
        }

        // Via rápida azul, como nas capturas.
        val a37 = Path().apply {
            moveTo(-dp(10f), h * 0.14f)
            cubicTo(w * 0.28f, h * 0.20f, w * 0.45f, h * 0.34f, w * 0.66f, h * 0.32f)
            cubicTo(w * 0.80f, h * 0.31f, w * 0.92f, h * 0.38f, w + dp(10f), h * 0.40f)
        }
        canvas.drawPath(a37, blueRoad)
        canvas.drawText("A37", w * 0.06f, h * 0.18f, label)
        canvas.drawText("LISBOA", w * 0.63f, h * 0.58f, label)
        canvas.drawText("CAMPO GRANDE", w * 0.44f, h * 0.45f, label)

        if (route.size >= 2) drawRoute(canvas, w, h)
        if (driver != null) drawDriver(canvas, w, h, driver!!)

        if (showUser) {
            val cx = w * 0.50f
            val cy = h * 0.43f
            canvas.drawCircle(cx, cy, dp(11f), white)
            canvas.drawCircle(cx, cy, dp(7.5f), if (userLocation != null) userFix else userFill)
        }
        canvas.restore()
    }

    private fun bounds(): RectF? {
        if (route.size < 2) return null
        val minLat = route.minOf { it.first }
        val maxLat = route.maxOf { it.first }
        val minLng = route.minOf { it.second }
        val maxLng = route.maxOf { it.second }
        return RectF(
            minLng.toFloat(), minLat.toFloat(), maxLng.toFloat(), maxLat.toFloat()
        )
    }

    private fun project(p: Pair<Double, Double>, w: Float, h: Float, b: RectF): Pair<Float, Float> {
        val pad = dp(32f)
        val spanLng = (b.right - b.left).coerceAtLeast(1e-5f)
        val spanLat = (b.bottom - b.top).coerceAtLeast(1e-5f)
        val scale = minOf((w - 2 * pad) / spanLng, (h * 0.52f - 2 * pad) / spanLat)
        val ox = (w - spanLng * scale) / 2f
        val oy = pad + dp(16f)
        return ox + ((p.second.toFloat() - b.left) * scale) to oy + ((b.bottom - p.first.toFloat()) * scale)
    }

    private fun drawRoute(canvas: Canvas, w: Float, h: Float) {
        val b = bounds() ?: return
        val path = Path()
        route.forEachIndexed { i, p ->
            val (x, y) = project(p, w, h, b)
            if (i == 0) path.moveTo(x, y) else path.lineTo(x, y)
        }
        canvas.drawPath(path, routePaint)
        val (sx, sy) = project(route.first(), w, h, b)
        val (ex, ey) = project(route.last(), w, h, b)
        canvas.drawCircle(sx, sy, dp(9f), white)
        canvas.drawCircle(sx, sy, dp(5.5f), black)
        canvas.drawRect(ex - dp(8f), ey - dp(8f), ex + dp(8f), ey + dp(8f), black)
        canvas.drawRect(ex - dp(3f), ey - dp(3f), ex + dp(3f), ey + dp(3f), white)
    }

    private fun drawDriver(canvas: Canvas, w: Float, h: Float, p: Pair<Double, Double>) {
        val b = bounds()
        val (x, y) = if (b != null) project(p, w, h, b) else (w * 0.42f to h * 0.30f)
        canvas.drawCircle(x, y, dp(17f), white)
        canvas.drawCircle(x, y, dp(14f), black)
        val car = Path().apply {
            moveTo(x - dp(8f), y + dp(2f))
            lineTo(x - dp(5f), y - dp(4f))
            lineTo(x + dp(4f), y - dp(4f))
            lineTo(x + dp(8f), y + dp(2f))
            lineTo(x + dp(8f), y + dp(5f))
            lineTo(x - dp(8f), y + dp(5f))
            close()
        }
        canvas.drawPath(car, white)
        canvas.drawCircle(x - dp(4.5f), y + dp(5f), dp(2f), black)
        canvas.drawCircle(x + dp(4.5f), y + dp(5f), dp(2f), black)
    }
}
