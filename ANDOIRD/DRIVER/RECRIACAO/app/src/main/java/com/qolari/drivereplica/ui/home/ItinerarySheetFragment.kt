package com.qolari.drivereplica.ui.home

import android.os.Bundle
import android.view.View
import androidx.fragment.app.Fragment
import androidx.fragment.app.activityViewModels
import androidx.navigation.fragment.findNavController
import com.qolari.drivereplica.R
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

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        val b = FragmentItinerarySheetBinding.bind(view)
        binding = b
        b.itineraryBack.setOnClickListener { findNavController().popBackStack() }

        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                drive.state.collectLatest { d -> bind(b, d.trip) }
            }
        }
    }

    private fun bind(b: FragmentItinerarySheetBinding, trip: com.qolari.drivereplica.drive.ActiveTrip?) {
        row(b.itineraryFareRow, R.string.itinerary_fare, trip?.fare.orEmpty())
        row(b.itineraryTripRow, R.string.itinerary_trip_number, trip?.uuid.orEmpty())
        row(
            b.itineraryTimeRow, R.string.itinerary_time,
            SimpleDateFormat("MM/dd/yy HH:mm:ss z", Locale.UK).format(Date()),
        )
        row(b.itineraryPassengerRow, R.string.itinerary_passenger, trip?.riderName.orEmpty())
        row(b.itineraryViaRow, R.string.itinerary_via, trip?.product.orEmpty())
        row(
            b.itineraryFromRow, R.string.itinerary_from,
            trip?.pickupAddress?.takeIf { it.isNotBlank() } ?: trip?.address.orEmpty(),
        )
        row(
            b.itineraryDestinationRow, R.string.itinerary_destination,
            listOfNotNull(trip?.address, trip?.city).filter { it.isNotBlank() }.joinToString(", "),
        )
        row(b.itineraryNotesRow, R.string.itinerary_notes, getString(R.string.itinerary_notes_body))
        // O bloco do condutor sai do perfil local: o servidor não o manda na tarefa da viagem.
        row(b.itineraryNameRow, R.string.itinerary_name, trip?.riderName?.let { "" } ?: "")
        row(b.itineraryLiveryRow, R.string.itinerary_livery, "")
        row(b.itineraryPlateRow, R.string.itinerary_plate, "")
        row(b.itineraryCapacityRow, R.string.itinerary_capacity, "")
    }

    private fun row(binding: ItemItineraryRowBinding, labelRes: Int, value: String) {
        binding.itineraryRowLabel.setText(labelRes)
        binding.itineraryRowValue.text = value
    }

    override fun onDestroyView() {
        binding = null
        super.onDestroyView()
    }
}
