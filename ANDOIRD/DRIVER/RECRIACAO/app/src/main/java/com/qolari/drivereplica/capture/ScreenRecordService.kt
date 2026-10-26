package com.qolari.drivereplica.capture

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.pm.ServiceInfo
import android.hardware.display.DisplayManager
import android.hardware.display.VirtualDisplay
import android.media.MediaRecorder
import android.media.projection.MediaProjection
import android.media.projection.MediaProjectionManager
import android.os.Build
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import androidx.core.app.NotificationCompat
import com.qolari.drivereplica.R
import com.qolari.drivereplica.data.AppGraph
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import java.io.File
import java.util.concurrent.atomic.AtomicBoolean

/** Gravação de vídeo do ecrã completo, associada a uma viagem. */
class ScreenRecordService : Service() {

    companion object {
        private const val CHANNEL = "qolari_screen_record"
        private const val NOTIFICATION_ID = 7402
        private const val ACTION_START = "com.qolari.drivereplica.SCREEN_RECORD_START"
        private const val ACTION_STOP = "com.qolari.drivereplica.SCREEN_RECORD_STOP"
        private const val EXTRA_RESULT_CODE = "result_code"
        private const val EXTRA_DATA = "data"
        private const val EXTRA_RECORDING = "recording"

        fun start(context: Context, resultCode: Int, data: Intent, recording: String) {
            val i = Intent(context, ScreenRecordService::class.java)
                .setAction(ACTION_START)
                .putExtra(EXTRA_RESULT_CODE, resultCode)
                .putExtra(EXTRA_DATA, data)
                .putExtra(EXTRA_RECORDING, recording)
            if (Build.VERSION.SDK_INT >= 26) context.startForegroundService(i) else context.startService(i)
        }

        fun stop(context: Context) {
            context.startService(Intent(context, ScreenRecordService::class.java).setAction(ACTION_STOP))
        }
    }

    private var projection: MediaProjection? = null
    private var virtualDisplay: VirtualDisplay? = null
    private var recorder: MediaRecorder? = null
    private var file: File? = null
    private var recordingUuid: String? = null
    private val stopping = AtomicBoolean(false)

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onCreate() {
        super.onCreate()
        val nm = getSystemService(NotificationManager::class.java)
        if (Build.VERSION.SDK_INT >= 26) {
            nm.createNotificationChannel(NotificationChannel(CHANNEL, "Gravação de vídeo", NotificationManager.IMPORTANCE_LOW))
        }
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_START -> startCapture(intent)
            ACTION_STOP -> stopCapture(true)
        }
        return START_NOT_STICKY
    }

    private fun notification(): Notification {
        val stop = PendingIntent.getService(
            this, 0,
            Intent(this, ScreenRecordService::class.java).setAction(ACTION_STOP),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )
        return NotificationCompat.Builder(this, CHANNEL)
            .setSmallIcon(R.drawable.ic_shield)
            .setContentTitle("A gravar vídeo")
            .setContentText("A gravação do ecrã está ativa.")
            .setOngoing(true)
            .addAction(0, "Parar", stop)
            .build()
    }

    private fun startCapture(intent: Intent) {
        val n = notification()
        if (Build.VERSION.SDK_INT >= 29) {
            startForeground(NOTIFICATION_ID, n, ServiceInfo.FOREGROUND_SERVICE_TYPE_MEDIA_PROJECTION)
        } else {
            startForeground(NOTIFICATION_ID, n)
        }
        recordingUuid = intent.getStringExtra(EXTRA_RECORDING)
        val data = intent.getParcelableExtra<Intent>(EXTRA_DATA)
        val code = intent.getIntExtra(EXTRA_RESULT_CODE, 0)
        if (data == null || recordingUuid == null) {
            stopCapture(false)
            return
        }
        val manager = getSystemService(MediaProjectionManager::class.java)
        val mp = runCatching { manager.getMediaProjection(code, data) }.getOrNull()
        if (mp == null) {
            stopCapture(false)
            return
        }
        projection = mp
        mp.registerCallback(object : MediaProjection.Callback() {
            override fun onStop() = stopCapture(true)
        }, Handler(Looper.getMainLooper()))

        val metrics = resources.displayMetrics
        val width = (metrics.widthPixels / 2).coerceAtLeast(2) / 2 * 2
        val height = (metrics.heightPixels / 2).coerceAtLeast(2) / 2 * 2
        val target = File(cacheDir, "video-${System.currentTimeMillis()}.mp4")
        val rec = if (Build.VERSION.SDK_INT >= 31) MediaRecorder(this) else {
            @Suppress("DEPRECATION")
            MediaRecorder()
        }
        try {
            rec.setVideoSource(MediaRecorder.VideoSource.SURFACE)
            rec.setOutputFormat(MediaRecorder.OutputFormat.MPEG_4)
            rec.setVideoEncoder(MediaRecorder.VideoEncoder.H264)
            rec.setVideoSize(width, height)
            rec.setVideoEncodingBitRate(1_500_000)
            rec.setVideoFrameRate(20)
            rec.setMaxDuration(60_000)
            rec.setOutputFile(target.absolutePath)
            rec.setOnInfoListener { _, what, _ ->
                if (what == MediaRecorder.MEDIA_RECORDER_INFO_MAX_DURATION_REACHED) stopCapture(true)
            }
            rec.prepare()
            virtualDisplay = mp.createVirtualDisplay(
                "qolari-record", width, height, metrics.densityDpi,
                DisplayManager.VIRTUAL_DISPLAY_FLAG_AUTO_MIRROR, rec.surface, null, null,
            )
            rec.start()
            recorder = rec
            file = target
        } catch (_: Exception) {
            runCatching { rec.release() }
            target.delete()
            stopCapture(false)
        }
    }

    private fun stopCapture(upload: Boolean) {
        if (!stopping.compareAndSet(false, true)) return
        val rec = recorder
        recorder = null
        runCatching { rec?.stop() }
        runCatching { rec?.release() }
        runCatching { virtualDisplay?.release() }
        virtualDisplay = null
        runCatching { projection?.stop() }
        projection = null
        val target = file
        file = null
        val uuid = recordingUuid
        recordingUuid = null
        stopForeground(STOP_FOREGROUND_REMOVE)
        if (upload && uuid != null && target != null && target.isFile && target.length() > 0) {
            val bytes = runCatching { target.readBytes() }.getOrNull()
            if (bytes != null) {
                CoroutineScope(Dispatchers.IO).launch {
                    val b64 = android.util.Base64.encodeToString(bytes, android.util.Base64.NO_WRAP)
                    AppGraph.repository.stopRecording(uuid, b64)
                }
            }
        }
        target?.delete()
        stopSelf()
    }

    override fun onDestroy() {
        if (recorder != null) stopCapture(true)
        super.onDestroy()
    }
}
