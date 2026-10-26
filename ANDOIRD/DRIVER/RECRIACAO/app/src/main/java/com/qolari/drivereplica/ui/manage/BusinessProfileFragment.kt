package com.qolari.drivereplica.ui.manage

import android.os.Bundle
import android.text.InputType
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.TextView
import androidx.core.view.isVisible
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import androidx.navigation.fragment.findNavController
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import com.google.gson.JsonObject
import com.qolari.drivereplica.R
import com.qolari.drivereplica.data.AppGraph
import com.qolari.drivereplica.databinding.FragmentBusinessProfileBinding
import com.qolari.drivereplica.net.DriverBusiness
import com.qolari.drivereplica.net.DriverDelegate
import kotlinx.coroutines.launch

/** Perfil empresarial e delegados do motorista. */
class BusinessProfileFragment : Fragment() {

    private var _binding: FragmentBusinessProfileBinding? = null
    private val binding get() = _binding!!
    private var current: DriverBusiness? = null

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentBusinessProfileBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        binding.businessBack.setOnClickListener { findNavController().popBackStack() }
        binding.businessEdit.setOnClickListener { edit() }
        binding.businessAddDelegate.setOnClickListener { addDelegate() }
        load()
    }

    private fun load() {
        lifecycleScope.launch {
            AppGraph.repository.businessProfile()
                .onSuccess { render(it) }
                .onFailure { error() }
        }
    }

    private fun render(b: DriverBusiness) {
        current = b
        binding.businessError.isVisible = false
        binding.businessStatus.text = if (b.active) {
            getString(R.string.business_on, b.companyName, b.vat)
        } else {
            getString(R.string.business_off)
        }
        binding.businessDelegates.removeAllViews()
        if (b.delegates.isEmpty()) {
            binding.businessDelegates.addView(text(getString(R.string.business_no_delegates)))
        }
        b.delegates.forEach { d -> binding.businessDelegates.addView(delegateRow(d)) }
    }

    private fun delegateRow(d: DriverDelegate): View {
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
            text = d.name
            setTextColor(requireContext().getColor(R.color.qd_ink))
            textSize = 16f
        })
        info.addView(TextView(requireContext()).apply {
            text = d.phone
            setTextColor(requireContext().getColor(R.color.qd_core_gray600))
            textSize = 14f
        })
        row.addView(info)
        row.addView(TextView(requireContext()).apply {
            setText(R.string.business_remove)
            setTextColor(requireContext().getColor(R.color.qd_core_red600))
            textSize = 14f
            setPadding(dp(10), dp(6), 0, dp(6))
            setOnClickListener { removeDelegate(d.phone) }
        })
        return row
    }

    private fun edit() {
        val box = LinearLayout(requireContext()).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(20), dp(4), dp(20), 0)
        }
        val company = EditText(requireContext()).apply {
            hint = getString(R.string.business_company)
            inputType = InputType.TYPE_CLASS_TEXT
            setText(current?.companyName.orEmpty())
        }
        val vat = EditText(requireContext()).apply {
            hint = getString(R.string.business_vat)
            inputType = InputType.TYPE_CLASS_TEXT
            setText(current?.vat.orEmpty())
        }
        val email = EditText(requireContext()).apply {
            hint = getString(R.string.business_email)
            inputType = InputType.TYPE_TEXT_VARIATION_EMAIL_ADDRESS
            setText(current?.email.orEmpty())
        }
        box.addView(company)
        box.addView(vat)
        box.addView(email)
        MaterialAlertDialogBuilder(requireContext())
            .setTitle(R.string.business_edit)
            .setView(box)
            .setPositiveButton(R.string.business_save) { _, _ ->
                val body = JsonObject().apply {
                    addProperty("action", "save")
                    addProperty("active", true)
                    addProperty("companyName", company.text.toString())
                    addProperty("vat", vat.text.toString())
                    addProperty("email", email.text.toString())
                }
                save(body)
            }
            .setNegativeButton(R.string.safety_cancel, null)
            .show()
    }

    private fun addDelegate() {
        val box = LinearLayout(requireContext()).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(20), dp(4), dp(20), 0)
        }
        val name = EditText(requireContext()).apply {
            hint = getString(R.string.business_delegate_name)
            inputType = InputType.TYPE_CLASS_TEXT
        }
        val phone = EditText(requireContext()).apply {
            hint = getString(R.string.business_delegate_phone)
            inputType = InputType.TYPE_CLASS_PHONE
        }
        box.addView(name)
        box.addView(phone)
        MaterialAlertDialogBuilder(requireContext())
            .setTitle(R.string.business_add_delegate)
            .setView(box)
            .setPositiveButton(R.string.business_save) { _, _ ->
                val body = JsonObject().apply {
                    addProperty("action", "add_delegate")
                    addProperty("delegateName", name.text.toString())
                    addProperty("delegatePhone", phone.text.toString())
                }
                save(body)
            }
            .setNegativeButton(R.string.safety_cancel, null)
            .show()
    }

    private fun removeDelegate(phone: String) {
        save(JsonObject().apply {
            addProperty("action", "remove_delegate")
            addProperty("delegatePhone", phone)
        })
    }

    private fun save(body: JsonObject) {
        lifecycleScope.launch {
            AppGraph.repository.saveBusinessProfile(body)
                .onSuccess { render(it) }
                .onFailure { error() }
        }
    }

    private fun text(value: String) = TextView(requireContext()).apply {
        text = value
        setTextColor(requireContext().getColor(R.color.qd_core_gray600))
        textSize = 14f
        setPadding(0, dp(4), 0, dp(4))
    }

    private fun error() {
        binding.businessError.isVisible = true
        binding.businessError.setText(R.string.business_error)
    }

    private fun dp(value: Int) = (value * resources.displayMetrics.density).toInt()

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
