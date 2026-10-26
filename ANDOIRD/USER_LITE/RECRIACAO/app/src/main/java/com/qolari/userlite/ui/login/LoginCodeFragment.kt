package com.qolari.userlite.ui.login

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
import com.qolari.userlite.R
import com.qolari.userlite.databinding.FragmentLoginCodeBinding
import kotlinx.coroutines.launch

/** Código de 4 dígitos (não capturado na Lite; fluxo nativo do laboratório, marcado [inf]). */
class LoginCodeFragment : Fragment() {

    private var _binding: FragmentLoginCodeBinding? = null
    private val binding get() = _binding!!
    private val viewModel: LoginViewModel by viewModels()
    private var phone: String = ""

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentLoginCodeBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        phone = arguments?.getString("phone").orEmpty()
        binding.subtitle.text = getString(R.string.login_code_subtitle, phone)
        binding.backButton.setOnClickListener { findNavController().navigateUp() }
        binding.verifyButton.setOnClickListener { verify() }
        binding.resendButton.setOnClickListener {
            // O laboratorio nao envia SMS: o botao preenche o codigo fixo, em vez de prometer um envio.
            binding.codeInput.setText(getString(R.string.login_code_lab_value))
            binding.codeInput.setSelection(binding.codeInput.text?.length ?: 0)
        }
        binding.codeInput.setOnEditorActionListener { _, _, _ -> verify(); true }

        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                viewModel.state.collect { state ->
                    binding.verifyButton.isEnabled = !state.loading
                    binding.verifyButton.text = if (state.loading) {
                        getString(R.string.loading)
                    } else {
                        getString(R.string.login_code_verify)
                    }
                    binding.error.isVisible = state.error != null
                    binding.error.text = state.error
                    if (state.session != null) {
                        findNavController().navigate(R.id.action_code_to_home)
                    }
                }
            }
        }
    }

    private fun verify() {
        val code = binding.codeInput.text.toString().trim()
        if (code.length != 4) {
            binding.error.text = getString(R.string.login_code_invalid)
            binding.error.isVisible = true
            return
        }
        viewModel.login(phone, code)
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
