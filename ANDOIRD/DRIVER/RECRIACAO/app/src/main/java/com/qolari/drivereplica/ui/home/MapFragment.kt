package com.qolari.drivereplica.ui.home

import android.Manifest
import android.app.Activity
import android.content.Intent
import android.media.projection.MediaProjectionManager
import android.net.Uri
import android.os.Bundle
import android.os.SystemClock
import android.view.View
import androidx.activity.result.contract.ActivityResultContracts
import androidx.core.view.isVisible
import androidx.fragment.app.Fragment
import androidx.fragment.app.activityViewModels
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import androidx.navigation.fragment.findNavController
import com.qolari.drivereplica.R
import com.qolari.drivereplica.capture.ScreenRecordService
import com.qolari.drivereplica.data.AppGraph
import com.google.android.material.snackbar.Snackbar
import com.qolari.drivereplica.databinding.FragmentMapBinding
import com.qolari.drivereplica.drive.ActiveTrip
import com.qolari.drivereplica.drive.AudioRecorder
import com.qolari.drivereplica.drive.DriveStage
import com.qolari.drivereplica.drive.DriveUiState
import com.qolari.drivereplica.drive.DriveViewModel
import com.qolari.drivereplica.drive.OfferCard
import com.qolari.drivereplica.drive.PinSheet
import com.qolari.drivereplica.drive.RatingSheet
import com.qolari.drivereplica.drive.TripPhase
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.launch

/**
 * Modo mapa da Página inicial (captura 110) e, com o motorista online, o ecrã da proposta e da viagem
 * (capturas 100_online_*): "Radar de viagens", cartão da proposta, recolher, PIN, deixar e avaliação.
 * O ícone da casa volta ao painel (ux_behavior.md §1.2). Partilha o estado com o painel.
 */
class MapFragment : Fragment(R.layout.fragment_map) {

    private val viewModel: HomeViewModel by activityViewModels { HomeViewModel.Factory }
    private val drive: DriveViewModel by activityViewModels { DriveViewModel.Factory }
    private var binding: FragmentMapBinding? = null

    private val locationPermission = registerForActivityResult(ActivityResultContracts.RequestPermission()) {
        viewModel.toggleOnline()
    }

    private val audioRecorder = AudioRecorder()
    private var recordingUuid: String? = null
    private var pendingTripUuid: String? = null
    private val recordPermission = registerForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
        if (granted) pendingTripUuid?.let { startRecording(it) }
        pendingTripUuid = null
    }

    private var videoRecordingUuid: String? = null
    private var pendingVideoRecording: String? = null
    private val captureVideo = registerForActivityResult(ActivityResultContracts.StartActivityForResult()) { result ->
        val uuid = pendingVideoRecording
        pendingVideoRecording = null
        if (result.resultCode == Activity.RESULT_OK && result.data != null && uuid != null) {
            ScreenRecordService.start(requireContext(), result.resultCode, result.data!!, uuid)
            videoRecordingUuid = uuid
            binding?.tripCard?.tripVideo?.setText(R.string.drive_video_stop)
        } else if (uuid != null) {
            kotlinx.coroutines.CoroutineScope(kotlinx.coroutines.Dispatchers.IO).launch {
                AppGraph.repository.stopRecording(uuid, null)
            }
            Snackbar.make(requireView(), R.string.drive_video_error, Snackbar.LENGTH_SHORT).show()
        }
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        val b = FragmentMapBinding.bind(view)
        binding = b
        b.mapHome.setOnClickListener { findNavController().popBackStack() }
        b.mapSearch.setOnClickListener {
            com.qolari.drivereplica.ui.map.PlaceSearchSheet.show(childFragmentManager) { name, lat, lng ->
                b.mapFull.focus(lat, lng, name)
            }
        }
        b.mapShield.setOnClickListener { com.qolari.drivereplica.ui.manage.SafetySheet.show(this) }
        b.mapPrefs.setOnClickListener {
            findNavController().navigate(R.id.menuTab)
            findNavController().navigate(
                R.id.settingsFragment,
                androidx.core.os.bundleOf(
                    com.qolari.drivereplica.ui.settings.SettingsFragment.ARG_BACK_TO to R.id.mapFragment,
                ),
            )
        }
        b.mapBolt.setOnClickListener { findNavController().navigate(R.id.discoverFragment) }
        b.mapReport.setOnClickListener { com.qolari.drivereplica.ui.map.MapReportSheet.show(childFragmentManager) }
        b.mapTrends.setOnClickListener { findNavController().navigate(R.id.earningsFragment) }
        b.mapLocate.setOnClickListener { b.mapFull.recenter() }
        b.mapStart.setOnClickListener {
            if (AppGraph.location.hasPermission) viewModel.toggleOnline()
            else locationPermission.launch(Manifest.permission.ACCESS_FINE_LOCATION)
        }
        b.offerCard.offerAccept.setOnClickListener { drive.accept() }
        b.offerCard.offerClose.setOnClickListener { drive.decline() }
        b.tripCard.tripPinButton.setOnClickListener { PinSheet().show(childFragmentManager, "pin") }

        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                launch {
                    // Tempo de espera na recolha: relógio que avança por segundos (WaitTimeTaskData.startTimeSec).
                    while (true) {
                        val t = drive.state.value.trip
                        val start = t?.waitStartSec
                        if (t != null && t.phase == TripPhase.AT_PICKUP && start != null) {
                            val secs = (System.currentTimeMillis() / 1000 - start).coerceAtLeast(0)
                            b.tripCard.tripWait.text = getString(R.string.drive_wait, "%d:%02d".format(secs / 60, secs % 60))
                        }
                        delay(1000)
                    }
                }
                launch {
                    combine(viewModel.state, AppGraph.network.connected, drive.state) { s, c, d -> Triple(s, c, d) }.collect { (s, connected, d) ->
                        renderStatus(b, s.online, connected, d.stage)
                        render(b, d)
                    }
                }
                launch {
                    viewModel.events.collect {
                        ErrorSheet.show(childFragmentManager, viewLifecycleOwner) { viewModel.refresh() }
                    }
                }
                launch { drive.events.collect { ErrorSheet.show(childFragmentManager, viewLifecycleOwner) { drive.setOnline(true) } } }
            }
        }
    }

    private fun renderStatus(b: FragmentMapBinding, online: Boolean, connected: Boolean, stage: DriveStage) {
        val idle = stage == DriveStage.IDLE || stage == DriveStage.RATING
        b.mapStart.isVisible = !online
        b.mapStatus.setText(if (online) R.string.home_online else R.string.home_offline)
        b.mapStatusHint.setText(if (online) R.string.map_online_hint else R.string.map_offline_no_network)
        b.mapStatusHint.isVisible = !connected || online
        b.mapStatusHint.setTextColor(requireContext().getColor(if (online) R.color.qd_core_green600 else R.color.qd_core_red600))
        b.statusPanel.isVisible = idle
        // Com proposta ou viagem o cartão ocupa o fundo: os atalhos do mapa saem para não ficarem por baixo dele.
        b.mapShortcuts.isVisible = idle
        b.mapShield.isVisible = idle
        b.radarPill.isVisible = online && (idle || stage == DriveStage.OFFER)
    }

    private fun render(b: FragmentMapBinding, d: DriveUiState) {
        val offer = d.offer
        val trip = d.trip
        val tripVisible = trip != null && d.stage in listOf(DriveStage.TO_PICKUP, DriveStage.AT_PICKUP, DriveStage.ON_TRIP)
        val tripPoint = trip?.let { t ->
            if (t.latitude != null && t.longitude != null) t.latitude to t.longitude else null
        }
        b.mapFull.route = when {
            d.stage == DriveStage.OFFER -> d.route
            tripVisible && d.route.isNotEmpty() -> d.route
            tripVisible && tripPoint != null -> listOf(tripPoint)
            else -> emptyList()
        }
        b.mapFull.userLocation =
            if (AppGraph.location.hasPermission) AppGraph.location.lastKnown() else null
        b.mapFull.setBottomPaddingDp(if (d.stage != DriveStage.IDLE && d.stage != DriveStage.RATING) 280 else 0)

        b.offerCard.root.isVisible = d.stage == DriveStage.OFFER && offer != null
        b.radarCount.text = if (offer != null) "1" else "0"
        if (offer != null && d.stage == DriveStage.OFFER) bindOffer(b, offer)

        b.tripCard.root.isVisible = tripVisible
        if (trip != null && tripVisible) bindTrip(b, trip, d)

        val sheet = childFragmentManager.findFragmentByTag("rating")
        when {
            d.stage == DriveStage.RATING && sheet == null -> RatingSheet().show(childFragmentManager, "rating")
            // Fecha a folha se o estado já saiu de RATING (ex.: avaliação enviada): sem isto, uma emissão
            // atrasada do estado anterior volta a abrir a folha e o motorista fica preso nela.
            d.stage != DriveStage.RATING && sheet != null -> {
                (sheet as? androidx.fragment.app.DialogFragment)?.dismissAllowingStateLoss()
            }
        }
    }

    private var timerKey: String? = null

    private fun bindOffer(b: FragmentMapBinding, o: OfferCard) {
        val c = b.offerCard
        c.offerProduct.text = o.product
        c.offerPrice.text = o.price
        c.offerPickupLine.text = o.pickupLine
        c.offerPickupAddress.text = o.pickupAddress
        c.offerTripLine.text = o.tripLine
        c.offerTripLine.isVisible = o.tripLine != null
        c.offerDropoffAddress.text = o.dropoffAddress
        c.offerDropoffAddress.isVisible = o.dropoffAddress != null
        if (timerKey == o.uuid) return
        timerKey = o.uuid
        // Contagem decrescente (convenção própria [inf]: a original não mostra o tempo): a barra encolhe e, a zero, expira.
        val total = (o.acceptWindowS * 1000L).coerceAtLeast(1000L)
        val start = SystemClock.elapsedRealtime()
        viewLifecycleOwner.lifecycleScope.launch {
            while (timerKey == o.uuid) {
                val left = total - (SystemClock.elapsedRealtime() - start)
                c.offerTimer.scaleX = (left.toFloat() / total).coerceIn(0f, 1f)
                c.offerTimer.pivotX = 0f
                if (left <= 0) {
                    timerKey = null
                    drive.expire()
                    return@launch
                }
                delay(100)
            }
        }
    }

    private fun bindTrip(b: FragmentMapBinding, t: ActiveTrip, d: DriveUiState) {
        val c = b.tripCard
        val pinNeeded = t.phase == TripPhase.AT_PICKUP && t.pin != null && !d.pinVerified
        c.tripTitle.text = getString(if (t.phase == TripPhase.ON_TRIP) R.string.drive_dropoff_title else R.string.drive_pickup_title, t.riderName)
        c.tripRider.text = t.riderRating?.let { getString(R.string.drive_rider_rating, "%.2f".format(java.util.Locale("pt", "PT"), it)) }.orEmpty()
        c.tripAddress.text = t.address
        c.tripFare.text = t.fare?.let { getString(R.string.drive_fare, it) }.orEmpty()
        c.tripFare.isVisible = t.fare != null
        c.tripWait.isVisible = t.phase == TripPhase.AT_PICKUP && t.waitStartSec != null
        t.waitStartSec?.let { start ->
            val secs = (System.currentTimeMillis() / 1000 - start).coerceAtLeast(0)
            c.tripWait.text = getString(R.string.drive_wait, "%d:%02d".format(secs / 60, secs % 60))
        }
        c.tripPinButton.isVisible = pinNeeded
        c.tripNavigate.setOnClickListener {
            val lat = t.latitude
            val lng = t.longitude
            if (lat == null || lng == null) return@setOnClickListener
            com.google.android.material.dialog.MaterialAlertDialogBuilder(requireContext())
                .setTitle(R.string.drive_navigate)
                .setItems(arrayOf(getString(R.string.drive_google_maps), getString(R.string.drive_waze))) { _, which ->
                    val uri = if (which == 0) {
                        Uri.parse("google.navigation:q=$lat,$lng")
                    } else {
                        Uri.parse("waze://?ll=$lat,$lng&navigate=yes")
                    }
                    startActivity(Intent(Intent.ACTION_VIEW, uri))
                }
                .show()
        }
        c.tripCompleteStop.isVisible = t.nextStopIndex != null
        c.tripCompleteStop.text = getString(R.string.drive_stop_button, (t.nextStopIndex ?: 0) + 1, t.stops.size)
        c.tripCompleteStop.setOnClickListener { drive.completeStop() }
        c.tripRecord.isVisible = true
        c.tripRecord.setText(if (recordingUuid != null) R.string.drive_record_stop else R.string.drive_record_start)
        c.tripRecord.setOnClickListener { toggleRecording(t.uuid) }
        c.tripVideo.isVisible = true
        c.tripVideo.setText(if (videoRecordingUuid != null) R.string.drive_video_stop else R.string.drive_video_start)
        c.tripVideo.setOnClickListener { toggleVideo(t.uuid) }
        c.tripSlide.isVisible = !pinNeeded
        c.tripSlide.label = getString(
            when (t.phase) {
                TripPhase.TO_PICKUP -> R.string.drive_slide_arrived
                TripPhase.AT_PICKUP -> R.string.drive_slide_pickup
                TripPhase.ON_TRIP -> R.string.drive_slide_end
            }
        )
        c.tripSlide.reset()
        c.tripSlide.onConfirmed = {
            when (t.phase) {
                TripPhase.TO_PICKUP -> drive.arrive()
                TripPhase.AT_PICKUP -> drive.startTrip()
                TripPhase.ON_TRIP -> drive.finishTrip()
            }
        }
    }

    private fun toggleVideo(tripUuid: String) {
        if (videoRecordingUuid != null) {
            ScreenRecordService.stop(requireContext())
            videoRecordingUuid = null
            binding?.tripCard?.tripVideo?.setText(R.string.drive_video_start)
            return
        }
        viewLifecycleOwner.lifecycleScope.launch {
            AppGraph.repository.startRecording(tripUuid, "video")
                .onSuccess { uuid ->
                    if (uuid == null) {
                        Snackbar.make(requireView(), R.string.drive_video_error, Snackbar.LENGTH_SHORT).show()
                        return@onSuccess
                    }
                    pendingVideoRecording = uuid
                    val manager = requireContext().getSystemService(MediaProjectionManager::class.java)
                    captureVideo.launch(manager.createScreenCaptureIntent())
                }
                .onFailure {
                    Snackbar.make(requireView(), R.string.drive_video_error, Snackbar.LENGTH_SHORT).show()
                }
        }
    }

    private fun toggleRecording(tripUuid: String) {
        if (recordingUuid != null) {
            stopRecording()
            return
        }
        val granted = androidx.core.content.ContextCompat.checkSelfPermission(
            requireContext(), Manifest.permission.RECORD_AUDIO,
        ) == android.content.pm.PackageManager.PERMISSION_GRANTED
        if (granted) {
            startRecording(tripUuid)
        } else {
            pendingTripUuid = tripUuid
            recordPermission.launch(Manifest.permission.RECORD_AUDIO)
        }
    }

    private fun startRecording(tripUuid: String) {
        viewLifecycleOwner.lifecycleScope.launch {
            val uuid = AppGraph.repository.startRecording(tripUuid).getOrNull()
            if (uuid == null) {
                Snackbar.make(requireView(), R.string.drive_record_error, Snackbar.LENGTH_SHORT).show()
                return@launch
            }
            if (!audioRecorder.start(requireContext())) {
                AppGraph.repository.stopRecording(uuid, null)
                Snackbar.make(requireView(), R.string.drive_record_error, Snackbar.LENGTH_SHORT).show()
                return@launch
            }
            recordingUuid = uuid
            binding?.tripCard?.tripRecord?.setText(R.string.drive_record_stop)
            Snackbar.make(requireView(), R.string.drive_record_on, Snackbar.LENGTH_LONG).show()
        }
    }

    private fun stopRecording() {
        val uuid = recordingUuid
        val bytes = audioRecorder.stop()
        recordingUuid = null
        binding?.tripCard?.tripRecord?.setText(R.string.drive_record_start)
        if (uuid != null) {
            viewLifecycleOwner.lifecycleScope.launch {
                val b64 = bytes?.let { android.util.Base64.encodeToString(it, android.util.Base64.NO_WRAP) }
                AppGraph.repository.stopRecording(uuid, b64)
                Snackbar.make(requireView(), R.string.drive_record_saved, Snackbar.LENGTH_LONG).show()
            }
        }
    }

    override fun onResume() {
        super.onResume()
        binding?.mapFull?.onResume()
    }

    override fun onPause() {
        binding?.mapFull?.onPause()
        super.onPause()
    }

    override fun onDestroyView() {
        audioRecorder.cancel()
        val uuid = recordingUuid
        recordingUuid = null
        if (uuid != null) {
            kotlinx.coroutines.CoroutineScope(kotlinx.coroutines.Dispatchers.IO).launch {
                AppGraph.repository.stopRecording(uuid, null)
            }
        }
        if (videoRecordingUuid != null) {
            ScreenRecordService.stop(requireContext())
            videoRecordingUuid = null
        }
        binding?.mapFull?.onDestroy()
        timerKey = null
        binding = null
        super.onDestroyView()
    }
}
