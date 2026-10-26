package com.qolari.userlite.ui.home

import android.Manifest
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.activity.result.contract.ActivityResultContracts
import androidx.core.view.isVisible
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import androidx.navigation.fragment.findNavController
import androidx.recyclerview.widget.LinearLayoutManager
import com.google.android.material.snackbar.Snackbar
import com.qolari.userlite.R
import com.qolari.userlite.data.AppGraph
import com.qolari.userlite.data.LocationSource
import com.qolari.userlite.data.PendingTripStore
import com.qolari.userlite.databinding.FragmentHomeBinding
import com.qolari.userlite.net.PromoCard
import com.qolari.userlite.net.Suggestion
import kotlinx.coroutines.launch

/** Início (captura 010): título, pesquisa, mapa e sugestões; scroll vertical + carrosséis horizontais. */
class HomeFragment : Fragment() {

    private var _binding: FragmentHomeBinding? = null
    private val binding get() = _binding!!
    private val viewModel: HomeViewModel by viewModels()
    private lateinit var suggestionAdapter: SuggestionAdapter
    private lateinit var promoAdapter: PromoAdapter
    private lateinit var locationSource: LocationSource
    private var firstLoad = true
    private var navigatedToTrip = false

    private val locationPermission =
        registerForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
            if (granted) locate() else Snackbar.make(
                binding.root, R.string.home_location_denied, Snackbar.LENGTH_SHORT
            ).show()
        }

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentHomeBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        locationSource = LocationSource(requireContext())
        suggestionAdapter = SuggestionAdapter { onSuggestion(it) }
        promoAdapter = PromoAdapter { onPromo(it) }
        binding.suggestions.layoutManager = LinearLayoutManager(requireContext(), LinearLayoutManager.HORIZONTAL, false)
        binding.suggestions.adapter = suggestionAdapter
        binding.promos.layoutManager = LinearLayoutManager(requireContext(), LinearLayoutManager.HORIZONTAL, false)
        binding.promos.adapter = promoAdapter

        binding.menuButton.setOnClickListener {
            findNavController().navigate(R.id.action_home_to_menu)
        }
        binding.searchBar.setOnClickListener {
            findNavController().navigate(R.id.action_home_to_search)
        }
        binding.retryButton.setOnClickListener { viewModel.load() }
        binding.refresh.setOnRefreshListener { viewModel.load(quiet = true) }
        binding.locateButton.setOnClickListener {
            if (locationSource.hasPermission) locate()
            else locationPermission.launch(Manifest.permission.ACCESS_FINE_LOCATION)
        }
        binding.zoomInButton.setOnClickListener { binding.map.zoomIn() }
        binding.zoomOutButton.setOnClickListener { binding.map.zoomOut() }

        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                viewModel.state.collect { state ->
                    binding.loading.isVisible = state.loading && state.home == null
                    binding.refresh.isRefreshing = false
                    binding.errorCard.isVisible = state.error != null && state.home == null
                    binding.errorText.text = state.error ?: getString(R.string.home_error)
                    binding.scroll.isVisible = state.home != null
                    state.home?.let { render(it) }
                    if (state.activeTrip != null && !navigatedToTrip) {
                        navigatedToTrip = true
                        findNavController().navigate(R.id.action_home_to_active)
                    }
                }
            }
        }
    }

    override fun onResume() {
        super.onResume()
        _binding?.let { b ->
            b.map.onResume()
            if (locationSource.hasPermission) locationSource.lastKnown()?.let { b.map.userLocation = it }
        }
        if (firstLoad) {
            firstLoad = false
            viewModel.load()
        } else {
            navigatedToTrip = false
            viewModel.load(quiet = true)
        }
        retryPending()
    }

    private fun retryPending() {
        val pending = PendingTripStore.load(requireContext()) ?: return
        viewLifecycleOwner.lifecycleScope.launch {
            AppGraph.repository.request(
                pending.pickup, pending.dropoff, pending.productId,
                pending.payment, pending.promoCode, pending.scheduledAt, pending.stops,
            ).onSuccess {
                PendingTripStore.clear(requireContext())
                Snackbar.make(binding.root, R.string.home_pending_sent, Snackbar.LENGTH_LONG).show()
                findNavController().navigate(R.id.action_home_to_active)
            }
        }
    }

    override fun onPause() {
        _binding?.map?.onPause()
        super.onPause()
    }

    private fun render(home: com.qolari.userlite.net.HomeResponse) {
        binding.headline.text = home.headline
        binding.savedPlace.text = listOf(home.savedPlace.name, home.savedPlace.line2)
            .filter { it.isNotBlank() }.joinToString(" · ")
        binding.mapSavedPlace.text = getString(R.string.trip_pickup) + ": " + home.savedPlace.name
        suggestionAdapter.submit(home.suggestions)
        promoAdapter.submit(home.promos)
    }

    private fun onSuggestion(item: Suggestion) {
        // A unica vertical do âmbito é ride-hailing: qualquer sugestao abre a procura de destino.
        findNavController().navigate(R.id.action_home_to_search)
    }

    private fun onPromo(item: PromoCard) {
        findNavController().navigate(R.id.promotionsFragment)
    }

    private fun locate() {
        val fix = locationSource.lastKnown()
        if (fix == null) {
            Snackbar.make(binding.root, R.string.home_location_unavailable, Snackbar.LENGTH_SHORT).show()
            return
        }
        binding.map.userLocation = fix
        binding.map.recenter()
        viewModel.updateLocation(fix.first, fix.second)
        Snackbar.make(binding.root, R.string.home_location_updated, Snackbar.LENGTH_SHORT).show()
    }

    override fun onDestroyView() {
        _binding?.map?.onDestroy()
        super.onDestroyView()
        _binding = null
    }
}
