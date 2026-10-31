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
    private var detailsExpanded = false

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentActiveTripBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        binding.closeButton.setOnClickListener { dismissTrip() }
        binding.homeButton.setOnClickListener { goHome() }
        binding.menuButton.setOnClickListener { findNavController().navigate(R.id.menuFragment) }
        binding.retryButton.setOnClickListener {
            ride.reset()
            findNavController().navigate(R.id.action_active_to_search)
        }
        binding.cancelButton.setOnClickListener { confirmCancel() }
        binding.error.setOnClickListener { viewModel.refresh() }
        binding.detailsHeader.setOnClickListener { setDetailsExpanded(!detailsExpanded) }
        binding.detailsToggle.setOnClickListener { setDetailsExpanded(!detailsExpanded) }
        binding.messageButton.setOnClickListener { contactDriver(message = true) }
        binding.callButton.setOnClickListener { contactDriver(message = false) }
        binding.changeDropoff.setOnClickListener {
            findNavController().navigate(R.id.action_active_to_search)
        }
        binding.securityButton.setOnClickListener { showSecurity() }
        binding.shareButton.setOnClickListener { shareTrip() }
        binding.skipRating.setOnClickListener {
            val uuid = viewModel.state.value.trip?.uuid
            if (uuid != null && viewModel.state.value.trip?.canRate == true) viewModel.rate(uuid, 0) else goHome()
        }
        binding.sendRating.setOnClickListener {
            viewModel.state.value.trip?.let { viewModel.rate(it.uuid, stars) }
        }
        setStars(stars)
        setDetailsExpanded(false)

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

    /** Alterna o cartão "Detalhes da viagem" entre recolhido e expandido, como no original. */
    private fun setDetailsExpanded(expanded: Boolean) {
        detailsExpanded = expanded
        binding.detailsBody.isVisible = expanded
        binding.detailsCollapsed.isVisible = !expanded
        binding.detailsToggle.rotation = if (expanded) 180f else 0f
        binding.detailsToggle.contentDescription = getString(
            if (expanded) R.string.trip_details_collapse else R.string.trip_details_expand
        )
    }

    private fun render(trip: Trip, canceling: Boolean) {
        val title: String
        val detail: String
        var etaText: String? = null
        var progress = 0
        when (trip.state) {
            "requested" -> {
                title = getString(R.string.trip_searching)
                detail = getString(R.string.trip_searching_detail)
                progress = 20
            }
            "accepted" -> {
                val eta = trip.driverEtaMin
                title = getString(R.string.trip_accepted)
                detail = getString(R.string.trip_accepted_detail)
                etaText = eta?.let { getString(R.string.trip_pickup_in, it) }
                progress = 60
            }
            "arrived" -> {
                title = getString(R.string.trip_arrived)
                detail = if (trip.pin.isNullOrBlank()) {
                    getString(R.string.trip_arrived_no_pin)
                } else {
                    getString(R.string.trip_arrived_detail)
                }
                progress = 75
            }
            "in_progress" -> {
                title = getString(R.string.trip_in_progress)
                detail = trip.tripEtaMin?.let { getString(R.string.trip_in_progress_detail, it) }
                    ?: getString(R.string.trip_in_progress)
                progress = 90
            }
            "completed" -> {
                title = getString(R.string.trip_completed)
                detail = getString(R.string.trip_completed_detail)
                progress = 100
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
        binding.statusEta.text = etaText.orEmpty()
        binding.statusEta.isVisible = !etaText.isNullOrBlank()
        binding.searchProgress.isVisible = progress in 1..99
        binding.searchProgress.progress = progress

        val driver = trip.driver
        binding.driverCard.isVisible = driver != null
        if (driver != null) {
            binding.avatar.text = driver.name.take(1).uppercase().ifBlank { "Q" }
            binding.driverName.text = driver.name
            binding.driverDetail.text = driver.vehicle?.let { listOfNotNull(it.make, it.model).joinToString(" ").trim() }
                ?.takeIf { it.isNotBlank() }
                ?: driver.vehicle?.label.orEmpty()
            binding.vehiclePlate.text = driver.vehicle?.plate.orEmpty()
            binding.driverRating.text = String.format("★ %.2f", driver.rating)
            // O backend envia o número da licença da autoridade reguladora; sem ele não inventamos.
            binding.driverLicense.text = driver.licenseNumber
                ?.takeIf { it.isNotBlank() }
                ?.let { getString(R.string.trip_license, it) }
                .orEmpty()
            binding.driverLicense.isVisible = !driver.licenseNumber.isNullOrBlank()
        }

        val pin = trip.pin
        binding.pinCard.isVisible = !pin.isNullOrBlank()
        binding.pinValue.text = pin.orEmpty()
        binding.pickupText.text = trip.pickup.address
        binding.dropoffText.text = trip.dropoff.address
        binding.detailsCollapsed.text = getString(R.string.trip_accepted_at, trip.pickup.address)
        binding.detailsFare.text = trip.fare.label
        binding.detailsPayment.text = trip.paymentLabel()
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

    /** Diálogo igual ao original: "NÃO" em botão escuro (acção segura) e cancelar em botão claro. */
    private fun confirmCancel() {
        val trip = viewModel.state.value.trip ?: return
        val name = trip.driver?.name
        val onWay = trip.state == "accepted" || trip.state == "arrived"
        MaterialAlertDialogBuilder(requireContext())
            .setTitle(
                if (name.isNullOrBlank()) getString(R.string.trip_cancel_confirm)
                else getString(R.string.trip_cancel_with, name)
            )
            .apply { if (onWay) setMessage(R.string.trip_cancel_driver_on_way) }
            .setPositiveButton(R.string.trip_cancel_no) { _, _ -> }
            .setNegativeButton(R.string.trip_cancel_sim) { _, _ -> viewModel.cancel(trip.uuid) }
            .show()
    }

    /** Ligar ou enviar SMS ao motorista, com o número do próprio servidor (nunca inventado). */
    private fun contactDriver(message: Boolean) {
        val phone = viewModel.state.value.trip?.driver?.phone?.takeIf { it.isNotBlank() }
        if (phone == null) {
            Snackbar.make(binding.root, R.string.trip_contact_unavailable, Snackbar.LENGTH_SHORT).show()
            return
        }
        val uri = android.net.Uri.parse(if (message) "sms:$phone" else "tel:$phone")
        val intent = android.content.Intent(if (message) android.content.Intent.ACTION_SENDTO
            else android.content.Intent.ACTION_DIAL, uri)
        runCatching { startActivity(intent) }.onFailure {
            Snackbar.make(binding.root, R.string.trip_contact_unavailable, Snackbar.LENGTH_SHORT).show()
        }
    }

    private fun showSecurity() {
        val trip = viewModel.state.value.trip ?: return
        val body = buildString {
            append(getString(R.string.trip_security_body))
            trip.driver?.let {
                append("\n\n")
                append(it.name)
                it.vehicle?.plate?.takeIf { p -> p.isNotBlank() }?.let { p ->
                    append(" · ")
                    append(p)
                }
                it.licenseNumber?.takeIf { l -> l.isNotBlank() }?.let { l ->
                    append("\n")
                    append(getString(R.string.trip_license, l))
                }
            }
        }
        findNavController().navigate(
            R.id.infoFragment,
            com.qolari.userlite.ui.info.InfoFragment.args(getString(R.string.trip_security), body)
        )
    }

    private fun shareTrip() {
        val trip = viewModel.state.value.trip ?: return
        val text = getString(
            R.string.trip_share_text,
            trip.driver?.name.orEmpty(),
            trip.vehiclePlate(),
            trip.pickup.address,
            trip.dropoff.address,
        )
        val send = android.content.Intent(android.content.Intent.ACTION_SEND).apply {
            type = "text/plain"
            putExtra(android.content.Intent.EXTRA_TEXT, text)
        }
        startActivity(android.content.Intent.createChooser(send, getString(R.string.trip_share_action)))
    }

    private fun Trip.vehiclePlate(): String = driver?.vehicle?.plate.orEmpty()

    private fun Trip.paymentLabel(): String =
        if (payment == "card") getString(R.string.ride_payment_card) else getString(R.string.ride_payment_cash)

    private fun goHome() {
        ride.reset()
        if (isAdded) findNavController().navigate(R.id.action_active_to_home)
    }

    /**
     * Fecha o acompanhamento sem cancelar a viagem: o Início fica livre e mostra o cartão
     * "Viagem em curso" para voltar. Sem isto o Início reabria a viagem logo a seguir e o X
     * parecia não fazer nada.
     */
    private fun dismissTrip() {
        ride.dismissTrip()
        if (isAdded) findNavController().navigate(R.id.action_active_to_home)
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
