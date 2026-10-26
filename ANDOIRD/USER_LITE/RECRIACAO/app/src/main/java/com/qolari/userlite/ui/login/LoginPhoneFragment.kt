package com.qolari.userlite.ui.login

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.core.os.bundleOf
import androidx.core.view.isVisible
import androidx.fragment.app.Fragment
import androidx.navigation.fragment.findNavController
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import com.qolari.userlite.R
import com.qolari.userlite.databinding.FragmentLoginPhoneBinding

/** Login por telefone (captura 001): país, número, "Encontrar a minha conta" e "Seguinte". */
class LoginPhoneFragment : Fragment() {

    private var _binding: FragmentLoginPhoneBinding? = null
    private val binding get() = _binding!!

    private var prefix = "+351"
    private var flag = "🇵🇹"

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentLoginPhoneBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        binding.countryButton.setOnClickListener { chooseCountry() }
        binding.nextButton.setOnClickListener { submit() }
        binding.findAccount.setOnClickListener {
            if (binding.phoneInput.text.toString().filter { it.isDigit() }.length == 9) {
                submit()
            } else {
                binding.phoneInput.requestFocus()
            }
        }
        binding.phoneInput.setOnEditorActionListener { _, _, _ ->
            submit(); true
        }
    }

    private fun chooseCountry() {
        val labels = arrayOf(
            getString(R.string.login_country_pt),
            getString(R.string.login_country_es),
            getString(R.string.login_country_fr),
            getString(R.string.login_country_br),
        )
        val values = arrayOf("+351" to "🇵🇹", "+34" to "🇪🇸", "+33" to "🇫🇷", "+55" to "🇧🇷")
        MaterialAlertDialogBuilder(requireContext())
            .setTitle(R.string.login_country_title)
            .setItems(labels) { _, which ->
                prefix = values[which].first
                flag = values[which].second
                binding.prefix.text = prefix
                binding.countryFlag.text = flag
            }
            .show()
    }

    private fun submit() {
        val national = binding.phoneInput.text.toString().filter { it.isDigit() }
        if (national.length != 9) {
            binding.error.text = getString(R.string.login_phone_invalid)
            binding.error.isVisible = true
            return
        }
        binding.error.isVisible = false
        findNavController().navigate(
            R.id.action_login_to_code,
            bundleOf("phone" to (prefix + national)),
        )
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
