package com.qolari.userlite.ui.search

import android.os.Bundle
import android.text.Editable
import android.text.TextWatcher
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.core.view.isVisible
import androidx.core.view.WindowInsetsCompat
import androidx.core.view.WindowInsetsControllerCompat
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
import com.qolari.userlite.databinding.FragmentSearchBinding
import com.qolari.userlite.net.Place
import com.qolari.userlite.net.RoutePoint
import com.qolari.userlite.ui.ride.RideViewModel
import kotlinx.coroutines.launch

/** Pesquisa de destino (captura 031): recolha, destino, sugestões e atalhos. */
class SearchFragment : Fragment() {

    private var _binding: FragmentSearchBinding? = null
    private val binding get() = _binding!!
    private val viewModel: SearchViewModel by viewModels()
    private val ride: RideViewModel by activityViewModels()
    private lateinit var adapter: PlaceAdapter
    private var savedPlace: Place? = null

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentSearchBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        adapter = PlaceAdapter { select(it) }
        binding.places.layoutManager = LinearLayoutManager(requireContext())
        binding.places.adapter = adapter
        binding.pickupText.text = ride.pickup.value.address
        binding.backButton.setOnClickListener {
            hideKeyboard()
            findNavController().navigateUp()
        }
        binding.savedRow.setOnClickListener {
            val place = savedPlace
            if (place == null) {
                Snackbar.make(binding.root, R.string.search_saved_empty, Snackbar.LENGTH_SHORT).show()
            } else {
                select(place)
            }
        }

        binding.destinationInput.addTextChangedListener(object : TextWatcher {
            override fun beforeTextChanged(s: CharSequence?, start: Int, count: Int, after: Int) = Unit
            override fun onTextChanged(s: CharSequence?, start: Int, before: Int, count: Int) = Unit
            override fun afterTextChanged(s: Editable?) {
                viewModel.search(s?.toString().orEmpty())
            }
        })
        binding.destinationInput.setOnEditorActionListener { _, _, _ ->
            val first = viewModel.state.value.places.firstOrNull()
            if (first != null) select(first)
            true
        }

        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                viewModel.state.collect { state ->
                    adapter.submit(state.places)
                    binding.loading.isVisible = state.loading
                    binding.emptyText.isVisible = !state.loading && state.places.isEmpty() &&
                        binding.destinationInput.text.isNotEmpty()
                    if (state.error != null) {
                        Snackbar.make(binding.root, state.error, Snackbar.LENGTH_LONG).show()
                    }
                }
            }
        }
        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                viewModel.savedPlace.collect { place ->
                    savedPlace = place
                    binding.savedLabel.text = place?.let {
                        "${getString(R.string.search_saved)} · ${it.name}"
                    } ?: getString(R.string.search_saved)
                }
            }
        }

        viewModel.search("")
        binding.destinationInput.requestFocus()
        binding.destinationInput.postDelayed({
            WindowInsetsControllerCompat(requireActivity().window, binding.root)
                .show(WindowInsetsCompat.Type.ime())
        }, 180)
    }

    private fun select(place: Place) {
        ride.setDropoff(RoutePoint(place.lat, place.lng, place.address))
        hideKeyboard()
        findNavController().navigate(R.id.action_search_to_ride)
    }

    private fun hideKeyboard() {
        WindowInsetsControllerCompat(requireActivity().window, binding.root)
            .hide(WindowInsetsCompat.Type.ime())
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
