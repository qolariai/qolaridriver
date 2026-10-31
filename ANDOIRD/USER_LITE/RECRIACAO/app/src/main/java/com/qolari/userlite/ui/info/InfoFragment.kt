package com.qolari.userlite.ui.info

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import androidx.navigation.fragment.findNavController
import com.qolari.userlite.databinding.FragmentInfoBinding

/** Pagina informativa com conteudo proprio (privacidade, seguranca, verificacao). */
class InfoFragment : Fragment() {

    private var _binding: FragmentInfoBinding? = null
    private val binding get() = _binding!!

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentInfoBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        binding.backButton.setOnClickListener { findNavController().navigateUp() }
        binding.infoTitle.text = requireArguments().getString(ARG_TITLE).orEmpty()
        binding.infoBody.text = requireArguments().getString(ARG_BODY).orEmpty()
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }

    companion object {
        const val ARG_TITLE = "title"
        const val ARG_BODY = "body"
        const val ROUTE = "infoFragment"

        /** Bundle para `navigate(infoFragment, args(...))`. */
        fun args(title: String, body: String): Bundle =
            Bundle().apply {
                putString(ARG_TITLE, title)
                putString(ARG_BODY, body)
            }
    }
}
