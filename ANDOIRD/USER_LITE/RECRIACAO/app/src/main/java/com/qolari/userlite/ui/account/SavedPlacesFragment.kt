package com.qolari.userlite.ui.account

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
import com.qolari.userlite.databinding.FragmentSavedPlacesBinding
import com.qolari.userlite.net.Place
import kotlinx.coroutines.launch

/** Locais guardados: listar, adicionar por morada e remover. */
class SavedPlacesFragment : Fragment() {

    private var _binding: FragmentSavedPlacesBinding? = null
    private val binding get() = _binding!!

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentSavedPlacesBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        binding.savedBack.setOnClickListener { findNavController().navigateUp() }
        binding.savedAdd.setOnClickListener { add() }
        load()
    }

    private fun load() {
        lifecycleScope.launch {
            AppGraph.repository.savedPlaces()
                .onSuccess { render(it) }
                .onFailure { error() }
        }
    }

    private fun render(places: List<Place>) {
        binding.savedError.isVisible = false
        binding.savedList.removeAllViews()
        if (places.isEmpty()) {
            binding.savedList.addView(TextView(requireContext()).apply {
                setText(R.string.saved_empty)
                setTextColor(requireContext().getColor(R.color.ql_gray_500))
                textSize = 14f
                setPadding(0, dp(6), 0, dp(6))
            })
            return
        }
        places.forEach { p ->
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
                text = p.name
                setTextColor(requireContext().getColor(R.color.ql_black))
                textSize = 16f
            })
            info.addView(TextView(requireContext()).apply {
                text = p.address
                setTextColor(requireContext().getColor(R.color.ql_gray_500))
                textSize = 14f
            })
            row.addView(info)
            row.addView(TextView(requireContext()).apply {
                setText(R.string.saved_remove)
                setTextColor(requireContext().getColor(R.color.ql_red))
                textSize = 14f
                setPadding(dp(10), dp(6), 0, dp(6))
                setOnClickListener { remove(p.id) }
            })
            binding.savedList.addView(row)
        }
    }

    private fun add() {
        val box = LinearLayout(requireContext()).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(20), dp(4), dp(20), 0)
        }
        val label = EditText(requireContext()).apply {
            hint = getString(R.string.saved_label)
            inputType = InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_FLAG_CAP_WORDS
        }
        val address = EditText(requireContext()).apply {
            hint = getString(R.string.saved_address)
            inputType = InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_FLAG_CAP_WORDS
        }
        box.addView(label)
        box.addView(address)
        MaterialAlertDialogBuilder(requireContext())
            .setTitle(R.string.saved_add)
            .setView(box)
            .setPositiveButton(R.string.saved_save) { _, _ ->
                val name = label.text.toString().trim()
                val addr = address.text.toString().trim()
                if (name.isNotEmpty() && addr.isNotEmpty()) {
                    lifecycleScope.launch {
                        AppGraph.repository.savePlace(name, addr)
                            .onSuccess { load() }
                            .onFailure { error() }
                    }
                }
            }
            .setNegativeButton(R.string.safety_cancel, null)
            .show()
    }

    private fun remove(id: String) {
        lifecycleScope.launch {
            AppGraph.repository.deleteSavedPlace(id)
                .onSuccess { load() }
                .onFailure { error() }
        }
    }

    private fun error() {
        binding.savedError.isVisible = true
        binding.savedError.setText(R.string.saved_error)
    }

    private fun dp(value: Int) = (value * resources.displayMetrics.density).toInt()

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
