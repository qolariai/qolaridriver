package com.qolari.userlite.ui.wallet

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
import androidx.recyclerview.widget.LinearLayoutManager
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import com.google.android.material.snackbar.Snackbar
import com.qolari.userlite.R
import com.qolari.userlite.databinding.FragmentWalletBinding
import com.qolari.userlite.net.Payment
import kotlinx.coroutines.launch

/** Carteira: saldo Qolari Cash e formas de pagamento (captura 021, adaptada a passageiro). */
class WalletFragment : Fragment() {

    private var _binding: FragmentWalletBinding? = null
    private val binding get() = _binding!!
    private val viewModel: WalletViewModel by viewModels()
    private lateinit var adapter: PaymentAdapter
    private var profiles: List<Payment> = emptyList()
    private var selectedId: String = "cash"

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentWalletBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        adapter = PaymentAdapter { select(it) }
        binding.payments.layoutManager = LinearLayoutManager(requireContext())
        binding.payments.adapter = adapter
        binding.backButton.setOnClickListener { findNavController().navigateUp() }
        binding.addPayment.setOnClickListener { choosePayment() }
        binding.withdrawButton.setOnClickListener {
            Snackbar.make(binding.root, R.string.wallet_withdraw_unavailable, Snackbar.LENGTH_SHORT).show()
        }

        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                viewModel.state.collect { state ->
                    binding.loading.isVisible = state.loading
                    binding.error.isVisible = state.error != null
                    binding.error.text = state.error
                    state.wallet?.let { w ->
                        binding.balanceValue.text = w.cash.label
                        binding.cashValue.text = w.cash.label
                        val nextMonday = java.time.LocalDate.now()
                            .with(java.time.temporal.TemporalAdjusters.next(java.time.DayOfWeek.MONDAY))
                            .format(java.time.format.DateTimeFormatter.ofPattern("dd/MM"))
                        binding.paymentScheduled.text = getString(R.string.wallet_scheduled, nextMonday)
                        profiles = w.profiles
                        selectedId = w.payment.id
                        adapter.submit(w.profiles, w.payment.id)
                    }
                }
            }
        }
        viewModel.load()
    }

    private fun select(payment: Payment) {
        viewModel.select(payment.id)
    }

    private fun choosePayment() {
        if (profiles.isEmpty()) {
            Snackbar.make(binding.root, R.string.wallet_error, Snackbar.LENGTH_SHORT).show()
            return
        }
        val labels = profiles.map { "${it.label} · ${it.detail}" }.toTypedArray()
        val checked = profiles.indexOfFirst { it.id == selectedId }.coerceAtLeast(0)
        MaterialAlertDialogBuilder(requireContext())
            .setTitle(R.string.wallet_choose)
            .setSingleChoiceItems(labels, checked) { dialog, which ->
                viewModel.select(profiles[which].id)
                dialog.dismiss()
            }
            .setNegativeButton(R.string.error_cancel, null)
            .show()
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
