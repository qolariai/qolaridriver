package com.qolari.drivereplica.capture

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.pm.ServiceInfo
import android.graphics.Bitmap
import android.graphics.PixelFormat
import android.hardware.display.DisplayManager
import android.hardware.display.VirtualDisplay
import android.media.Image
import android.media.ImageReader
import android.media.projection.MediaProjection
import android.media.projection.MediaProjectionManager
import android.os.Build
import android.os.Handler
import android.os.HandlerThread
import android.os.IBinder
import android.os.Looper
import android.os.SystemClock
import androidx.core.app.NotificationCompat
import com.qolari.drivereplica.R
import com.qolari.drivereplica.data.AppGraph
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import java.io.ByteArrayOutputStream
import java.util.concurrent.atomic.AtomicBoolean
import kotlin.math.min

/** Partilha do ecrã completo do dispositivo com o apoio (MediaProjection + foreground service). */
class ScreenShareService : Service() {

    companion object {
        private const val CHANNEL = "qolari_screen_share"
        private const val NOTIFICATION_ID = 7401
        private const val ACTION_START = "com.qolari.drivereplica.SCREEN_SHARE_START"
        private const val ACTION_STOP = "com.qolari.drivereplica.SCREEN_SHARE_STOP"
        private const val EXTRA_RESULT_CODE = "result_code"
        private const val EXTRA_DATA = "data"
        private const val EXTRA_THREAD = "thread"
        private const val EXTRA_SHARE = "share"

        fun start(context: Context, resultCode: Int, data: Intent, thread: String, share: String) {
            val i = Intent(context, ScreenShareService::class.java)
                .setAction(ACTION_START)
                .putExtra(EXTRA_RESULT_CODE, resultCode)
                .putExtra(EXTRA_DATA, data)
                .putExtra(EXTRA_THREAD, thread)
                .putExtra(EXTRA_SHARE, share)
            if (Build.VERSION.SDK_INT >= 26) context.startForegroundService(i) else context.startService(i)
        }

        fun stop(context: Context) {
            context.startService(Intent(context, ScreenShareService::class.java).setAction(ACTION_STOP))
        }
    }

    private var projection: MediaProjection? = null
    private var virtualDisplay: VirtualDisplay? = null
    private var reader: ImageReader? = null
    private var thread: HandlerThread? = null
    private var shareUuid: String? = null
    private var supportThread: String? = null
    private val uploading = AtomicBoolean(false)
    private var lastSent = 0L

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onCreate() {
        super.onCreate()
        val nm = getSystemService(NotificationManager::class.java)
        if (Build.VERSION.SDK_INT >= 26) {
            nm.createNotificationChannel(NotificationChannel(CHANNEL, "Partilha de ecrã", NotificationManager.IMPORTANCE_LOW))
        }
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_START -> startCapture(intent)
            ACTION_STOP -> stopCapture()
        }
        return START_NOT_STICKY
    }

    private fun notification(): Notification {
        val stop = PendingIntent.getService(
            this, 0,
            Intent(this, ScreenShareService::class.java).setAction(ACTION_STOP),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )
        return NotificationCompat.Builder(this, CHANNEL)
            .setSmallIcon(R.drawable.ic_shield)
            .setContentTitle("A partilhar o ecrã")
            .setContentText("O apoio está a ver o ecrã deste telemóvel.")
            .setOngoing(true)
            .addAction(0, "Parar", stop)
            .build()
    }

    private fun startCapture(intent: Intent) {
        val notification = notification()
        if (Build.VERSION.SDK_INT >= 29) {
            startForeground(NOTIFICATION_ID, notification, ServiceInfo.FOREGROUND_SERVICE_TYPE_MEDIA_PROJECTION)
        } else {
            startForeground(NOTIFICATION_ID, notification)
        }
        supportThread = intent.getStringExtra(EXTRA_THREAD)
        shareUuid = intent.getStringExtra(EXTRA_SHARE)
        val data = intent.getParcelableExtra<Intent>(EXTRA_DATA)
        val code = intent.getIntExtra(EXTRA_RESULT_CODE, 0)
        if (data == null || supportThread == null || shareUuid == null) {
            stopCapture()
            return
        }
        val manager = getSystemService(MediaProjectionManager::class.java)
        val mp = runCatching { manager.getMediaProjection(code, data) }.getOrNull()
        if (mp == null) {
            stopCapture()
            return
        }
        projection = mp
        mp.registerCallback(object : MediaProjection.Callback() {
            override fun onStop() = stopCapture()
        }, Handler(Looper.getMainLooper()))

        thread = HandlerThread("qolari-screen-share").also { it.start() }
        val handler = Handler(thread!!.looper)
        val metrics = resources.displayMetrics
        val width = metrics.widthPixels
        val height = metrics.heightPixels
        reader = ImageReader.newInstance(width, height, PixelFormat.RGBA_8888, 2)
        reader!!.setOnImageAvailableListener({ r ->
            val image = r.acquireLatestImage() ?: return@setOnImageAvailableListener
            try {
                val now = SystemClock.elapsedRealtime()
                if (now - lastSent < 800 || !uploading.compareAndSet(false, true)) return@setOnImageAvailableListener
                lastSent = now
                val bmp = imageToBitmap(image, width, height)
                val scaled = scale(bmp)
                val bytes = ByteArrayOutputStream().also { scaled.compress(Bitmap.CompressFormat.JPEG, 55, it) }.toByteArray()
                val b64 = android.util.Base64.encodeToString(bytes, android.util.Base64.NO_WRAP)
                val t = supportThread
                val s = shareUuid
                if (t != null && s != null) {
                    CoroutineScope(Dispatchers.IO).launch {
                        AppGraph.repository.sendScreenFrame(t, s, b64)
                        uploading.set(false)
                    }
                } else {
                    uploading.set(false)
                }
            } catch (_: Exception) {
                uploading.set(false)
            } finally {
                image.close()
            }
        }, handler)
        virtualDisplay = mp.createVirtualDisplay(
            "qolari-screen", width, height, metrics.densityDpi,
            DisplayManager.VIRTUAL_DISPLAY_FLAG_AUTO_MIRROR, reader!!.surface, null, handler,
        )
    }

    private fun imageToBitmap(image: Image, width: Int, height: Int): Bitmap {
        val plane = image.planes[0]
        val rowPadding = plane.rowStride - plane.pixelStride * width
        val bmp = Bitmap.createBitmap(width + rowPadding / plane.pixelStride, height, Bitmap.Config.ARGB_8888)
        bmp.copyPixelsFromBuffer(plane.buffer)
        return Bitmap.createBitmap(bmp, 0, 0, width, height)
    }

    private fun scale(source: Bitmap): Bitmap {
        val maxWidth = 720f
        if (source.width <= maxWidth) return source
        val ratio = min(1f, maxWidth / source.width)
        return Bitmap.createScaledBitmap(source, (source.width * ratio).toInt(), (source.height * ratio).toInt(), true)
    }

    private fun stopCapture() {
        runCatching { virtualDisplay?.release() }
        virtualDisplay = null
        runCatching { reader?.close() }
        reader = null
        runCatching { projection?.stop() }
        projection = null
        thread?.quitSafely()
        thread = null
        uploading.set(false)
        stopForeground(STOP_FOREGROUND_REMOVE)
        stopSelf()
    }

    override fun onDestroy() {
        stopCapture()
        super.onDestroy()
    }
}
