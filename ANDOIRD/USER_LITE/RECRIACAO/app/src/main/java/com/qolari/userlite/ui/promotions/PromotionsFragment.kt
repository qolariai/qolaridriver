package com.qolari.userlite.ui.promotions

import android.os.Bundle
import android.text.Editable
import android.text.TextWatcher
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
import com.qolari.userlite.databinding.FragmentPromotionsBinding
import kotlinx.coroutines.launch

/** Promoções (captura 024): código, aplicar, preços e lista de códigos da conta. */
class PromotionsFragment : Fragment() {

    private var _binding: FragmentPromotionsBinding? = null
    private val binding get() = _binding!!
    private val viewModel: PromotionsViewModel by viewModels()
    private lateinit var adapter: AppliedPromoAdapter

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentPromotionsBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        adapter = AppliedPromoAdapter()
        binding.applied.layoutManager = LinearLayoutManager(requireContext())
        binding.applied.adapter = adapter
        binding.backButton.setOnClickListener { findNavController().navigateUp() }
        binding.menuButton.setOnClickListener { findNavController().navigate(R.id.menuFragment) }
        binding.pricesButton.setOnClickListener { findNavController().navigate(R.id.searchFragment) }
        binding.applyButton.setOnClickListener {
            viewModel.apply(binding.codeInput.text.toString().trim())
        }
        binding.codeInput.addTextChangedListener(object : TextWatcher {
            override fun beforeTextChanged(s: CharSequence?, start: Int, count: Int, after: Int) = Unit
            override fun onTextChanged(s: CharSequence?, start: Int, before: Int, count: Int) = Unit
            override fun afterTextChanged(s: Editable?) {
                binding.applyButton.isEnabled = !s.isNullOrBlank()
            }
        })

        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                viewModel.state.collect { state ->
                    binding.loading.isVisible = state.loading
                    binding.message.text = state.message ?: state.error
                    binding.message.setTextColor(
                        requireContext().getColor(if (state.error != null) R.color.ql_red else R.color.ql_gray_500)
                    )
                    binding.applied.isVisible = state.applied.isNotEmpty()
                    binding.appliedTitle.isVisible = state.applied.isNotEmpty()
                    adapter.submit(state.applied)
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
