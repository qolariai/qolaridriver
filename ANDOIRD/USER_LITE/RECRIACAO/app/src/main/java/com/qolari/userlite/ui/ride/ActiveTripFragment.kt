package com.qolari.userlite.ui.ride

import android.content.res.ColorStateList
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.EditText
import androidx.core.content.ContextCompat
import androidx.core.view.isVisible
import androidx.fragment.app.Fragment
import androidx.fragment.app.activityViewModels
import androidx.fragment.app.viewModels
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import androidx.navigation.fragment.findNavController
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import com.google.android.material.snackbar.Snackbar
import com.qolari.userlite.R
import com.qolari.userlite.data.AppGraph
import com.qolari.userlite.databinding.FragmentActiveTripBinding
import com.qolari.userlite.net.Trip
import kotlinx.coroutines.launch
import java.text.DateFormat
import java.util.Date

/** Viagem em curso: procura, motorista a caminho, PIN, em viagem, fim e avaliação. */
class ActiveTripFragment : Fragment() {

    private var _binding: FragmentActiveTripBinding? = null
    private val binding get() = _binding!!
    private val viewModel: ActiveTripViewModel by viewModels()
    private val ride: RideViewModel by activityViewModels()
    private var stars = 5
    private var routeKey: String? = null

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentActiveTripBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        binding.closeButton.setOnClickListener { goHome() }
        binding.homeButton.setOnClickListener { goHome() }
        binding.tip1.setOnClickListener { tip(100) }
        binding.tip2.setOnClickListener { tip(200) }
        binding.tip5.setOnClickListener { tip(500) }
        binding.tip0.setOnClickListener { tip(0) }
        binding.rideOk.setOnClickListener { rideCheck("ok") }
        binding.rideHelp.setOnClickListener { rideCheck("help") }
        binding.receiptButton.setOnClickListener { showReceipt() }
        binding.disputeButton.setOnClickListener { showDispute() }
        binding.retryButton.setOnClickListener {
            ride.reset()
            findNavController().navigate(R.id.action_active_to_search)
        }
        binding.cancelButton.setOnClickListener { confirmCancel() }
        binding.error.setOnClickListener { viewModel.refresh() }
        binding.skipRating.setOnClickListener { goHome() }
        binding.sendRating.setOnClickListener {
            viewModel.state.value.trip?.let { viewModel.rate(it.uuid, stars) }
        }
        setStars(stars)

        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                viewModel.state.collect { state ->
                    binding.loading.isVisible = state.loading && state.trip == null
                    binding.error.isVisible = state.error != null
                    binding.error.text = state.error
                    if (state.rated) {
                        Snackbar.make(binding.root, R.string.trip_rate_thanks, Snackbar.LENGTH_SHORT).show()
                        goHome()
                    }
                    if (state.empty) {
                        goHome()
                    }
                    state.trip?.let { render(it, state.canceling) }
                    binding.cancelButton.isEnabled = !state.canceling
                    binding.cancelButton.text = if (state.canceling) {
                        getString(R.string.loading)
                    } else {
                        getString(R.string.trip_cancel)
                    }
                }
            }
        }
        viewModel.start()
    }

    override fun onStop() {
        markTerminalSeen()
        viewModel.stop()
        super.onStop()
    }

    override fun onStart() {
        super.onStart()
        viewModel.start()
    }

    private fun render(trip: Trip, canceling: Boolean) {
        val title: String
        val detail: String
        when (trip.state) {
            "requested" -> {
                val scheduled = trip.scheduledAt
                if (scheduled != null && scheduled > System.currentTimeMillis()) {
                    val whenLabel = DateFormat.getDateTimeInstance(DateFormat.SHORT, DateFormat.SHORT)
                        .format(Date(scheduled))
                    title = getString(R.string.trip_scheduled)
                    detail = getString(R.string.trip_scheduled_detail, whenLabel)
                } else {
                    title = getString(R.string.trip_searching)
                    detail = getString(R.string.trip_searching_detail)
                }
            }
            "accepted" -> {
                title = getString(R.string.trip_accepted)
                detail = trip.driverEtaMin?.let { getString(R.string.trip_driver_eta, it) }
                    ?: getString(R.string.trip_accepted)
            }
            "arrived" -> {
                title = getString(R.string.trip_arrived)
                detail = getString(R.string.trip_arrived_detail)
            }
            "in_progress" -> {
                title = getString(R.string.trip_in_progress)
                detail = trip.tripEtaMin?.let { getString(R.string.trip_in_progress_detail, it) }
                    ?: getString(R.string.trip_in_progress)
            }
            "completed" -> {
                title = getString(R.string.trip_completed)
                detail = getString(R.string.trip_completed_detail)
            }
            "cancelled" -> {
                title = getString(R.string.trip_cancelled)
                detail = trip.cancelReason ?: ""
            }
            "no_drivers" -> {
                title = getString(R.string.trip_no_drivers)
                detail = getString(R.string.trip_no_drivers_detail)
            }
            else -> {
                title = trip.state
                detail = ""
            }
        }
        binding.statusTitle.text = title
        binding.statusDetail.text = detail
        binding.statusDetail.isVisible = detail.isNotBlank()

        val driver = trip.driver
        binding.driverCard.isVisible = driver != null
        if (driver != null) {
            binding.avatar.text = driver.name.take(1).uppercase().ifBlank { "Q" }
            binding.driverName.text = driver.name
            val vehicle = driver.vehicle
            binding.driverDetail.text = listOfNotNull(
                vehicle?.label?.takeIf { it.isNotBlank() },
                vehicle?.plate?.takeIf { it.isNotBlank() },
            ).joinToString(" · ")
            binding.driverRating.text = String.format("★ %.1f", driver.rating)
        }

        val pin = trip.pin
        binding.pinCard.isVisible = trip.state == "arrived" && !pin.isNullOrBlank()
        binding.pinValue.text = pin.orEmpty()
        binding.routeCard.isVisible = true
        binding.pickupText.text = trip.pickup.address
        binding.dropoffText.text = trip.dropoff.address
        if (trip.stops.isNotEmpty()) {
            binding.tripStops.isVisible = true
            binding.tripStops.text = trip.stops.mapIndexed { i, s ->
                val mark = if (s.done) " ✓" else ""
                getString(R.string.trip_stop_line, i + 1, s.address) + mark
            }.joinToString("\n")
        } else {
            binding.tripStops.isVisible = false
        }
        binding.fareCard.isVisible = trip.state == "completed"
        binding.fareValue.text = trip.fare.label
        binding.tipCard.isVisible = trip.state == "completed" && trip.canTip
        binding.receiptRow.isVisible = trip.state == "completed"
        binding.rideCheckCard.isVisible = trip.state in setOf("accepted", "arrived", "in_progress")
        binding.ratingContainer.isVisible = trip.state == "completed" && trip.canRate
        binding.cancelButton.isVisible = trip.canCancel && !canceling
        binding.retryButton.isVisible = trip.state == "no_drivers"
        binding.homeButton.isVisible = trip.state in setOf("completed", "cancelled", "no_drivers")

        val pickupPoint = if (trip.pickup.lat != 0.0) trip.pickup.lat to trip.pickup.lng else null
        val dropoffPoint = if (trip.dropoff.lat != 0.0) trip.dropoff.lat to trip.dropoff.lng else null
        val driverPoint = driver?.let { d ->
            if (d.lat != null && d.lng != null) d.lat to d.lng else null
        }
        // "Motorista a caminho": rota do motorista até à recolha. Em viagem: recolha -> destino.
        val approaching = trip.state == "accepted" || trip.state == "arrived"
        val from = if (approaching && driverPoint != null) driverPoint else pickupPoint
        val to = if (approaching) pickupPoint else dropoffPoint
        val points = listOfNotNull(from, to)
        binding.map.route = points
        val key = "${trip.uuid}:${trip.state}:" +
            (if (approaching && driverPoint != null) "%.3f,%.3f".format(driverPoint.first, driverPoint.second) else "trip")
        if (routeKey != key && from != null && to != null && from != to) {
            routeKey = key
            viewLifecycleOwner.lifecycleScope.launch {
                AppGraph.repository.route(
                    com.qolari.userlite.net.RoutePoint(from.first, from.second),
                    com.qolari.userlite.net.RoutePoint(to.first, to.second),
                ).onSuccess { road ->
                    if (road.size >= 2) _binding?.map?.route = road
                }
            }
        }
        binding.map.driver = driver?.let { d ->
            if (d.lat != null && d.lng != null) d.lat to d.lng else null
        }
        binding.map.driverHeading = driver?.heading?.toFloat() ?: 0f
        binding.map.showUser = trip.state == "requested"
    }

    private fun setStars(value: Int) {
        stars = value.coerceIn(1, 5)
        val selected = ContextCompat.getColor(requireContext(), R.color.ql_black)
        val unselected = ContextCompat.getColor(requireContext(), R.color.ql_gray_400)
        val buttons = listOf(binding.star1, binding.star2, binding.star3, binding.star4, binding.star5)
        buttons.forEachIndexed { index, button ->
            button.setImageResource(if (index < stars) R.drawable.ic_star else R.drawable.ic_star_outline)
            button.imageTintList = ColorStateList.valueOf(if (index < stars) selected else unselected)
            button.setOnClickListener { setStars(index + 1) }
        }
    }

    private fun confirmCancel() {
        val uuid = viewModel.state.value.trip?.uuid ?: return
        MaterialAlertDialogBuilder(requireContext())
            .setTitle(R.string.trip_cancel_confirm)
            .setPositiveButton(R.string.trip_cancel_yes) { _, _ -> viewModel.cancel(uuid) }
            .setNegativeButton(R.string.trip_cancel_keep, null)
            .show()
    }

    private fun markTerminalSeen() {
        val trip = viewModel.state.value.trip ?: return
        if (trip.state in setOf("completed", "cancelled", "no_drivers")) {
            SeenTrips.lastTerminal = trip.uuid
            lifecycleScope.launch { AppGraph.session.markTerminal(trip.uuid) }
        }
    }

    private fun goHome() {
        markTerminalSeen()
        ride.reset()
        if (isAdded) findNavController().navigate(R.id.action_active_to_home)
    }

    private fun tip(amountCents: Int) {
        val trip = viewModel.state.value.trip ?: return
        lifecycleScope.launch {
            AppGraph.repository.tip(trip.uuid, amountCents)
                .onSuccess { viewModel.refresh() }
                .onFailure {
                    Snackbar.make(binding.root, R.string.trip_tip_error, Snackbar.LENGTH_SHORT).show()
                }
        }
    }

    private fun rideCheck(status: String) {
        val trip = viewModel.state.value.trip ?: return
        lifecycleScope.launch {
            AppGraph.repository.rideCheck(trip.uuid, status, trip.pickup.lat, trip.pickup.lng)
                .onSuccess {
                    if (status == "help") {
                        MaterialAlertDialogBuilder(requireContext())
                            .setTitle(R.string.trip_ride_help)
                            .setMessage(R.string.trip_ride_help_detail)
                            .setPositiveButton(R.string.safety_call_112) { _, _ ->
                                startActivity(android.content.Intent(
                                    android.content.Intent.ACTION_DIAL,
                                    android.net.Uri.parse("tel:112"),
                                ))
                            }
                            .setNegativeButton(R.string.safety_close, null)
                            .show()
                    } else {
                        Snackbar.make(binding.root, R.string.trip_ride_ok_sent, Snackbar.LENGTH_SHORT).show()
                    }
                }
                .onFailure {
                    Snackbar.make(binding.root, R.string.trip_ride_error, Snackbar.LENGTH_SHORT).show()
                }
        }
    }

    private fun showReceipt() {
        val trip = viewModel.state.value.trip ?: return
        lifecycleScope.launch {
            AppGraph.repository.receipt(trip.uuid)
                .onSuccess { r ->
                    if (r == null) return@onSuccess
                    val body = r.lines.joinToString("\n") { "${it.label}: ${money(it.amountCents)}" } +
                        "\n\nTotal: ${r.total}"
                    MaterialAlertDialogBuilder(requireContext())
                        .setTitle(R.string.trip_receipt)
                        .setMessage(body)
                        .setPositiveButton(android.R.string.ok, null)
                        .show()
                }
                .onFailure {
                    Snackbar.make(binding.root, R.string.trip_receipt_error, Snackbar.LENGTH_SHORT).show()
                }
        }
    }

    private fun showDispute() {
        val trip = viewModel.state.value.trip ?: return
        val input = EditText(requireContext()).apply {
            hint = getString(R.string.trip_dispute_hint)
            setPadding(dp(20), dp(8), dp(20), dp(8))
        }
        MaterialAlertDialogBuilder(requireContext())
            .setTitle(R.string.trip_dispute)
            .setView(input)
            .setPositiveButton(R.string.trip_dispute_send) { _, _ ->
                val reason = input.text.toString().trim()
                if (reason.isNotEmpty()) {
                    lifecycleScope.launch {
                        AppGraph.repository.dispute(trip.uuid, reason)
                            .onSuccess {
                                Snackbar.make(binding.root, R.string.trip_dispute_ok, Snackbar.LENGTH_LONG).show()
                            }
                            .onFailure {
                                Snackbar.make(binding.root, R.string.trip_dispute_error, Snackbar.LENGTH_SHORT).show()
                            }
                    }
                }
            }
            .setNegativeButton(R.string.trip_cancel_keep, null)
            .show()
    }

    private fun money(cents: Int): String =
        String.format(java.util.Locale("pt", "PT"), "%.2f €", cents / 100.0)

    private fun dp(value: Int) = (value * resources.displayMetrics.density).toInt()

    override fun onResume() {
        super.onResume()
        _binding?.map?.onResume()
    }

    override fun onPause() {
        _binding?.map?.onPause()
        super.onPause()
    }

    override fun onDestroyView() {
        _binding?.map?.onDestroy()
        super.onDestroyView()
        _binding = null
    }
}
