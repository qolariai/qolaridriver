package com.qolari.userlite.ui.account

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import androidx.core.os.bundleOf
import androidx.core.view.isVisible
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import androidx.navigation.NavOptions
import androidx.navigation.fragment.findNavController
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import com.google.android.material.snackbar.Snackbar
import com.qolari.userlite.R
import com.qolari.userlite.databinding.DialogAccountEditBinding
import com.qolari.userlite.databinding.FragmentAccountBinding
import com.qolari.userlite.net.Place
import com.qolari.userlite.net.SessionResponse
import com.qolari.userlite.ui.info.InfoFragment
import kotlinx.coroutines.launch

/**
 * Gerir conta (captura 041): separadores Casa / Informações pessoais / Segurança /
 * Privacidade e Dados. Em Casa aparece o perfil, os três atalhos e as sugestões.
 */
class AccountFragment : Fragment() {

    private var _binding: FragmentAccountBinding? = null
    private val binding get() = _binding!!
    private val viewModel: AccountViewModel by viewModels()

    private var session: SessionResponse? = null
    private var home: Place? = null
    private var places: List<Place> = emptyList()

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentAccountBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        binding.backButton.setOnClickListener { findNavController().navigateUp() }
        binding.homeRow.setOnClickListener { chooseHome() }
        binding.personalCard.setOnClickListener { selectTab(1) }
        binding.securityCard.setOnClickListener { selectTab(2) }
        binding.privacyCard.setOnClickListener { selectTab(3) }
        binding.tabHome.setOnClickListener { selectTab(0) }
        binding.tabPersonal.setOnClickListener { selectTab(1) }
        binding.tabSecurity.setOnClickListener { selectTab(2) }
        binding.tabPrivacy.setOnClickListener { selectTab(3) }
        binding.editButton.setOnClickListener { editPersonal() }
        binding.signOutButton.setOnClickListener { confirmSignOut() }
        binding.verifyButton.setOnClickListener {
            openInfo(getString(R.string.account_verify), buildString {
                append(getString(R.string.account_verify_body))
                append("\n\n")
                append(getString(R.string.account_phone))
                append(": ")
                append(session?.phone.orEmpty())
            })
        }
        selectTab(0)

        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                viewModel.state.collect { state ->
                    state.session?.let { s ->
                        session = s
                        binding.avatar.text = s.firstName.take(1).uppercase().ifBlank { "Q" }
                        binding.name.text = s.name.uppercase()
                        binding.detail.text = s.email
                        binding.personalName.text = s.name
                        binding.personalEmail.text = s.email
                        binding.personalPhone.text = s.phone
                        binding.securityBody.text = getString(
                            R.string.account_security_body,
                            s.phone,
                            s.name,
                        )
                    }
                    state.home?.let { h ->
                        home = h
                        binding.homeValue.text = h.address
                    }
                    if (state.places.isNotEmpty()) places = state.places
                    state.error?.let { message ->
                        Snackbar.make(binding.root, message, Snackbar.LENGTH_LONG).show()
                    }
                    if (state.signedOut) {
                        val options = NavOptions.Builder().setPopUpTo(R.id.nav_main, true).build()
                        findNavController().navigate(R.id.welcomeFragment, null, options)
                    }
                }
            }
        }
    }

    /** Mostra o separador pedido e desliza a barra preta por baixo do título escolhido. */
    private fun selectTab(index: Int) {
        val tabs = listOf(binding.tabHome, binding.tabPersonal, binding.tabSecurity, binding.tabPrivacy)
        val contents = listOf(binding.homeContent, binding.personalContent, binding.securityContent, binding.privacyContent)
        contents.forEachIndexed { i, content -> content.isVisible = i == index }
        tabs.forEachIndexed { i, tab -> tab.alpha = if (i == index) 1f else 0.8f }
        binding.tabIndicator.post {
            val tab = tabs[index]
            binding.tabIndicator.layoutParams = binding.tabIndicator.layoutParams.apply { width = tab.width }
            binding.tabIndicator.translationX = tab.left.toFloat()
        }
    }

    private fun chooseHome() {
        val current = home
        val options = buildList {
            current?.let { add(it) }
            add(Place(id = "home", name = getString(R.string.account_home_default), line2 = getString(R.string.account_home_default_detail)))
            places.filter { p -> p.id != current?.id && p.id != "home" }.forEach { add(it) }
        }
        val labels = options.map { "${it.name} · ${it.line2.ifBlank { it.address }}" }.toTypedArray()
        MaterialAlertDialogBuilder(requireContext())
            .setTitle(R.string.account_home)
            .setItems(labels) { _, which ->
                val chosen = options[which]
                viewModel.saveHome(chosen.id) { saved ->
                    if (saved != null) {
                        binding.homeValue.text = saved.address
                        Snackbar.make(binding.root, R.string.account_home_saved, Snackbar.LENGTH_SHORT).show()
                    } else {
                        Snackbar.make(binding.root, R.string.account_save_error, Snackbar.LENGTH_LONG).show()
                    }
                }
            }
            .setNegativeButton(R.string.error_cancel, null)
            .show()
    }

    private fun editPersonal() {
        val current = session ?: return
        val dialogBinding = DialogAccountEditBinding.inflate(layoutInflater)
        dialogBinding.firstName.setText(current.firstName)
        dialogBinding.lastName.setText(current.name.removePrefix(current.firstName).trim())
        dialogBinding.email.setText(current.email)

        val dialog = MaterialAlertDialogBuilder(requireContext())
            .setTitle(R.string.account_personal)
            .setView(dialogBinding.root)
            .setPositiveButton(R.string.account_save, null)
            .setNegativeButton(R.string.error_cancel, null)
            .create()

        dialog.setOnShowListener {
            val save = dialog.getButton(android.app.AlertDialog.BUTTON_POSITIVE) as Button
            save.setOnClickListener {
                val first = dialogBinding.firstName.text?.toString()?.trim().orEmpty()
                val last = dialogBinding.lastName.text?.toString()?.trim().orEmpty()
                val email = dialogBinding.email.text?.toString()?.trim().orEmpty()
                var valid = true
                if (first.isBlank()) {
                    dialogBinding.firstNameLayout.error = getString(R.string.account_name_required)
                    valid = false
                } else {
                    dialogBinding.firstNameLayout.error = null
                }
                if (email.isNotBlank() && (!email.contains("@") || email.startsWith("@") || email.endsWith("@"))) {
                    dialogBinding.emailLayout.error = getString(R.string.account_email_invalid)
                    valid = false
                } else {
                    dialogBinding.emailLayout.error = null
                }
                if (!valid) return@setOnClickListener
                save.isEnabled = false
                viewModel.saveAccount(first, last, email) { ok, message ->
                    if (ok) {
                        dialog.dismiss()
                        Snackbar.make(binding.root, R.string.account_saved, Snackbar.LENGTH_SHORT).show()
                    } else {
                        save.isEnabled = true
                        dialogBinding.error.text = message ?: getString(R.string.account_save_error)
                        dialogBinding.error.isVisible = true
                    }
                }
            }
        }
        dialog.show()
    }

    private fun confirmSignOut() {
        MaterialAlertDialogBuilder(requireContext())
            .setTitle(R.string.account_security)
            .setMessage(R.string.account_sign_out_confirm)
            .setPositiveButton(R.string.account_sign_out) { _, _ -> viewModel.signOut() }
            .setNegativeButton(R.string.error_cancel, null)
            .show()
    }

    private fun openInfo(title: String, body: String) {
        findNavController().navigate(
            R.id.infoFragment,
            bundleOf(InfoFragment.ARG_TITLE to title, InfoFragment.ARG_BODY to body)
        )
    }

    override fun onDestroyView() {
        _binding = null
        super.onDestroyView()
    }
}
