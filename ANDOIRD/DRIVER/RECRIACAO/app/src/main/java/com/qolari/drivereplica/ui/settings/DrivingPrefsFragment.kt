package com.qolari.drivereplica.ui.settings

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.core.view.isVisible
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import androidx.navigation.fragment.findNavController
import com.google.gson.JsonObject
import com.qolari.drivereplica.R
import com.qolari.drivereplica.data.AppGraph
import com.qolari.drivereplica.databinding.FragmentDrivingPrefsBinding
import com.qolari.drivereplica.net.DriverPreferences
import kotlinx.coroutines.launch
import java.text.DateFormat
import java.util.Date

/** Modo destino, área, aceitação automática e pausa (P1 da análise de funcionalidades). */
class DrivingPrefsFragment : Fragment() {

    private var _binding: FragmentDrivingPrefsBinding? = null
    private val binding get() = _binding!!
    private var loaded: DriverPreferences? = null

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentDrivingPrefsBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        binding.prefsBack.setOnClickListener { findNavController().popBackStack() }
        binding.prefSave.setOnClickListener { save() }
        binding.prefBreak15.setOnClickListener { setBreak(15) }
        binding.prefBreak30.setOnClickListener { setBreak(30) }
        binding.prefResume.setOnClickListener { setBreak(0, resume = true) }
        load()
    }

    private fun load() {
        lifecycleScope.launch {
            AppGraph.repository.preferences()
                .onSuccess { bind(it) }
                .onFailure { error() }
        }
    }

    private fun bind(p: DriverPreferences) {
        loaded = p
        binding.prefDestination.isChecked = p.destinationMode
        binding.prefDestinationAddress.setText(p.destinationAddress)
        binding.prefArea.isChecked = p.areaMode
        binding.prefAreaLabel.setText(p.areaLabel)
        binding.prefAreaRadius.setText(p.areaRadiusKm.toString())
        binding.prefAuto.isChecked = p.autoAccept
        renderBreak(p)
    }

    private fun renderBreak(p: DriverPreferences) {
        binding.prefBreakStatus.text = if (p.breakActive && p.breakUntil != null) {
            val time = DateFormat.getTimeInstance(DateFormat.SHORT).format(Date(p.breakUntil * 1000))
            getString(R.string.prefs_break_active, time)
        } else {
            getString(R.string.prefs_break_inactive)
        }
    }

    private fun save() {
        val destMode = binding.prefDestination.isChecked
        val destText = binding.prefDestinationAddress.text.toString().trim()
        val areaMode = binding.prefArea.isChecked
        val areaText = binding.prefAreaLabel.text.toString().trim()
        if (destMode && destText.isEmpty()) {
            error(getString(R.string.prefs_error_address))
            return
        }
        if (areaMode && areaText.isEmpty()) {
            error(getString(R.string.prefs_error_address))
            return
        }
        binding.prefSave.isEnabled = false
        lifecycleScope.launch {
            val current = loaded
            var destLat = current?.destinationLat
            var destLng = current?.destinationLng
            if (destMode && (destText != current?.destinationAddress || destLat == null)) {
                val places = AppGraph.repository.searchPlaces(destText, null, null).getOrNull().orEmpty()
                if (places.isEmpty()) {
                    error(getString(R.string.prefs_error_address))
                    binding.prefSave.isEnabled = true
                    return@launch
                }
                destLat = places.first().lat
                destLng = places.first().lng
            }
            var areaLat = current?.areaLat
            var areaLng = current?.areaLng
            if (areaMode && (areaText != current?.areaLabel || areaLat == null)) {
                val places = AppGraph.repository.searchPlaces(areaText, null, null).getOrNull().orEmpty()
                if (places.isEmpty()) {
                    error(getString(R.string.prefs_error_address))
                    binding.prefSave.isEnabled = true
                    return@launch
                }
                areaLat = places.first().lat
                areaLng = places.first().lng
            }
            val body = JsonObject().apply {
                addProperty("destinationMode", destMode)
                addProperty("destinationAddress", destText)
                destLat?.let { addProperty("destinationLat", it) }
                destLng?.let { addProperty("destinationLng", it) }
                addProperty("areaMode", areaMode)
                addProperty("areaLabel", areaText)
                areaLat?.let { addProperty("areaLat", it) }
                areaLng?.let { addProperty("areaLng", it) }
                addProperty("areaRadiusKm", binding.prefAreaRadius.text.toString().toDoubleOrNull() ?: 5.0)
                addProperty("autoAccept", binding.prefAuto.isChecked)
            }
            AppGraph.repository.savePreferences(body)
                .onSuccess {
                    bind(it)
                    binding.prefError.isVisible = false
                    android.widget.Toast.makeText(requireContext(), R.string.prefs_saved, android.widget.Toast.LENGTH_SHORT).show()
                }
                .onFailure { error() }
            binding.prefSave.isEnabled = true
        }
    }

    private fun setBreak(minutes: Int, resume: Boolean = false) {
        lifecycleScope.launch {
            AppGraph.repository.setBreak(minutes, resume)
                .onSuccess {
                    bind(it)
                    android.widget.Toast.makeText(requireContext(), R.string.prefs_break_set, android.widget.Toast.LENGTH_SHORT).show()
                }
                .onFailure { error() }
        }
    }

    private fun error(message: String? = null) {
        binding.prefError.isVisible = true
        binding.prefError.text = message ?: getString(R.string.prefs_error)
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
