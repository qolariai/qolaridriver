package com.qolari.userlite.ui.home

import android.Manifest
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.activity.result.contract.ActivityResultContracts
import androidx.core.view.isVisible
import androidx.fragment.app.Fragment
import androidx.fragment.app.activityViewModels
import androidx.fragment.app.viewModels
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import androidx.navigation.fragment.findNavController
import androidx.recyclerview.widget.LinearLayoutManager
import com.google.android.material.snackbar.Snackbar
import com.qolari.userlite.R
import com.qolari.userlite.data.LocationSource
import com.qolari.userlite.databinding.FragmentHomeBinding
import com.qolari.userlite.net.PromoCard
import com.qolari.userlite.net.RoutePoint
import com.qolari.userlite.net.Suggestion
import com.qolari.userlite.ui.map.GeocodeClient
import com.qolari.userlite.ui.ride.RideViewModel
import kotlinx.coroutines.launch

/** Início (captura 010): título, pesquisa, mapa e sugestões; scroll vertical + carrosséis horizontais. */
class HomeFragment : Fragment() {

    private var _binding: FragmentHomeBinding? = null
    private val binding get() = _binding!!
    private val viewModel: HomeViewModel by viewModels()
    private val ride: RideViewModel by activityViewModels()
    private var lastPickupFix: Pair<Double, Double>? = null
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
        binding.ongoingCard.setOnClickListener {
            ride.reopenTrip()
            findNavController().navigate(R.id.action_home_to_active)
        }
        binding.zoomIn.setOnClickListener { binding.map.zoomIn() }
        binding.zoomOut.setOnClickListener { binding.map.zoomOut() }
        binding.locateButton.setOnClickListener {
            if (locationSource.hasPermission) locate()
            else locationPermission.launch(Manifest.permission.ACCESS_FINE_LOCATION)
        }

        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                viewModel.state.collect { state ->
                    binding.loading.isVisible = state.loading && state.home == null
                    binding.refresh.isRefreshing = false
                    binding.errorCard.isVisible = state.error != null && state.home == null
                    binding.errorText.text = state.error ?: getString(R.string.home_error)
                    binding.scroll.isVisible = state.home != null
                    state.home?.let { render(it) }
                    // Viagens em curso: se o utilizador ainda não fechou o ecrã da viagem, abre-o
                    // uma vez; se fechou (X), mostra o cartão para voltar quando quiser.
                    val active = state.activeTrip
                    val ongoing = active != null &&
                        active.state !in setOf("completed", "cancelled", "no_drivers")
                    binding.ongoingCard.isVisible = ongoing && ride.tripDismissed
                    binding.ongoingDetail.text = active?.dropoff?.address.orEmpty()
                    if (ongoing && !ride.tripDismissed && !navigatedToTrip &&
                        findNavController().currentDestination?.id == R.id.homeFragment
                    ) {
                        navigatedToTrip = true
                        findNavController().navigate(R.id.action_home_to_active)
                    }
                }
            }
        }
    }

    override fun onResume() {
        super.onResume()
        if (firstLoad) {
            firstLoad = false
            viewModel.load()
        } else {
            navigatedToTrip = false
            viewModel.load(quiet = true)
        }
        applyCurrentPickup()
    }

    private fun render(home: com.qolari.userlite.net.HomeResponse) {
        binding.headline.text = home.headline
        binding.savedPlace.text = home.savedPlace.name
        binding.mapSavedPlace.text = "De " + home.savedPlace.name
        // O mapa da pagina inicial mostra os carros a volta da recolha, como na captura 030.
        binding.map.userLocation = home.savedPlace.lat to home.savedPlace.lng
        binding.map.showCars = true
        binding.map.recenter()
        suggestionAdapter.submit(home.suggestions)
        promoAdapter.submit(home.promos)
        applyCurrentPickup(force = true)
    }

    /**
     * O pickup passa a ser a localização real do telemóvel (GPS), com o endereço obtido por
     * reverse geocoding. Sem permissão/fix, mantém-se o local guardado do servidor.
     */
    private fun applyCurrentPickup(force: Boolean = false) {
        if (!locationSource.hasPermission) return
        val fix = locationSource.lastKnown() ?: return
        if (!force && fix == lastPickupFix) return
        lastPickupFix = fix
        val label = getString(R.string.home_current_location)
        ride.setPickup(RoutePoint(fix.first, fix.second, label))
        binding.map.userLocation = fix
        binding.map.showCars = true
        binding.map.recenter()
        binding.savedPlace.text = label
        binding.mapSavedPlace.text = "De $label"
        GeocodeClient.reverse(requireContext(), fix.first, fix.second) { address ->
            if (_binding != null && lastPickupFix == fix) {
                ride.setPickup(RoutePoint(fix.first, fix.second, address))
                binding.savedPlace.text = address
                binding.mapSavedPlace.text = "De $address"
            }
        }
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
        lastPickupFix = null
        applyCurrentPickup(force = true)
        Snackbar.make(binding.root, R.string.home_location_updated, Snackbar.LENGTH_SHORT).show()
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
