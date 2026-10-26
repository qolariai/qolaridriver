package com.qolari.drivereplica.ui.home

import android.content.Context
import android.graphics.Canvas
import android.graphics.Paint
import android.graphics.RectF
import android.util.AttributeSet
import android.view.View

/** Gráfico de barras simples das secções de tendências (capturas 060_s2 e 060_s3). Dados de exemplo, definidos pelo ecrã. */
class BarChartView @JvmOverloads constructor(context: Context, attrs: AttributeSet? = null) : View(context, attrs) {

    var values: List<Float> = emptyList()
        set(value) { field = value; invalidate() }

    /** Barra a realçar (hora atual). */
    var highlight: Int = -1
        set(value) { field = value; invalidate() }

    var barColor: Int = 0xFF5E5E5E.toInt()
    var highlightColor: Int = 0xFF111111.toInt()
    var accentIndex: Int = -1
    var accentColor: Int = 0xFFF6BC2F.toInt()

    private val paint = Paint(Paint.ANTI_ALIAS_FLAG)

    override fun onDraw(canvas: Canvas) {
        if (values.isEmpty()) return
        // Escala mínima de 1: uma semana sem valores mostra barras baixas e não todas à altura máxima.
        val max = values.max().coerceAtLeast(1f)
        val minBar = resources.displayMetrics.density * 3f
        val gap = resources.displayMetrics.density * 3f
        val bw = (width - gap * (values.size - 1)) / values.size
        values.forEachIndexed { i, v ->
            paint.color = when (i) { highlight -> highlightColor; accentIndex -> accentColor; else -> barColor }
            val top = minOf(height - (height * v / max), height - minBar)
            canvas.drawRect(RectF(i * (bw + gap), top, i * (bw + gap) + bw, height.toFloat()), paint)
        }
    }
}
