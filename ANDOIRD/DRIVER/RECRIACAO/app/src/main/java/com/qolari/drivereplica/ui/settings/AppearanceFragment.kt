package com.qolari.drivereplica.ui.settings

import android.content.Intent
import android.os.Bundle
import android.provider.Settings
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import androidx.navigation.fragment.findNavController
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import com.qolari.drivereplica.R
import com.qolari.drivereplica.databinding.FragmentAppearanceBinding
import com.qolari.drivereplica.state.UiPrefs

/** Idioma, modo escuro, modo simples e atalho de acessibilidade. */
class AppearanceFragment : Fragment() {

    private var _binding: FragmentAppearanceBinding? = null
    private val binding get() = _binding!!

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentAppearanceBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        val context = requireContext()
        binding.appearanceBack.setOnClickListener { findNavController().popBackStack() }
        binding.darkSwitch.isChecked = UiPrefs.dark(context)
        binding.simpleSwitch.isChecked = UiPrefs.simple(context)
        renderLanguage()
        binding.languageRow.setOnClickListener { chooseLanguage() }
        binding.darkSwitch.setOnCheckedChangeListener { _, value ->
            UiPrefs.setDark(context, value)
            requireActivity().recreate()
        }
        binding.simpleSwitch.setOnCheckedChangeListener { _, value ->
            UiPrefs.setSimple(context, value)
            requireActivity().recreate()
        }
        binding.accessibilityButton.setOnClickListener {
            startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))
        }
    }

    private fun renderLanguage() {
        binding.languageValue.text = if (UiPrefs.language(requireContext()) == UiPrefs.LANG_EN) {
            getString(R.string.appearance_language_en)
        } else {
            getString(R.string.appearance_language_pt)
        }
    }

    private fun chooseLanguage() {
        val ids = arrayOf(UiPrefs.LANG_PT, UiPrefs.LANG_EN)
        val labels = arrayOf(
            getString(R.string.appearance_language_pt),
            getString(R.string.appearance_language_en),
        )
        val current = ids.indexOf(UiPrefs.language(requireContext())).coerceAtLeast(0)
        MaterialAlertDialogBuilder(requireContext())
            .setTitle(R.string.appearance_language)
            .setSingleChoiceItems(labels, current) { dialog, which ->
                UiPrefs.setLanguage(requireContext(), ids[which])
                dialog.dismiss()
                requireActivity().recreate()
            }
            .setNegativeButton(R.string.safety_cancel, null)
            .show()
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
