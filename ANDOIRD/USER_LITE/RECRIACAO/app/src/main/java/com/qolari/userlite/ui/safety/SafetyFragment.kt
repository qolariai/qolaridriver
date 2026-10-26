package com.qolari.userlite.ui.safety

import android.content.Intent
import android.net.Uri
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
import com.qolari.userlite.R
import com.qolari.userlite.data.AppGraph
import com.qolari.userlite.databinding.FragmentSafetyBinding
import com.qolari.userlite.net.SafetyContact
import kotlinx.coroutines.launch

/** Segurança: contactos de confiança, SOS e partilha da viagem ativa. */
class SafetyFragment : Fragment() {

    private var _binding: FragmentSafetyBinding? = null
    private val binding get() = _binding!!

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentSafetyBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        binding.safetyBack.setOnClickListener { findNavController().navigateUp() }
        binding.safetyAdd.setOnClickListener { addContact() }
        binding.safetySos.setOnClickListener { sos() }
        binding.safetyCall.setOnClickListener {
            startActivity(Intent(Intent.ACTION_DIAL, Uri.parse("tel:112")))
        }
        binding.safetyShare.setOnClickListener { shareTrip() }
        loadContacts()
    }

    private fun loadContacts() {
        lifecycleScope.launch {
            AppGraph.repository.safetyContacts()
                .onSuccess { render(it) }
                .onFailure { status(getString(R.string.safety_error)) }
        }
    }

    private fun render(contacts: List<SafetyContact>) {
        binding.safetyContacts.removeAllViews()
        if (contacts.isEmpty()) {
            binding.safetyContacts.addView(TextView(requireContext()).apply {
                setText(R.string.safety_contacts_empty)
                setTextColor(requireContext().getColor(R.color.ql_gray_500))
                textSize = 14f
                setPadding(0, dp(6), 0, dp(6))
            })
            return
        }
        contacts.forEach { c ->
            val row = LinearLayout(requireContext()).apply {
                orientation = LinearLayout.HORIZONTAL
                gravity = android.view.Gravity.CENTER_VERTICAL
                setPadding(0, dp(10), 0, dp(10))
            }
            val info = LinearLayout(requireContext()).apply {
                orientation = LinearLayout.VERTICAL
                layoutParams = LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f)
            }
            info.addView(TextView(requireContext()).apply {
                text = c.name
                setTextColor(requireContext().getColor(R.color.ql_black))
                textSize = 16f
            })
            info.addView(TextView(requireContext()).apply {
                text = c.phone
                setTextColor(requireContext().getColor(R.color.ql_gray_500))
                textSize = 14f
            })
            row.addView(info)
            row.addView(TextView(requireContext()).apply {
                setText(R.string.safety_remove)
                setTextColor(requireContext().getColor(R.color.ql_red))
                textSize = 14f
                setPadding(dp(10), dp(6), 0, dp(6))
                setOnClickListener { removeContact(c.uuid) }
            })
            binding.safetyContacts.addView(row)
        }
    }

    private fun addContact() {
        val box = LinearLayout(requireContext()).apply {
            orientation = LinearLayout.VERTICAL
            val pad = dp(20)
            setPadding(pad, dp(4), pad, 0)
        }
        val name = EditText(requireContext()).apply {
            hint = getString(R.string.safety_contact_name)
            inputType = InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_FLAG_CAP_WORDS
        }
        val phone = EditText(requireContext()).apply {
            hint = getString(R.string.safety_contact_phone)
            inputType = InputType.TYPE_CLASS_PHONE
        }
        box.addView(name)
        box.addView(phone)
        MaterialAlertDialogBuilder(requireContext())
            .setTitle(R.string.safety_add_contact)
            .setView(box)
            .setPositiveButton(R.string.safety_add) { _, _ ->
                val n = name.text.toString().trim()
                val p = phone.text.toString().trim()
                if (n.isEmpty() || p.length < 6) return@setPositiveButton
                lifecycleScope.launch {
                    AppGraph.repository.addSafetyContact(n, p)
                        .onSuccess { loadContacts() }
                        .onFailure { status(getString(R.string.safety_error)) }
                }
            }
            .setNegativeButton(R.string.safety_cancel, null)
            .show()
    }

    private fun removeContact(uuid: String) {
        lifecycleScope.launch {
            AppGraph.repository.deleteSafetyContact(uuid)
                .onSuccess { loadContacts() }
                .onFailure { status(getString(R.string.safety_error)) }
        }
    }

    private fun sos() {
        lifecycleScope.launch {
            val trip = AppGraph.repository.active().getOrNull()
            AppGraph.repository.safetySos(trip?.uuid, trip?.pickup?.lat, trip?.pickup?.lng)
                .onSuccess {
                    MaterialAlertDialogBuilder(requireContext())
                        .setTitle(R.string.safety_sos)
                        .setMessage(R.string.safety_sos_ok)
                        .setPositiveButton(R.string.safety_call_112) { _, _ ->
                            startActivity(Intent(Intent.ACTION_DIAL, Uri.parse("tel:112")))
                        }
                        .setNegativeButton(R.string.safety_close, null)
                        .show()
                }
                .onFailure { status(getString(R.string.safety_error)) }
        }
    }

    private fun shareTrip() {
        lifecycleScope.launch {
            val trip = AppGraph.repository.active().getOrNull()
            if (trip == null) {
                status(getString(R.string.safety_share_no_trip))
                return@launch
            }
            AppGraph.repository.shareTrip(trip.uuid)
                .onSuccess { s ->
                    val intent = Intent(Intent.ACTION_SEND).apply {
                        type = "text/plain"
                        putExtra(Intent.EXTRA_TEXT, getString(R.string.safety_share_text, s.url))
                    }
                    startActivity(Intent.createChooser(intent, getString(R.string.safety_share)))
                }
                .onFailure { status(getString(R.string.safety_error)) }
        }
    }

    private fun status(text: String) {
        binding.safetyStatus.isVisible = true
        binding.safetyStatus.text = text
    }

    private fun dp(value: Int) = (value * resources.displayMetrics.density).toInt()

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
