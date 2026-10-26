package com.qolari.drivereplica.ui.discover

import android.content.Context
import android.graphics.Canvas
import android.graphics.Paint
import android.util.AttributeSet
import android.view.View

/** Pontos de paginação dos cartões de promoções (captura 061: 5 pontos, o ativo mais escuro). */
class DotsView @JvmOverloads constructor(context: Context, attrs: AttributeSet? = null) : View(context, attrs) {

    var count = 0
        set(value) { field = value; requestLayout(); invalidate() }
    var selected = 0
        set(value) { field = value; invalidate() }

    private val paint = Paint(Paint.ANTI_ALIAS_FLAG)
    private val d = resources.displayMetrics.density

    override fun onMeasure(widthMeasureSpec: Int, heightMeasureSpec: Int) {
        val w = if (count == 0) 0 else ((count * 8 + (count - 1) * 8) * d).toInt()
        setMeasuredDimension(w, (8 * d).toInt())
    }

    override fun onDraw(canvas: Canvas) {
        for (i in 0 until count) {
            paint.color = if (i == selected) 0xFF111111.toInt() else 0xFF8C8C8C.toInt()
            canvas.drawCircle((i * 16 + 4) * d, 4 * d, 4 * d, paint)
        }
    }
}
