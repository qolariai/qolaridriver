package com.qolari.drivereplica.ui.home

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.core.view.isVisible
import androidx.fragment.app.Fragment
import androidx.fragment.app.activityViewModels
import androidx.navigation.fragment.findNavController
import com.qolari.drivereplica.R
import com.qolari.drivereplica.databinding.FragmentPlannerCancelBinding
import com.qolari.drivereplica.databinding.ItemPlannerReasonBinding
import com.qolari.drivereplica.drive.DriveViewModel
import java.util.Locale

/**
 * Cancelamento a partir do planeador (print 2026-10-30, 01:59).
 *
 * Diferente da lista da espera: aqui o motorista desiste da viagem já aceite, com o
 * cabeçalho do passageiro (nome, avaliação, produto) e a morada da recolha. Os motivos
 * são os do print — engano, rota, não compensa, não é segura...
 */
class PlannerCancelFragment : Fragment(R.layout.fragment_planner_cancel) {

    private val drive: DriveViewModel by activityViewModels { DriveViewModel.Factory }
    private var binding: FragmentPlannerCancelBinding? = null
    private var selected: String? = null

    /** Motivos na ordem do print (01:59). */
    private val reasons = listOf(
        R.string.cancel_reason_accepted_mistake to R.drawable.ic_reason_x,
        R.string.cancel_reason_pickup_route to R.drawable.ic_reason_x,
        R.string.cancel_reason_lost_way to R.drawable.ic_reason_x,
        R.string.cancel_reason_not_worth to R.drawable.ic_reason_x,
        R.string.cancel_reason_not_safe to R.drawable.ic_reason_x,
        R.string.cancel_reason_vehicle to R.drawable.ic_reason_x,
        R.string.cancel_reason_no_recording to R.drawable.ic_mic_off,
        R.string.cancel_reason_more to R.drawable.ic_overflow,
    )

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        val b = FragmentPlannerCancelBinding.inflate(inflater, container, false)
        binding = b
        b.plannerCancelBack.setOnClickListener { findNavController().popBackStack() }
        b.plannerCancelChat.setOnClickListener { findNavController().navigate(R.id.chatFragment) }
        b.plannerCancelConfirm.setOnClickListener {
            val reason = selected ?: return@setOnClickListener
            drive.cancelForReason(reason)
            // Sai do planeador e do cancelamento: a viagem acabou.
            findNavController().popBackStack(R.id.mapFragment, false)
        }
        val trip = drive.state.value.trip
        b.plannerCancelName.text = trip?.riderName.orEmpty()
        val rating = trip?.riderRating?.let {
            "%.2f".format(Locale("pt", "PT"), it)
        }
        b.plannerCancelMeta.text = listOfNotNull(
            rating?.let { "$it ★" },
            trip?.product?.takeIf { it.isNotBlank() },
        ).joinToString(" · ")
        b.plannerCancelAddress.text = listOfNotNull(
            trip?.pickupAddress?.takeIf { it.isNotBlank() } ?: trip?.address,
            trip?.city?.takeIf { it.isNotBlank() },
        ).joinToString("\n")
        bindReasons(b)
        return b.root
    }

    private fun bindReasons(b: FragmentPlannerCancelBinding) {
        val container = b.plannerCancelRows
        container.removeAllViews()
        reasons.forEach { (textRes, iconRes) ->
            val row = ItemPlannerReasonBinding.inflate(layoutInflater, container, false)
            row.plannerReasonText.setText(textRes)
            row.plannerReasonIcon.setImageResource(iconRes)
            row.root.setOnClickListener { select(b, row, getString(textRes)) }
            container.addView(row.root)
        }
    }

    private fun select(b: FragmentPlannerCancelBinding, row: ItemPlannerReasonBinding, label: String) {
        selected = label
        for (i in 0 until b.plannerCancelRows.childCount) {
            b.plannerCancelRows.getChildAt(i).setBackgroundColor(
                requireContext().getColor(android.R.color.transparent),
            )
        }
        row.root.setBackgroundColor(requireContext().getColor(R.color.qd_surface_variant))
        b.plannerCancelConfirm.isVisible = true
    }

    override fun onDestroyView() {
        binding = null
        super.onDestroyView()
    }
}
