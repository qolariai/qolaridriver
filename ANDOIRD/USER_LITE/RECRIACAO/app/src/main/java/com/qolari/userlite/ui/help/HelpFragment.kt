package com.qolari.userlite.ui.help

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.core.os.bundleOf
import androidx.fragment.app.Fragment
import androidx.navigation.fragment.findNavController
import androidx.recyclerview.widget.LinearLayoutManager
import com.qolari.userlite.R
import com.qolari.userlite.databinding.FragmentHelpBinding

/** Ajuda (captura 020, tema escuro da própria página): tópicos com pesquisa local. */
class HelpFragment : Fragment() {

    private var _binding: FragmentHelpBinding? = null
    private val binding get() = _binding!!
    private lateinit var adapter: HelpAdapter

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentHelpBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        adapter = HelpAdapter { open(it) }
        binding.topics.layoutManager = LinearLayoutManager(requireContext())
        binding.topics.adapter = adapter
        adapter.submit(HelpTopics.all())
        binding.backButton.setOnClickListener { findNavController().navigateUp() }
        binding.searchButton.setOnClickListener { filter() }
        binding.searchInput.setOnEditorActionListener { _, _, _ -> filter(); true }
    }

    private fun filter() {
        val q = binding.searchInput.text.toString().trim().lowercase()
        adapter.submit(HelpTopics.all().filter { q.isEmpty() || it.title.lowercase().contains(q) })
    }

    private fun open(topic: HelpTopic) {
        findNavController().navigate(
            R.id.action_help_to_topic,
            bundleOf("title" to topic.title),
        )
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
