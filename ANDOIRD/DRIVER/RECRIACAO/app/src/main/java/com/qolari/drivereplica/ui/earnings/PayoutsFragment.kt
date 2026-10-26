package com.qolari.drivereplica.ui.earnings

import android.os.Bundle
import android.text.InputType
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Toast
import androidx.core.view.isVisible
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import androidx.navigation.fragment.findNavController
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import com.qolari.drivereplica.R
import com.qolari.drivereplica.data.AppGraph
import com.qolari.drivereplica.databinding.FragmentPayoutsBinding
import com.qolari.drivereplica.net.PayoutDto
import com.qolari.drivereplica.net.StatementRow
import com.qolari.drivereplica.net.TaxInfo
import kotlinx.coroutines.launch
import java.text.DateFormat
import java.util.Date

/** Saldo, transferencia (IBAN/Instant Pay), historico e extratos mensais. */
class PayoutsFragment : Fragment() {

    private var _binding: FragmentPayoutsBinding? = null
    private val binding get() = _binding!!
    private var balance = ""

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentPayoutsBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        binding.payoutsBack.setOnClickListener { findNavController().popBackStack() }
        binding.payoutsIban.setOnClickListener { confirm(false) }
        binding.payoutsInstant.setOnClickListener { confirm(true) }
        binding.payoutsAdjust.setOnClickListener { chooseAdjustment() }
        binding.payoutsInvoices.setOnClickListener { showInvoices() }
        binding.payoutsTax.setOnClickListener { showTax() }
        load()
    }

    private fun load() {
        lifecycleScope.launch {
            AppGraph.repository.payoutMethods()
                .onSuccess {
                    balance = it.balance
                    binding.payoutsBalance.text = it.balance
                    binding.payoutsError.isVisible = false
                }
                .onFailure { error() }
            AppGraph.repository.payoutHistory()
                .onSuccess { renderHistory(it) }
                .onFailure { error() }
            AppGraph.repository.statements()
                .onSuccess { renderStatements(it) }
                .onFailure { error() }
        }
    }

    private fun confirm(instant: Boolean) {
        val title = if (instant) R.string.payouts_instant else R.string.payouts_iban
        MaterialAlertDialogBuilder(requireContext())
            .setTitle(title)
            .setMessage(getString(R.string.payouts_confirm, balance))
            .setPositiveButton(R.string.payouts_confirm_yes) { _, _ -> run(instant) }
            .setNegativeButton(R.string.payouts_cancel, null)
            .show()
    }

    private fun run(instant: Boolean) {
        binding.payoutsIban.isEnabled = false
        binding.payoutsInstant.isEnabled = false
        lifecycleScope.launch {
            AppGraph.repository.requestPayout(instant)
                .onSuccess {
                    binding.payoutsBalance.text = it.balance
                    balance = it.balance
                    android.widget.Toast.makeText(requireContext(), R.string.payouts_done, android.widget.Toast.LENGTH_SHORT).show()
                    load()
                }
                .onFailure { error() }
            binding.payoutsIban.isEnabled = true
            binding.payoutsInstant.isEnabled = true
        }
    }

    private fun renderHistory(rows: List<PayoutDto>) {
        binding.payoutsHistoryList.removeAllViews()
        if (rows.isEmpty()) {
            binding.payoutsHistoryList.addView(text(getString(R.string.payouts_history_empty)))
            return
        }
        rows.forEach { p ->
            val date = DateFormat.getDateInstance(DateFormat.SHORT).format(Date(p.createdAt))
            val status = when (p.status) {
                "paid" -> getString(R.string.payouts_paid)
                "pending" -> getString(R.string.payouts_pending)
                else -> p.status
            }
            binding.payoutsHistoryList.addView(text("${p.amount}  ·  $status  ·  $date"))
        }
    }

    private fun renderStatements(rows: List<StatementRow>) {
        binding.payoutsStatementList.removeAllViews()
        rows.forEach { s ->
            binding.payoutsStatementList.addView(text(getString(R.string.payouts_month, s.month, s.net, s.trips)))
        }
    }

    private fun chooseAdjustment() {
        val ids = arrayOf("tolls", "manual_fare", "other")
        val labels = arrayOf(
            getString(R.string.payouts_kind_tolls),
            getString(R.string.payouts_kind_manual),
            getString(R.string.payouts_kind_other),
        )
        MaterialAlertDialogBuilder(requireContext())
            .setTitle(R.string.payouts_adjust)
            .setItems(labels) { _, which -> askAdjustment(ids[which]) }
            .setNegativeButton(R.string.payouts_cancel, null)
            .show()
    }

    private fun askAdjustment(kind: String) {
        val box = LinearLayout(requireContext()).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(20), dp(4), dp(20), 0)
        }
        val amount = EditText(requireContext()).apply {
            hint = getString(R.string.payouts_amount)
            inputType = InputType.TYPE_CLASS_NUMBER or InputType.TYPE_NUMBER_FLAG_DECIMAL
        }
        val note = EditText(requireContext()).apply {
            hint = getString(R.string.payouts_note)
            inputType = InputType.TYPE_CLASS_TEXT
        }
        box.addView(amount)
        box.addView(note)
        MaterialAlertDialogBuilder(requireContext())
            .setTitle(R.string.payouts_adjust)
            .setView(box)
            .setPositiveButton(R.string.payouts_send) { _, _ ->
                val cents = ((amount.text.toString().replace(",", ".").toDoubleOrNull() ?: 0.0) * 100).toInt()
                if (cents > 0) {
                    lifecycleScope.launch {
                        AppGraph.repository.requestAdjustment(kind, cents, note.text.toString())
                            .onSuccess {
                                Toast.makeText(requireContext(), R.string.payouts_adjust_sent, Toast.LENGTH_SHORT).show()
                            }
                            .onFailure { error() }
                    }
                }
            }
            .setNegativeButton(R.string.payouts_cancel, null)
            .show()
    }

    private fun showInvoices() {
        lifecycleScope.launch {
            AppGraph.repository.invoices()
                .onSuccess { rows ->
                    val body = rows.joinToString("\n") {
                        "${it.month} · ${it.total} · IVA ${it.tax}"
                    }
                    MaterialAlertDialogBuilder(requireContext())
                        .setTitle(R.string.payouts_invoices)
                        .setMessage(body)
                        .setPositiveButton(android.R.string.ok, null)
                        .show()
                }
                .onFailure { error() }
        }
    }

    private fun showTax() {
        lifecycleScope.launch {
            val result: Result<TaxInfo> = AppGraph.repository.taxSummary()
            result.onSuccess { t: TaxInfo ->
                MaterialAlertDialogBuilder(requireContext())
                    .setTitle(getString(R.string.payouts_tax_year, t.year))
                    .setMessage(getString(R.string.payouts_tax_body, t.gross, t.net, t.tax) + "\n\n" + t.note)
                    .setPositiveButton(android.R.string.ok, null)
                    .show()
            }
            result.onFailure { error() }
        }
    }

    private fun text(value: String) = TextView(requireContext()).apply {
        text = value
        setTextColor(requireContext().getColor(R.color.qd_ink))
        textSize = 15f
        setPadding(0, dp(8), 0, dp(8))
    }

    private fun error() {
        binding.payoutsError.isVisible = true
        binding.payoutsError.setText(R.string.payouts_error)
    }

    private fun dp(value: Int) = (value * resources.displayMetrics.density).toInt()

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
