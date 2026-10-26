package com.qolari.userlite.ui.legal

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.core.os.bundleOf
import androidx.fragment.app.Fragment
import androidx.navigation.fragment.findNavController
import androidx.recyclerview.widget.LinearLayoutManager
import com.qolari.userlite.R
import com.qolari.userlite.databinding.FragmentLegalBinding

/** Legal (captura 025): lista de tópicos com conteúdo próprio do laboratório. */
class LegalFragment : Fragment() {

    private var _binding: FragmentLegalBinding? = null
    private val binding get() = _binding!!

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentLegalBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        val adapter = LegalAdapter { topic ->
            findNavController().navigate(
                R.id.action_legal_to_topic,
                bundleOf("title" to topic.title),
            )
        }
        binding.topics.layoutManager = LinearLayoutManager(requireContext())
        binding.topics.adapter = adapter
        adapter.submit(LegalTopics.all())
        binding.backButton.setOnClickListener { findNavController().navigateUp() }
        binding.closeButton.setOnClickListener { findNavController().navigateUp() }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
