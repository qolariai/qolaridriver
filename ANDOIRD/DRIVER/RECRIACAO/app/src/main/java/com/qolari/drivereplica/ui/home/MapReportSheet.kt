package com.qolari.drivereplica.ui.home

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.fragment.app.activityViewModels
import com.google.android.material.bottomsheet.BottomSheetDialogFragment
import com.qolari.drivereplica.R
import com.qolari.drivereplica.databinding.SheetMapReportBinding
import com.qolari.drivereplica.state.PreferencesViewModel

/**
 * "Adicionar um relatório de mapa" (print 2026-10-30, 02:16).
 *
 * Aberto pelo botão A+ do mapa enquanto o motorista se dirige à recolha. Os relatórios ficam
 * guardados nas preferências e servem para avisar os próximos condutores do obstáculo — o
 * motorista não tem de voltar a escolher a cada viagem.
 */
class MapReportSheet : BottomSheetDialogFragment() {

    private val prefs: PreferencesViewModel by activityViewModels()
    private var binding: SheetMapReportBinding? = null

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        val b = SheetMapReportBinding.inflate(inflater, container, false)
        binding = b
        b.reportClose.setOnClickListener { dismiss() }
        b.reportHelp.setOnClickListener { dismiss() }
        // Cada sinal guarda a contribuição e fecha, como no original: escolher = reportar.
        mapOf(
            b.reportAccident to R.string.report_accident,
            b.reportTraffic to R.string.report_traffic,
            b.reportConstruction to R.string.report_construction,
            b.reportClosure to R.string.report_closure,
            b.reportSpeed to R.string.report_speed,
            b.reportWrongDirection to R.string.report_wrong_direction,
        ).forEach { (cell, label) ->
            cell.setOnClickListener {
                prefs.store.addMapReport(getString(label))
                Toast.makeText(requireContext(), R.string.report_sent, Toast.LENGTH_SHORT).show()
                dismiss()
            }
        }
        b.reportMine.setOnClickListener { dismiss() }
        return b.root
    }

    override fun onDestroyView() {
        binding = null
        super.onDestroyView()
    }

    companion object {
        fun show(fragment: androidx.fragment.app.Fragment) =
            MapReportSheet().show(fragment.childFragmentManager, "map_report")
    }
}
