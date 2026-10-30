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

    /** Largura fixa da barra em dp (0 = ocupa todo o espaço da ranhura). Rendimentos usa 16dp. */
    var barWidthDp: Float = 0f
        set(value) { field = value; invalidate() }

    /** Espaço entre barras em dp quando a largura é fixa. */
    var gapDp: Float = 7f
        set(value) { field = value; invalidate() }

    /** Alinha o conjunto de barras à direita (gráfico da semana, captura 062). */
    var alignRight: Boolean = false
        set(value) { field = value; invalidate() }

    /** Altura máxima das barras em dp (0 = usa a altura toda da vista). */
    var maxBarHeightDp: Float = 0f
        set(value) { field = value; invalidate() }

    private val paint = Paint(Paint.ANTI_ALIAS_FLAG)

    override fun onDraw(canvas: Canvas) {
        if (values.isEmpty()) return
        val d = resources.displayMetrics.density
        // Escala mínima de 1: uma semana sem valores mostra barras baixas e não todas à altura máxima.
        val max = values.max().coerceAtLeast(1f)
        val minBar = 10f * d
        val gap = if (barWidthDp > 0f) gapDp * d else 3f * d
        val bw = if (barWidthDp > 0f) barWidthDp * d else (width - gap * (values.size - 1)) / values.size
        val total = bw * values.size + gap * (values.size - 1)
        val startX = if (alignRight) (width - total).coerceAtLeast(0f) else 0f
        val maxH = if (maxBarHeightDp > 0f) maxBarHeightDp * d else height.toFloat()
        values.forEachIndexed { i, v ->
            paint.color = when (i) { highlight -> highlightColor; accentIndex -> accentColor; else -> barColor }
            val h = (maxH * v / max).coerceAtLeast(minBar).coerceAtMost(height.toFloat())
            val left = startX + i * (bw + gap)
            canvas.drawRect(RectF(left, height - h, left + bw, height.toFloat()), paint)
        }
    }
}
