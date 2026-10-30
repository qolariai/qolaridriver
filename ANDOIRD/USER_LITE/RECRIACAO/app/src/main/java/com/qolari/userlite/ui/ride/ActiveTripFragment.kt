package com.qolari.userlite.ui.ride

import android.content.res.ColorStateList
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
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
import com.qolari.userlite.databinding.FragmentActiveTripBinding
import com.qolari.userlite.net.Trip
import com.qolari.userlite.ui.map.DirectionsClient
import kotlinx.coroutines.launch

/** Viagem em curso: procura, motorista a caminho, PIN, em viagem, fim e avaliação. */
class ActiveTripFragment : Fragment() {

    private var lastRouteKey: String? = null

    /** Rota pelas estradas já carregada; sobrevive aos renders seguintes (o polling não a apaga). */
    private var roadRoute: List<Pair<Double, Double>>? = null

    private var _binding: FragmentActiveTripBinding? = null
    private val binding get() = _binding!!
    private val viewModel: ActiveTripViewModel by viewModels()
    private val ride: RideViewModel by activityViewModels()
    private var stars = 5

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentActiveTripBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        binding.closeButton.setOnClickListener { goHome() }
        binding.homeButton.setOnClickListener { goHome() }
        binding.retryButton.setOnClickListener {
            ride.reset()
            findNavController().navigate(R.id.action_active_to_search)
        }
        binding.cancelButton.setOnClickListener { confirmCancel() }
        binding.error.setOnClickListener { viewModel.refresh() }
        binding.skipRating.setOnClickListener {
            val uuid = viewModel.state.value.trip?.uuid
            if (uuid != null && viewModel.state.value.trip?.canRate == true) viewModel.rate(uuid, 0) else goHome()
        }
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
        super.onStop()
        viewModel.stop()
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
                title = getString(R.string.trip_searching)
                detail = getString(R.string.trip_searching_detail)
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
        binding.fareCard.isVisible = trip.state == "completed"
        binding.fareValue.text = trip.fare.label
        binding.ratingContainer.isVisible = trip.state == "completed" && trip.canRate
        binding.cancelButton.isVisible = trip.canCancel && !canceling
        binding.retryButton.isVisible = trip.state == "no_drivers"
        binding.homeButton.isVisible = trip.state in setOf("completed", "cancelled", "no_drivers")

        val points = mutableListOf<Pair<Double, Double>>()
        if (trip.pickup.lat != 0.0) points.add(trip.pickup.lat to trip.pickup.lng)
        if (trip.dropoff.lat != 0.0) points.add(trip.dropoff.lat to trip.dropoff.lng)
        val routeKey = "${trip.pickup.lat},${trip.pickup.lng}-${trip.dropoff.lat},${trip.dropoff.lng}"
        if (routeKey != lastRouteKey) {
            lastRouteKey = routeKey
            roadRoute = null
            if (trip.pickup.lat != 0.0 && trip.dropoff.lat != 0.0) {
                DirectionsClient.fetch(requireContext(), trip.pickup.lat, trip.pickup.lng, trip.dropoff.lat, trip.dropoff.lng) { pts ->
                    if (_binding != null && pts.size > 1 && lastRouteKey == routeKey) {
                        roadRoute = pts
                        binding.map.route = pts
                    }
                }
            }
        }
        binding.map.route = roadRoute ?: points
        binding.map.dropoff = if (trip.dropoff.lat != 0.0) trip.dropoff.lat to trip.dropoff.lng else null
        binding.map.driver = driver?.let { d ->
            if (d.lat != null && d.lng != null) d.lat to d.lng else null
        }
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

    private fun goHome() {
        ride.reset()
        if (isAdded) findNavController().navigate(R.id.action_active_to_home)
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
