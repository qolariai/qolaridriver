package com.qolari.drivereplica.ui.home

import android.os.Bundle
import android.view.View
import android.widget.LinearLayout
import androidx.core.view.isVisible
import androidx.fragment.app.Fragment
import androidx.fragment.app.activityViewModels
import androidx.navigation.fragment.findNavController
import com.qolari.drivereplica.R
import com.qolari.drivereplica.databinding.FragmentTripPlannerBinding
import com.qolari.drivereplica.drive.ActiveTrip
import com.qolari.drivereplica.drive.DriveViewModel
import com.qolari.drivereplica.drive.TripPhase
import com.qolari.drivereplica.state.PreferencesViewModel
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.launch
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
/**
 * "Planeador de viagem" (print 2026-10-30, 01:57).
 *
 * Aberto pelo botão de lista do canto inferior direito do mapa durante a recolha. Mostra a
 * recolha e a entrega como no original; os três pontos abrem o cancelamento com motivos
 * (print 01:59) e "Folha de itinerário" abre o comprovativo (print 02:06).
 */
class TripPlannerFragment : Fragment(R.layout.fragment_trip_planner) {

    private val drive: DriveViewModel by activityViewModels { DriveViewModel.Factory }
    private val prefs: PreferencesViewModel by activityViewModels()
    private var binding: FragmentTripPlannerBinding? = null

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        val b = FragmentTripPlannerBinding.bind(view)
        binding = b
        b.plannerClose.setOnClickListener { findNavController().popBackStack() }
        // Os três pontos levam ao cancelamento por motivos (print 01:59), na recolha.
        b.plannerPickupMenu.setOnClickListener { findNavController().navigate(R.id.plannerCancelFragment) }
        b.plannerDropoffMenu.setOnClickListener { findNavController().navigate(R.id.plannerCancelFragment) }
        b.plannerSheetLink.setOnClickListener { findNavController().navigate(R.id.itinerarySheetFragment) }
        b.plannerFilters.setOnClickListener { findNavController().navigate(R.id.preferencesServicesFragment) }
        b.plannerSearch.setOnClickListener { findNavController().popBackStack() }
        // "Parar novos pedidos": desliga a disponibilidade (não aceita mais viagens).
        b.plannerStopIcon.setOnClickListener {
            prefs.store.setStopped(b.plannerStopLabel.text == getString(R.string.planner_stop_requests))
            findNavController().popBackStack()
        }

        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                combine(drive.state, prefs.store.stopped) { d, _ -> d }.collect { d -> bind(b, d.trip) }
            }
        }    }

    private fun bind(b: FragmentTripPlannerBinding, trip: ActiveTrip?) {
        val product = trip?.product?.takeIf { it.isNotBlank() }
            ?: getString(R.string.drive_product_fallback)
        val rider = trip?.riderName.orEmpty()
        // Print 01:57: "Recolha · UberX Priority" / "annalisa" — produto na 1.ª linha,
        // nome do passageiro na 2.ª. O destino não aparece neste ecrã (está na folha).
        b.plannerPickupText.text = getString(R.string.planner_offset, getString(R.string.planner_pickup), product) +
            (if (rider.isNotBlank()) "\n$rider" else "")
        b.plannerDropoffText.text = getString(R.string.planner_offset, getString(R.string.planner_dropoff), product) +
            (if (rider.isNotBlank()) "\n$rider" else "")
        // Durante a viagem o ponto aceso passa a ser a entrega.
        val onTrip = trip?.phase == TripPhase.ON_TRIP
        b.plannerPickupDot.background = requireContext().getDrawable(
            if (onTrip) R.drawable.bg_planner_gray else R.drawable.bg_planner_green
        )
        b.plannerDropoffDot.background = requireContext().getDrawable(
            if (onTrip) R.drawable.bg_planner_green else R.drawable.bg_planner_gray
        )
        // O botão alterna entre "Parar novos pedidos" e "Retomar pedidos".
        b.plannerStopLabel.setText(
            if (prefs.store.stopped.value) R.string.planner_resume_requests
            else R.string.planner_stop_requests
        )
    }

    override fun onDestroyView() {
        binding = null
        super.onDestroyView()
    }
}
