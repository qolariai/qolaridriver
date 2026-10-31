package com.qolari.drivereplica.ui.home

import android.os.Bundle
import android.view.View
import androidx.fragment.app.Fragment
import androidx.fragment.app.activityViewModels
import androidx.navigation.fragment.findNavController
import com.qolari.drivereplica.R
import com.qolari.drivereplica.data.AppGraph
import com.qolari.drivereplica.databinding.FragmentItinerarySheetBinding
import com.qolari.drivereplica.databinding.ItemItineraryRowBinding
import com.qolari.drivereplica.drive.DriveViewModel
import com.qolari.drivereplica.drive.TripPhase
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.launch
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle

/**
 * "Folha de itinerário" (print 2026-10-30, 02:06).
 *
 * Comprovativo com os dados da viagem em curso. Os rótulos seguem o original em inglês
 * (é um documento para mostrar às autoridades) e os valores vêm todos da viagem que o
 * servidor devolveu — nada é inventado.
 */
class ItinerarySheetFragment : Fragment(R.layout.fragment_itinerary_sheet) {

    private val drive: DriveViewModel by activityViewModels { DriveViewModel.Factory }
    private var binding: FragmentItinerarySheetBinding? = null

    /** Perfil do condutor (nome/matrícula/lotação para o bloco "Driver"). Nulo até o servidor responder. */
    private var profile: com.qolari.drivereplica.ui.manage.ProfileSummary? = null

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        val b = FragmentItinerarySheetBinding.bind(view)
        binding = b
        b.itineraryBack.setOnClickListener { findNavController().popBackStack() }

        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                launch {
                    // O bloco do condutor vem do perfil (`get-profile-hub`): a tarefa da viagem não
                    // traz o nome do condutor nem a matrícula.
                    profile = AppGraph.repository.profile().getOrNull()
                    binding?.let { bind(it, drive.state.value.trip) }
                }
                launch {
                    drive.state.collectLatest { d -> binding?.let { bind(it, d.trip) } }
                }
            }
        }
    }

    private fun bind(b: FragmentItinerarySheetBinding, trip: com.qolari.drivereplica.drive.ActiveTrip?) {
        val p = profile
        // Fare: o servidor manda o valor por extenso ("4,00 €") no driverUpfrontFare.
        row(b.itineraryFareRow, R.string.itinerary_fare, trip?.fare.orEmpty())
        row(b.itineraryTripRow, R.string.itinerary_trip_number, tripRef(trip))
        row(b.itineraryTimeRow, R.string.itinerary_time, tripTime(trip))
        row(b.itineraryPassengerRow, R.string.itinerary_passenger, trip?.riderName.orEmpty())
        row(b.itineraryViaRow, R.string.itinerary_via, trip?.product.orEmpty())
        row(
            b.itineraryFromRow, R.string.itinerary_from,
            trip?.pickupAddress?.takeIf { it.isNotBlank() } ?: pickupFallback(trip),
        )
        // Destination: o destino que o servidor mandou. A recolha mora em `address`, por isso não
        // serve de destino (era o bug que mostrava a recolha nos dois campos).
        row(
            b.itineraryDestinationRow, R.string.itinerary_destination,
            trip?.dropoffAddress?.takeIf { it.isNotBlank() } ?: dropoffFallback(trip),
        )
        row(b.itineraryNotesRow, R.string.itinerary_notes, getString(R.string.itinerary_notes_body))
        // Bloco do condutor: nome e matrícula vêm do perfil; a lotação, do veículo do perfil.
        row(b.itineraryNameRow, R.string.itinerary_name, p?.name.orEmpty())
        row(b.itineraryLiveryRow, R.string.itinerary_livery, "")   // a Qolari não usa número de frota
        row(b.itineraryPlateRow, R.string.itinerary_plate, p?.plate.orEmpty())
        row(b.itineraryCapacityRow, R.string.itinerary_capacity, p?.capacity.orEmpty())
    }

    /**
     * "Time": a hora em que a viagem começou (ou foi aceite, se ainda não arrancou). Antes usava-se
     * `Date()` — a hora de abrir o ecrã, que mudava a cada visita e nada tinha a ver com a viagem.
     */
    private fun tripTime(trip: com.qolari.drivereplica.drive.ActiveTrip?): String {
        val sec = trip?.startedAtSec ?: trip?.acceptedAtSec ?: return ""
        return SimpleDateFormat("MM/dd/yy HH:mm:ss z", Locale.UK).format(Date(sec * 1000))
    }

    /** Número curto e legível: os primeiros 8 caracteres do UUID, em maiúsculas. */
    private fun tripRef(trip: com.qolari.drivereplica.drive.ActiveTrip?): String =
        trip?.uuid?.takeIf { it.isNotBlank() }?.substringBefore('-')?.uppercase().orEmpty()

    /** Recolha: `pickupAddress`, ou a morada da paragem atual quando a fase é a recolha. */
    private fun pickupFallback(trip: com.qolari.drivereplica.drive.ActiveTrip?): String =
        if (trip?.phase == TripPhase.TO_PICKUP || trip?.phase == TripPhase.AT_PICKUP) trip.address else ""

    /** Destino: na ida à recolha o `address` da tarefa ainda é a recolha, por isso não serve. */
    private fun dropoffFallback(trip: com.qolari.drivereplica.drive.ActiveTrip?): String =
        if (trip?.phase == TripPhase.ON_TRIP) trip.address else ""

    private fun row(binding: ItemItineraryRowBinding, labelRes: Int, value: String) {
        binding.itineraryRowLabel.setText(labelRes)
        binding.itineraryRowValue.text = value
    }

    override fun onDestroyView() {
        binding = null
        super.onDestroyView()
    }
}
