package com.qolari.drivereplica.drive

import android.content.Context
import android.graphics.Canvas
import android.graphics.Paint
import android.graphics.RectF
import android.util.AttributeSet
import android.view.View
import com.qolari.drivereplica.R

/**
 * Guia vertical do cartão da proposta (vídeo 2026-10-29): círculo vazado na linha da recolha e
 * quadrado vazado na linha do destino, ligados por uma linha de 2dp. Substitui os pinos de mapa
 * que a original não mostra dentro do cartão.
 *
 * As posições são medidas em dp a partir do topo da vista; o fragment ajusta-as depois do layout
 * (as moradas podem ocupar uma ou duas linhas).
 */
class OfferRailView @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null,
) : View(context, attrs) {

    private val density = resources.displayMetrics.density

    private val line = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = context.getColor(R.color.qd_ink)
        style = Paint.Style.STROKE
        strokeWidth = 2 * density
        strokeCap = Paint.Cap.ROUND
    }
    private val fill = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = context.getColor(R.color.qd_background)
        style = Paint.Style.FILL
    }

    /** Centro do círculo de recolha, em dp a partir do topo. */
    var pickupCenterDp: Float = 12f
        set(value) { field = value; invalidate() }

    /** Centro do quadrado de destino, em dp a partir do topo. */
    var dropoffCenterDp: Float = 96f
        set(value) { field = value; invalidate() }

    override fun onDraw(canvas: Canvas) {
        val cx = width / 2f
        val top = pickupCenterDp * density
        val bottom = (dropoffCenterDp * density).coerceAtLeast(top + 20 * density)
        val ringR = 4.5f * density
        val half = 4.5f * density

        // Haste entre o círculo e o quadrado.
        canvas.drawLine(cx, top + ringR, cx, bottom - half, line)

        // Recolha: círculo de contorno com miolo branco.
        canvas.drawCircle(cx, top, ringR, fill)
        canvas.drawCircle(cx, top, ringR, line)

        // Destino: quadrado de contorno com miolo branco.
        val box = RectF(cx - half, bottom - half, cx + half, bottom + half)
        canvas.drawRect(box, fill)
        canvas.drawRect(box, line)
    }
}
