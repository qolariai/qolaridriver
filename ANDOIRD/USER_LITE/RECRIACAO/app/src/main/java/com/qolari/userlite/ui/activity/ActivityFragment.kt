package com.qolari.userlite.ui.activity

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.core.view.isVisible
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import androidx.navigation.fragment.findNavController
import androidx.recyclerview.widget.LinearLayoutManager
import com.qolari.userlite.R
import com.qolari.userlite.databinding.FragmentActivityBinding
import kotlinx.coroutines.launch

/** Atividade (captura 022): estado vazio com ilustração própria e histórico real. */
class ActivityFragment : Fragment() {

    private var _binding: FragmentActivityBinding? = null
    private val binding get() = _binding!!
    private val viewModel: ActivityViewModel by viewModels()
    private lateinit var adapter: HistoryAdapter

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentActivityBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        adapter = HistoryAdapter(
            onClick = { trip -> openDetail(trip) },
        )
        binding.trips.layoutManager = LinearLayoutManager(requireContext())
        binding.trips.adapter = adapter
        binding.backButton.setOnClickListener { findNavController().navigateUp() }
        binding.menuButton.setOnClickListener { findNavController().navigate(R.id.menuFragment) }
        binding.emptyAction.setOnClickListener { findNavController().navigate(R.id.searchFragment) }
        binding.filterAll.setOnClickListener { showFilter() }

        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                viewModel.state.collect { state ->
                    binding.loading.isVisible = state.loading
                    binding.error.isVisible = state.error != null
                    binding.error.text = state.error
                    binding.emptyCard.isVisible = !state.loading && state.error == null && state.trips.isEmpty()
                    binding.trips.isVisible = state.trips.isNotEmpty()
                    adapter.submit(state.trips)
                }
            }
        }
        viewModel.load()
    }

    /** Detalhe da viagem: percurso, produto, valor e estado, com o conteúdo do próprio histórico. */
    private fun openDetail(trip: com.qolari.userlite.net.HistoryTrip) {
        val state = when (trip.state) {
            "completed" -> getString(R.string.activity_trip_state_completed)
            "cancelled" -> getString(R.string.activity_trip_state_cancelled)
            "no_drivers" -> getString(R.string.activity_trip_state_no_drivers)
            "requested" -> getString(R.string.activity_trip_state_requested)
            "accepted" -> getString(R.string.activity_trip_state_accepted)
            "arrived" -> getString(R.string.activity_trip_state_arrived)
            "in_progress" -> getString(R.string.activity_trip_state_in_progress)
            else -> trip.state
        }
        val charged = trip.state == "completed" && trip.fare.label.isNotBlank()
        val body = buildString {
            append(trip.date)
            append("\n\n")
            append(getString(R.string.trip_pickup))
            append(": ")
            append(trip.pickup.ifBlank { getString(R.string.activity_route_unknown) })
            append("\n")
            append(getString(R.string.trip_dropoff))
            append(": ")
            append(trip.dropoff.ifBlank { getString(R.string.activity_route_unknown) })
            append("\n")
            append(getString(R.string.activity_detail_product))
            append(": ")
            append(trip.product)
            append("\n")
            append(getString(R.string.activity_detail_state))
            append(": ")
            append(state)
            append("\n")
            append(getString(R.string.activity_detail_total))
            append(": ")
            append(if (charged) trip.fare.label else getString(R.string.activity_no_charge))
        }
        findNavController().navigate(
            R.id.infoFragment,
            com.qolari.userlite.ui.info.InfoFragment.args(getString(R.string.activity_detail_title), body)
        )
    }

    private fun showFilter() {
        val labels = arrayOf(
            getString(R.string.activity_filter_all),
            getString(R.string.activity_trip_state_completed),
            getString(R.string.activity_trip_state_cancelled),
            getString(R.string.activity_trip_state_no_drivers),
        )
        com.google.android.material.dialog.MaterialAlertDialogBuilder(requireContext())
            .setTitle(R.string.activity_filter_title)
            .setItems(labels) { _, which -> adapter.submit(viewModel.filtered(which)) }
            .show()
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}