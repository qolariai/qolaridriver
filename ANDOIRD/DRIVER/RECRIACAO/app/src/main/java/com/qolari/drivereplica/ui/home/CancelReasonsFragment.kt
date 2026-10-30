package com.qolari.drivereplica.ui.home

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.core.view.isVisible
import androidx.fragment.app.Fragment
import androidx.fragment.app.activityViewModels
import com.qolari.drivereplica.R
import com.qolari.drivereplica.databinding.FragmentCancelReasonsBinding
import com.qolari.drivereplica.databinding.ItemCancelReasonBinding
import com.qolari.drivereplica.drive.DriveViewModel

/**
 * Motivos de cancelamento na recolha (print do vídeo de 2026-10-30 17:30).
 * Abre pelo ícone de pessoa do ecrã de espera, não é o telefone.
 *
 * Cada linha tem ícone + motivo; ao escolher, o botão "Continuar" fica ativo e o cancelamento
 * é feito com a razão escolhida (o passageiro vê o motivo na app dele).
 */
class CancelReasonsFragment : Fragment(R.layout.fragment_cancel_reasons) {

    private val drive: DriveViewModel by activityViewModels { DriveViewModel.Factory }
    private var binding: FragmentCancelReasonsBinding? = null
    private var selected: String? = null

    /** Motivos na ordem do print, com o ícone próprio. */
    private val reasons = listOf(
        R.string.cancel_reason_not_found to R.drawable.ic_reason_not_found,
        R.string.cancel_reason_no_stop to R.drawable.ic_reason_no_stop,
        R.string.cancel_reason_luggage to R.drawable.ic_reason_luggage,
        R.string.cancel_reason_too_many to R.drawable.ic_reason_people,
        R.string.cancel_reason_minor to R.drawable.ic_reason_two_people,
        R.string.cancel_reason_child_seat to R.drawable.ic_reason_child_seat,
        R.string.cancel_reason_pet to R.drawable.ic_reason_pet,
        R.string.cancel_reason_behavior to R.drawable.ic_reason_behavior,
    )

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        val b = FragmentCancelReasonsBinding.inflate(inflater, container, false)
        binding = b
        b.cancelBack.setOnClickListener { parentFragmentManager.popBackStack() }
        // "Confirmar cancelamento": cancela a viagem com o motivo e volta ao mapa (a viagem acaba).
        b.cancelConfirm.setOnClickListener {
            val reason = selected ?: return@setOnClickListener
            drive.cancelForReason(reason)
            parentFragmentManager.popBackStack()
        }
        // "Cancelar": sai sem cancelar nada (o motorista volta ao ecrã de espera).
        b.cancelBack2.setOnClickListener { parentFragmentManager.popBackStack() }
        bindReasons(b)
        return b.root
    }

    private fun bindReasons(b: FragmentCancelReasonsBinding) {
        val container = b.cancelReasons
        container.removeAllViews()
        reasons.forEachIndexed { index, (textRes, iconRes) ->
            val row = ItemCancelReasonBinding.inflate(layoutInflater, container, false)
            row.reasonText.setText(textRes)
            row.reasonIcon.setImageResource(iconRes)
            row.reasonDivider.isVisible = index < reasons.lastIndex
            val label = getString(textRes)
            row.root.setOnClickListener { select(b, label, row) }
            container.addView(row.root)
        }
    }

    /** Marca o motivo: fundo cinza e botão "Continuar" ativo. */
    private fun select(b: FragmentCancelReasonsBinding, label: String, row: ItemCancelReasonBinding) {
        selected = label
        for (i in 0 until b.cancelReasons.childCount) {
            b.cancelReasons.getChildAt(i).setBackgroundColor(
                requireContext().getColor(android.R.color.transparent),
            )
        }
        row.root.setBackgroundColor(requireContext().getColor(R.color.qd_surface_variant))
        b.cancelConfirm.isVisible = true
    }

    override fun onDestroyView() {
        binding = null
        super.onDestroyView()
    }
}
