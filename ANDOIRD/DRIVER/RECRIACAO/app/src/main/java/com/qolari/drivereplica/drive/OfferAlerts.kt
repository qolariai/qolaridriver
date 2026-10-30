package com.qolari.drivereplica.drive

import android.content.Context
import android.media.AudioManager
import android.media.ToneGenerator
import android.os.Build
import android.os.VibrationEffect
import android.os.Vibrator
import android.os.VibratorManager
import android.view.View
import androidx.core.content.getSystemService
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

/**
 * Atenção ao pedido (vídeo 2026-10-29, minuto 0:10): a Uber vibra, toca e pisca o ecrã enquanto o pedido
 * está aberto. As opções vivem em Definições > Acessibilidade (vibração e iluminação do ecrã) e em
 * Definições > Sons e voz (volume). O alerta pára quando o pedido sai do ecrã.
 */
class OfferAlerts(private val context: Context) {

    private var loop: Job? = null
    private var flashView: View? = null
    private var tone: ToneGenerator? = null

    /**
     * Arranca o alerta: vibração em pulsos, tom curto e um flash branco por cima do mapa.
     * [vibrate] / [flash] seguem as preferências; [volume] 0..1.
     */
    fun start(scope: CoroutineScope, flashOverlay: View, vibrate: Boolean, flash: Boolean, volume: Float) {
        stop()
        flashView = flashOverlay
        flashOverlay.isClickable = false
        flashOverlay.isFocusable = false
        if (vibrate) vibratePulse()
        playTone(volume)
        loop = scope.launch {
            var on = false
            while (true) {
                delay(900)
                on = !on
                if (vibrate) vibratePulse()
                playTone(volume)
                if (!flash) continue
                flashOverlay.animate().cancel()
                flashOverlay.animate().alpha(if (on) 0.35f else 0f).setDuration(420).start()
            }
        }
    }

    fun stop() {
        loop?.cancel()
        loop = null
        tone?.release()
        tone = null
        flashView?.animate()?.cancel()
        flashView?.alpha = 0f
        flashView = null
    }

    private fun vibratePulse() {
        val vibrator = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            context.getSystemService<VibratorManager>()?.defaultVibrator
        } else {
            @Suppress("DEPRECATION")
            context.getSystemService<Vibrator>()
        } ?: return
        if (!vibrator.hasVibrator()) return
        val pattern = longArrayOf(0, 180, 120, 180)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            vibrator.vibrate(VibrationEffect.createWaveform(pattern, -1))
        } else {
            @Suppress("DEPRECATION")
            vibrator.vibrate(pattern, -1)
        }
    }

    /** Tom de "novo pedido" sintetizado (não há ficheiro de som na app). */
    private fun playTone(volume: Float) {
        tone?.release()
        tone = runCatching {
            ToneGenerator(AudioManager.STREAM_NOTIFICATION, (volume.coerceIn(0f, 1f) * 100).toInt())
        }.getOrNull() ?: return
        tone?.startTone(ToneGenerator.TONE_PROP_BEEP2, 220)
    }
}
