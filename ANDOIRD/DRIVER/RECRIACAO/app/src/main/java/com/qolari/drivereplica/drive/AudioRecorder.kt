package com.qolari.drivereplica.drive

import android.content.Context
import android.media.MediaRecorder
import android.os.Build
import java.io.File

/** Gravacao de audio da viagem (AAC em MPEG-4), guardada na cache ate ser enviada. */
class AudioRecorder {
    private var recorder: MediaRecorder? = null
    private var file: File? = null

    fun start(context: Context): Boolean {
        val target = File(context.cacheDir, "trip-${System.currentTimeMillis()}.m4a")
        val r = if (Build.VERSION.SDK_INT >= 31) {
            MediaRecorder(context)
        } else {
            @Suppress("DEPRECATION")
            MediaRecorder()
        }
        return try {
            r.setAudioSource(MediaRecorder.AudioSource.MIC)
            r.setOutputFormat(MediaRecorder.OutputFormat.MPEG_4)
            r.setAudioEncoder(MediaRecorder.AudioEncoder.AAC)
            r.setAudioEncodingBitRate(64_000)
            r.setAudioSamplingRate(44_100)
            r.setMaxDuration(10 * 60 * 1000)
            r.setOutputFile(target.absolutePath)
            r.prepare()
            r.start()
            recorder = r
            file = target
            true
        } catch (_: Exception) {
            runCatching { r.release() }
            target.delete()
            false
        }
    }

    fun stop(): ByteArray? {
        val r = recorder ?: return null
        return try {
            r.stop()
            r.release()
            recorder = null
            file?.takeIf { it.isFile }?.readBytes()
        } catch (_: Exception) {
            cancel()
            null
        } finally {
            file = null
        }
    }

    fun cancel() {
        runCatching { recorder?.stop() }
        runCatching { recorder?.release() }
        recorder = null
        file?.delete()
        file = null
    }
}
