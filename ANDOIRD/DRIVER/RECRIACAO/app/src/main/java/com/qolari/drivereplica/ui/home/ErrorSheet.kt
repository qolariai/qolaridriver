package com.qolari.drivereplica.ui.home

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.core.os.bundleOf
import androidx.fragment.app.FragmentManager
import androidx.lifecycle.LifecycleOwner
import com.google.android.material.bottomsheet.BottomSheetDialogFragment
import com.qolari.drivereplica.databinding.SheetErrorBinding

/** Janela "Erro" em folha inferior com "Tentar novamente" e "Cancelar" (capturas 115b e 125b). */
class ErrorSheet : BottomSheetDialogFragment() {

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        val b = SheetErrorBinding.inflate(inflater, container, false)
        b.errorRetry.setOnClickListener {
            parentFragmentManager.setFragmentResult(RESULT, bundleOf())
            dismiss()
        }
        b.errorCancel.setOnClickListener { dismiss() }
        return b.root
    }

    companion object {
        private const val RESULT = "error_sheet_retry"
        private const val TAG = "error_sheet"

        /** Abre a janela (uma de cada vez) e chama [onRetry] se o utilizador escolher "Tentar novamente". */
        fun show(fm: FragmentManager, owner: LifecycleOwner, onRetry: () -> Unit) {
            if (fm.findFragmentByTag(TAG) != null) return
            fm.setFragmentResultListener(RESULT, owner) { _, _ -> onRetry() }
            ErrorSheet().show(fm, TAG)
        }
    }
}
