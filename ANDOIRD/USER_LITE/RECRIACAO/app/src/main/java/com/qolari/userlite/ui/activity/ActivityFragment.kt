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
        adapter = HistoryAdapter()
        binding.trips.layoutManager = LinearLayoutManager(requireContext())
        binding.trips.adapter = adapter
        binding.backButton.setOnClickListener { findNavController().navigateUp() }
        binding.menuButton.setOnClickListener { findNavController().navigate(R.id.menuFragment) }
        binding.emptyAction.setOnClickListener { findNavController().navigate(R.id.searchFragment) }

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

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
