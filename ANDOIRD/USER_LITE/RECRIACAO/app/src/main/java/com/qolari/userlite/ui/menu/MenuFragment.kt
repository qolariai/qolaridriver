package com.qolari.userlite.ui.menu

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
import androidx.navigation.NavOptions
import androidx.navigation.fragment.findNavController
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import com.qolari.userlite.R
import com.qolari.userlite.data.UiPrefs
import com.qolari.userlite.databinding.FragmentMenuBinding
import kotlinx.coroutines.launch

/** Menu (captura 042): perfil, atalhos, saldo, conta, promoções, legal e terminar sessão. */
class MenuFragment : Fragment() {

    private var _binding: FragmentMenuBinding? = null
    private val binding get() = _binding!!
    private val viewModel: MenuViewModel by viewModels()

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentMenuBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        binding.closeButton.setOnClickListener { findNavController().navigateUp() }
        binding.helpTile.setOnClickListener { findNavController().navigate(R.id.action_menu_to_help) }
        binding.walletTile.setOnClickListener { findNavController().navigate(R.id.action_menu_to_wallet) }
        binding.activityTile.setOnClickListener { findNavController().navigate(R.id.action_menu_to_activity) }
        binding.accountRow.setOnClickListener { findNavController().navigate(R.id.action_menu_to_account) }
        binding.supportRow.setOnClickListener { findNavController().navigate(R.id.action_menu_to_support) }
        binding.safetyRow.setOnClickListener { findNavController().navigate(R.id.action_menu_to_safety) }
        binding.savedRow.setOnClickListener { findNavController().navigate(R.id.action_menu_to_saved) }
        binding.extrasRow.setOnClickListener { findNavController().navigate(R.id.action_menu_to_extras) }
        binding.appearanceRow.setOnClickListener { findNavController().navigate(R.id.action_menu_to_appearance) }
        binding.promotionsRow.setOnClickListener { findNavController().navigate(R.id.action_menu_to_promotions) }
        binding.legalRow.setOnClickListener { findNavController().navigate(R.id.action_menu_to_legal) }
        binding.cashRow.setOnClickListener { findNavController().navigate(R.id.action_menu_to_wallet) }
        binding.signOutButton.setOnClickListener { confirmSignOut() }
        if (UiPrefs.simple(requireContext())) {
            binding.extrasRow.isVisible = false
            binding.savedRow.isVisible = false
            binding.promotionsRow.isVisible = false
        }

        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                viewModel.state.collect { state ->
                    state.session?.let { s ->
                        binding.name.text = s.name
                        binding.avatar.text = s.firstName.take(1).uppercase().ifBlank { "Q" }
                        binding.rating.text = String.format("★ %.1f", s.rating)
                    }
                    state.wallet?.let { w -> binding.cashValue.text = w.cash.label }
                    if (state.signedOut) {
                        val options = NavOptions.Builder()
                            .setPopUpTo(R.id.nav_main, true)
                            .build()
                        findNavController().navigate(R.id.welcomeFragment, null, options)
                    }
                }
            }
        }
        viewModel.load()
    }

    private fun confirmSignOut() {
        MaterialAlertDialogBuilder(requireContext())
            .setTitle(R.string.menu_sign_out_confirm)
            .setMessage(R.string.menu_sign_out_detail)
            .setPositiveButton(R.string.menu_sign_out_yes) { _, _ -> viewModel.signOut() }
            .setNegativeButton(R.string.menu_cancel, null)
            .show()
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
