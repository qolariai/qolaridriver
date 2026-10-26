package com.qolari.userlite.ui.account

import android.os.Bundle
import android.text.InputType
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.CheckBox
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.TextView
import androidx.core.view.isVisible
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import androidx.navigation.fragment.findNavController
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import com.qolari.userlite.R
import com.qolari.userlite.data.AppGraph
import com.qolari.userlite.databinding.FragmentAccountExtrasBinding
import com.qolari.userlite.net.AccountExtrasResponse
import com.qolari.userlite.net.FamilyMember
import kotlinx.coroutines.launch

/** Perfil empresarial, família/teens e Uber One. */
class AccountExtrasFragment : Fragment() {

    private var _binding: FragmentAccountExtrasBinding? = null
    private val binding get() = _binding!!
    private var current: AccountExtrasResponse? = null

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentAccountExtrasBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        binding.extrasBack.setOnClickListener { findNavController().navigateUp() }
        binding.businessConfigure.setOnClickListener { editBusiness() }
        binding.familyAdd.setOnClickListener { addFamily() }
        binding.uberOneAction.setOnClickListener { toggleUberOne() }
        load()
    }

    private fun load() {
        lifecycleScope.launch {
            AppGraph.repository.accountExtras()
                .onSuccess { render(it) }
                .onFailure { error() }
        }
    }

    private fun render(x: AccountExtrasResponse) {
        current = x
        binding.extrasError.isVisible = false
        binding.businessStatus.text = if (x.business.active) {
            getString(R.string.extras_business_on, x.business.companyName, x.business.vat)
        } else {
            getString(R.string.extras_business_off)
        }
        binding.familyCode.text = getString(R.string.extras_family_code, x.family.code)
        binding.familyList.removeAllViews()
        if (x.family.members.isEmpty()) {
            binding.familyList.addView(text(getString(R.string.extras_family_empty)))
        }
        x.family.members.forEach { m -> binding.familyList.addView(familyRow(m)) }
        binding.uberOneStatus.text = if (x.uberOne.active) {
            getString(R.string.extras_uber_one_on)
        } else {
            getString(R.string.extras_uber_one_off)
        }
        binding.uberOneAction.setText(if (x.uberOne.active) R.string.extras_uber_one_cancel else R.string.extras_uber_one_subscribe)
    }

    private fun familyRow(m: FamilyMember): View {
        val row = LinearLayout(requireContext()).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = android.view.Gravity.CENTER_VERTICAL
            setPadding(0, dp(8), 0, dp(8))
        }
        val info = LinearLayout(requireContext()).apply {
            orientation = LinearLayout.VERTICAL
            layoutParams = LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f)
        }
        info.addView(TextView(requireContext()).apply {
            text = if (m.teen) "${m.name} · Teen" else m.name
            setTextColor(requireContext().getColor(R.color.ql_black))
            textSize = 16f
        })
        info.addView(TextView(requireContext()).apply {
            text = m.phone
            setTextColor(requireContext().getColor(R.color.ql_gray_500))
            textSize = 14f
        })
        row.addView(info)
        row.addView(TextView(requireContext()).apply {
            setText(R.string.saved_remove)
            setTextColor(requireContext().getColor(R.color.ql_red))
            textSize = 14f
            setPadding(dp(10), dp(6), 0, dp(6))
            setOnClickListener { removeFamily(m.phone) }
        })
        return row
    }

    private fun editBusiness() {
        val box = LinearLayout(requireContext()).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(20), dp(4), dp(20), 0)
        }
        val company = EditText(requireContext()).apply {
            hint = getString(R.string.extras_company)
            inputType = InputType.TYPE_CLASS_TEXT
            setText(current?.business?.companyName.orEmpty())
        }
        val vat = EditText(requireContext()).apply {
            hint = getString(R.string.extras_vat)
            inputType = InputType.TYPE_CLASS_TEXT
            setText(current?.business?.vat.orEmpty())
        }
        val email = EditText(requireContext()).apply {
            hint = getString(R.string.extras_email)
            inputType = InputType.TYPE_TEXT_VARIATION_EMAIL_ADDRESS
            setText(current?.business?.email.orEmpty())
        }
        box.addView(company)
        box.addView(vat)
        box.addView(email)
        MaterialAlertDialogBuilder(requireContext())
            .setTitle(R.string.extras_business_edit)
            .setView(box)
            .setPositiveButton(R.string.saved_save) { _, _ ->
                lifecycleScope.launch {
                    AppGraph.repository.saveBusiness(company.text.toString(), vat.text.toString(), email.text.toString())
                        .onSuccess { render(it) }
                        .onFailure { error() }
                }
            }
            .setNegativeButton(R.string.safety_cancel, null)
            .show()
    }

    private fun addFamily() {
        val box = LinearLayout(requireContext()).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(20), dp(4), dp(20), 0)
        }
        val name = EditText(requireContext()).apply {
            hint = getString(R.string.extras_family_name)
            inputType = InputType.TYPE_CLASS_TEXT
        }
        val phone = EditText(requireContext()).apply {
            hint = getString(R.string.extras_family_phone)
            inputType = InputType.TYPE_CLASS_PHONE
        }
        val teen = CheckBox(requireContext()).apply { setText(R.string.extras_family_teen) }
        box.addView(name)
        box.addView(phone)
        box.addView(teen)
        MaterialAlertDialogBuilder(requireContext())
            .setTitle(R.string.extras_family_add)
            .setView(box)
            .setPositiveButton(R.string.saved_save) { _, _ ->
                lifecycleScope.launch {
                    AppGraph.repository.saveFamily(name.text.toString(), phone.text.toString(), teen.isChecked)
                        .onSuccess { render(it) }
                        .onFailure { error() }
                }
            }
            .setNegativeButton(R.string.safety_cancel, null)
            .show()
    }

    private fun removeFamily(phone: String) {
        lifecycleScope.launch {
            AppGraph.repository.saveFamily("", phone, false, "remove")
                .onSuccess { render(it) }
                .onFailure { error() }
        }
    }

    private fun toggleUberOne() {
        val active = current?.uberOne?.active == true
        lifecycleScope.launch {
            AppGraph.repository.uberOne(if (active) "cancel" else "subscribe")
                .onSuccess { render(it) }
                .onFailure { error() }
        }
    }

    private fun text(value: String) = TextView(requireContext()).apply {
        text = value
        setTextColor(requireContext().getColor(R.color.ql_gray_500))
        textSize = 14f
        setPadding(0, dp(4), 0, dp(4))
    }

    private fun error() {
        binding.extrasError.isVisible = true
        binding.extrasError.setText(R.string.extras_error)
    }

    private fun dp(value: Int) = (value * resources.displayMetrics.density).toInt()

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
