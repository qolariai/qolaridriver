package com.qolari.drivereplica.drive

import android.content.Context
import android.graphics.Canvas
import android.graphics.Paint
import android.graphics.RectF
import android.util.AttributeSet
import android.view.MotionEvent
import android.view.View
import kotlin.math.max
import kotlin.math.min

/**
 * "Deslize para confirmar": o botão redondo arrasta-se até ao fim da pista; largar antes do fim volta ao início.
 * Usado nas ações da viagem (chegar, recolher, terminar), em que um toque sem querer teria custos para o passageiro.
 */
class SlideToConfirmView @JvmOverloads constructor(context: Context, attrs: AttributeSet? = null) : View(context, attrs) {

    var label: String = ""
        set(value) { field = value; invalidate() }

    var onConfirmed: (() -> Unit)? = null

    private val d = resources.displayMetrics.density
    private val track = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = 0xFF111111.toInt() }
    private val thumb = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = 0xFFFFFFFF.toInt() }
    private val arrow = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = 0xFF111111.toInt(); style = Paint.Style.STROKE; strokeWidth = 2.5f * d; strokeCap = Paint.Cap.ROUND; strokeJoin = Paint.Join.ROUND
    }
    private val text = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = 0xFFFFFFFF.toInt(); textAlign = Paint.Align.CENTER; textSize = 16f * d }

    private var offset = 0f
    private var dragging = false
    private var confirmed = false

    private val margin get() = 6f * d
    private val thumbR get() = height / 2f - margin
    private val maxOffset get() = max(0f, width - 2 * margin - 2 * thumbR)

    override fun onMeasure(widthMeasureSpec: Int, heightMeasureSpec: Int) {
        setMeasuredDimension(MeasureSpec.getSize(widthMeasureSpec), (60 * d).toInt())
    }

    override fun onDraw(canvas: Canvas) {
        val h = height.toFloat()
        canvas.drawRoundRect(RectF(0f, 0f, width.toFloat(), h), h / 2, h / 2, track)
        text.alpha = (255 * (1f - progress() * 0.8f)).toInt()
        canvas.drawText(label, width / 2f + thumbR, h / 2f + text.textSize / 3f, text)
        val cx = margin + thumbR + offset
        val cy = h / 2f
        canvas.drawCircle(cx, cy, thumbR, thumb)
        canvas.drawLine(cx - 7 * d, cy, cx + 7 * d, cy, arrow)
        canvas.drawLine(cx + 1 * d, cy - 6 * d, cx + 7 * d, cy, arrow)
        canvas.drawLine(cx + 1 * d, cy + 6 * d, cx + 7 * d, cy, arrow)
    }

    private fun progress() = if (maxOffset == 0f) 0f else offset / maxOffset

    override fun onTouchEvent(event: MotionEvent): Boolean {
        if (!isEnabled || confirmed) return false
        when (event.actionMasked) {
            MotionEvent.ACTION_DOWN -> {
                val cx = margin + thumbR + offset
                dragging = event.x in (cx - thumbR - 8 * d)..(cx + thumbR + 8 * d)
                parent?.requestDisallowInterceptTouchEvent(dragging)
                return dragging
            }
            MotionEvent.ACTION_MOVE -> if (dragging) {
                offset = min(max(0f, event.x - margin - thumbR), maxOffset)
                invalidate()
            }
            MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> if (dragging) {
                dragging = false
                if (event.actionMasked == MotionEvent.ACTION_UP && progress() >= 0.85f) {
                    confirmed = true
                    offset = maxOffset
                    invalidate()
                    onConfirmed?.invoke()
                } else {
                    offset = 0f
                    invalidate()
                }
            }
        }
        return true
    }

    /** Volta ao início (por exemplo, quando a ação falhou e o utilizador pode tentar de novo). */
    fun reset() {
        confirmed = false
        offset = 0f
        invalidate()
    }
}
