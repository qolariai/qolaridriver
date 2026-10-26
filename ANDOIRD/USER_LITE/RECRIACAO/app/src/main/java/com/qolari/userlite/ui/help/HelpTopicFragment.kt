package com.qolari.userlite.ui.help

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import androidx.navigation.fragment.findNavController
import com.qolari.userlite.databinding.FragmentHelpTopicBinding

/** Artigo de ajuda: conteúdo próprio do laboratório (não copia texto da Uber). */
class HelpTopicFragment : Fragment() {

    private var _binding: FragmentHelpTopicBinding? = null
    private val binding get() = _binding!!

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentHelpTopicBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        binding.title.text = arguments?.getString("title").orEmpty()
        binding.backButton.setOnClickListener { findNavController().navigateUp() }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
