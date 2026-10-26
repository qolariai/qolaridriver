package com.qolari.drivereplica.ui.map

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.core.view.isVisible
import androidx.lifecycle.lifecycleScope
import com.google.android.material.bottomsheet.BottomSheetDialogFragment
import com.qolari.drivereplica.R
import com.qolari.drivereplica.data.AppGraph
import com.qolari.drivereplica.databinding.SheetMapReportBinding
import kotlinx.coroutines.launch

/** Comunica um problema de mapa; grava no backend (`/rt/support/map-report`). */
class MapReportSheet : BottomSheetDialogFragment() {

    private var _binding: SheetMapReportBinding? = null
    private val binding get() = _binding!!

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = SheetMapReportBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        binding.reportCancel.setOnClickListener { dismiss() }
        binding.reportSend.setOnClickListener { send() }
    }

    private fun send() {
        val checked = binding.reportReasons.checkedRadioButtonId
        if (checked == View.NO_ID) {
            showError(getString(R.string.map_report_reason_missing))
            return
        }
        val reason = when (checked) {
            R.id.reportReasonAddress -> "address"
            R.id.reportReasonClosed -> "closed"
            R.id.reportReasonOutdated -> "outdated"
            else -> "other"
        }
        val note = binding.reportNote.text?.toString().orEmpty()
        val fix = if (AppGraph.location.hasPermission) AppGraph.location.lastKnown() else null
        binding.reportSend.isEnabled = false
        binding.reportError.isVisible = false
        viewLifecycleOwner.lifecycleScope.launch {
            AppGraph.repository.mapReport(reason, note, fix?.first, fix?.second)
                .onSuccess {
                    Toast.makeText(requireContext(), R.string.map_report_sent, Toast.LENGTH_SHORT).show()
                    dismiss()
                }
                .onFailure {
                    showError(getString(R.string.map_report_error))
                    binding.reportSend.isEnabled = true
                }
        }
    }

    private fun showError(message: String) {
        binding.reportError.text = message
        binding.reportError.isVisible = true
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }

    companion object {
        fun show(manager: androidx.fragment.app.FragmentManager) {
            MapReportSheet().show(manager, "map_report")
        }
    }
}
