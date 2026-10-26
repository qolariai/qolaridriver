package com.qolari.drivereplica.ui.manage

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.core.view.isVisible
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import androidx.navigation.fragment.findNavController
import com.qolari.drivereplica.R
import com.qolari.drivereplica.data.AppGraph
import com.qolari.drivereplica.databinding.FragmentAirportQueueBinding
import com.qolari.drivereplica.net.AirportQueueResponse
import kotlinx.coroutines.launch

/** Fila do aeroporto: posicao e entrada/saida. */
class AirportQueueFragment : Fragment() {

    private var _binding: FragmentAirportQueueBinding? = null
    private val binding get() = _binding!!

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentAirportQueueBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        binding.queueBack.setOnClickListener { findNavController().popBackStack() }
        binding.queueJoin.setOnClickListener { action("join") }
        binding.queueLeave.setOnClickListener { action("leave") }
        load()
    }

    private fun load() {
        lifecycleScope.launch {
            AppGraph.repository.airportQueue()
                .onSuccess { render(it) }
                .onFailure { error() }
        }
    }

    private fun action(value: String) {
        lifecycleScope.launch {
            AppGraph.repository.airportQueueAction(value)
                .onSuccess { render(it) }
                .onFailure { error() }
        }
    }

    private fun render(q: AirportQueueResponse) {
        binding.queueError.isVisible = false
        binding.queueJoin.isVisible = !q.joined
        binding.queueLeave.isVisible = q.joined
        if (q.joined) {
            binding.queuePosition.text = getString(R.string.queue_position, q.position ?: 0)
            binding.queueDetail.text = getString(R.string.queue_waiting, q.waiting, q.airport)
        } else {
            binding.queuePosition.text = getString(R.string.queue_not_joined)
            binding.queueDetail.text = getString(R.string.queue_waiting, q.waiting, q.airport)
        }
    }

    private fun error() {
        binding.queueError.isVisible = true
        binding.queueError.setText(R.string.queue_error)
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
