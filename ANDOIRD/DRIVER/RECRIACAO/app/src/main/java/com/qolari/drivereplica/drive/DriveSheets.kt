package com.qolari.drivereplica.drive

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.LinearLayout
import android.widget.TextView
import androidx.core.view.isVisible
import androidx.core.widget.doAfterTextChanged
import androidx.fragment.app.activityViewModels
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import com.google.android.material.bottomsheet.BottomSheetDialogFragment
import com.qolari.drivereplica.R
import com.qolari.drivereplica.databinding.SheetPinBinding
import com.qolari.drivereplica.databinding.SheetRatingBinding
import kotlinx.coroutines.launch

/**
 * Folha do PIN: o passageiro diz o PIN que vê na app e o motorista escreve-o (PinVerificationTaskData). Os textos e
 * o número de dígitos vêm do servidor; fecha-se sozinha quando o PIN fica verificado.
 */
class PinSheet : BottomSheetDialogFragment() {

    private val viewModel: DriveViewModel by activityViewModels { DriveViewModel.Factory }
    private var submitting = false

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        val b = SheetPinBinding.inflate(inflater, container, false)
        b.pinInput.doAfterTextChanged {
            val pin = viewModel.state.value.trip?.pin ?: return@doAfterTextChanged
            if (it?.length == pin.digits && !submitting) {
                submitting = true
                b.pinInput.clearFocus()
                viewModel.submitPin(it.toString())
            }
        }
        b.pinConfirm.setOnClickListener {
            val pin = viewModel.state.value.trip?.pin ?: return@setOnClickListener
            val typed = b.pinInput.text?.toString().orEmpty()
            if (typed.length == pin.digits && !submitting) {
                submitting = true
                viewModel.submitPin(typed)
            }
        }
        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                viewModel.state.collect { s ->
                    val pin = s.trip?.pin
                    if (pin != null) {
                        b.pinTitle.text = pin.title
                        b.pinSubtitle.text = pin.subtitle
                        b.pinInput.filters = arrayOf(android.text.InputFilter.LengthFilter(pin.digits))
                        b.pinConfirm.isEnabled = true
                    }
                    b.pinError.isVisible = s.pinError != null
                    b.pinError.text = s.pinError
                    if (s.pinError != null) {
                        // PIN errado: deixa voltar a escrever sem fechar a folha.
                        submitting = false
                        b.pinInput.text?.clear()
                    }
                    if (s.pinVerified) dismiss()
                }
            }
        }
        return b.root
    }
}

/** Fim da viagem: ganhos da viagem e avaliação do passageiro (1 a 5 estrelas, ou saltar). */
class RatingSheet : BottomSheetDialogFragment() {

    private val viewModel: DriveViewModel by activityViewModels { DriveViewModel.Factory }
    private var stars = 0

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        val b = SheetRatingBinding.inflate(inflater, container, false)
        isCancelable = false
        val summary = viewModel.state.value.summary
        b.ratingTotal.text = summary?.total.orEmpty()
        summary?.lines?.forEach { (label, value) ->
            b.ratingLines.addView(LinearLayout(requireContext()).apply {
                orientation = LinearLayout.HORIZONTAL
                addView(line(label, 1f))
                addView(line(value, 0f))
            })
        }
        val starViews = (1..5).map { n ->
            TextView(requireContext()).apply {
                text = "☆"; textSize = 40f
                setPadding(dp(6), 0, dp(6), 0)
                setTextColor(requireContext().getColor(R.color.qd_ink))
                setOnClickListener { stars = n; paint(b, n) }
            }
        }
        starViews.forEach { b.ratingStars.addView(it) }
        b.ratingSend.setOnClickListener { viewModel.rate(stars); dismissAllowingStateLoss() }
        b.ratingSkip.setOnClickListener { viewModel.skipRating(); dismissAllowingStateLoss() }
        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                viewModel.state.collect { s ->
                    // Se a avaliacao foi enviada/saltada (stage saiu de RATING), fecha mesmo que
                    // uma emissao antiga tenha voltado a mostrar a folha.
                    if (s.stage != DriveStage.RATING) dismissAllowingStateLoss()
                }
            }
        }
        return b.root
    }

    private fun paint(b: SheetRatingBinding, n: Int) {
        for (i in 0 until b.ratingStars.childCount) (b.ratingStars.getChildAt(i) as TextView).text = if (i < n) "★" else "☆"
        b.ratingSend.isEnabled = n > 0
    }

    private fun line(text: String, weight: Float) = TextView(requireContext()).apply {
        this.text = text
        textSize = 16f
        setTextColor(requireContext().getColor(R.color.qd_core_gray600))
        layoutParams = if (weight > 0f) LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, weight)
        else LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT)
    }

    private fun dp(v: Int) = (v * resources.displayMetrics.density).toInt()
}
