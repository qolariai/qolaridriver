package com.qolari.drivereplica.ui.settings

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.text.SpannableString
import android.text.Spanned
import android.text.method.LinkMovementMethod
import android.text.style.ClickableSpan
import android.text.style.ForegroundColorSpan
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.annotation.DrawableRes
import androidx.annotation.StringRes
import androidx.core.content.ContextCompat
import androidx.fragment.app.Fragment
import androidx.fragment.app.activityViewModels
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import androidx.navigation.fragment.findNavController
import com.google.android.material.bottomsheet.BottomSheetDialog
import com.qolari.drivereplica.R
import com.qolari.drivereplica.databinding.FragmentCommunicationBinding
import com.qolari.drivereplica.databinding.ItemChoiceRowBinding
import com.qolari.drivereplica.databinding.SheetPushBinding
import com.qolari.drivereplica.state.ContactPreference
import com.qolari.drivereplica.state.PreferencesViewModel
import kotlinx.coroutines.launch

/**
 * Comunicação (Views; captura 045). "Guardar alterações" só fica ativo quando a escolha de contacto difere da guardada.
 * "Notificações push" abre a janela da captura 051 (sem escolher nada fecha-se sem efeito).
 */
class CommunicationFragment : Fragment() {

    private val prefs: PreferencesViewModel by activityViewModels()
    private var _binding: FragmentCommunicationBinding? = null
    private val binding get() = _binding!!
    private val optionViews = mutableMapOf<ContactPreference, ItemChoiceRowBinding>()

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentCommunicationBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        val inflater = LayoutInflater.from(requireContext())
        binding.commBack.setOnClickListener { findNavController().popBackStack() }

        val options = listOf(
            Triple(ContactPreference.CALL_OR_CHAT, R.drawable.ic_phone, R.string.comm_call_or_chat),
            Triple(ContactPreference.CALL, R.drawable.ic_phone, R.string.comm_call),
            Triple(ContactPreference.CHAT, R.drawable.ic_mail, R.string.comm_chat),
        )
        options.forEachIndexed { index, (pref, icon, title) ->
            val row = ItemChoiceRowBinding.inflate(inflater, binding.contactOptions, false)
            row.choiceIcon.visibility = View.VISIBLE
            row.choiceIcon.setImageResource(icon)
            row.choiceTitle.setText(title)
            row.choiceRadio.visibility = View.VISIBLE
            if (pref == ContactPreference.CALL_OR_CHAT) {
                row.choiceTag.setText(R.string.comm_recommended)
                row.choiceTag.visibility = View.VISIBLE
            }
            row.choiceDivider.visibility = if (index == options.lastIndex) View.GONE else View.VISIBLE
            (row.choiceDivider.layoutParams as ViewGroup.MarginLayoutParams).marginStart = dp(64)
            row.choiceContent.setOnClickListener { prefs.store.selectContact(pref) }
            binding.contactOptions.addView(row.root)
            optionViews[pref] = row
        }

        listOf(R.string.comm_push, R.string.comm_email).forEachIndexed { index, title ->
            val row = ItemChoiceRowBinding.inflate(inflater, binding.marketingRows, false)
            row.choiceTitle.setText(title)
            row.choiceCheck.setImageResource(R.drawable.ic_chevron)
            row.choiceCheck.setColorFilter(ContextCompat.getColor(requireContext(), R.color.qd_chevron))
            row.choiceCheck.visibility = View.VISIBLE
            row.choiceDivider.visibility = if (index == 1) View.GONE else View.VISIBLE
            if (title == R.string.comm_push) row.choiceContent.setOnClickListener { showPushSheet() }
            binding.marketingRows.addView(row.root)
        }

        binding.commLegal.text = legalText()
        binding.commLegal.movementMethod = LinkMovementMethod.getInstance()
        binding.commSave.setOnClickListener { prefs.store.saveContact() }

        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                prefs.store.communication.collect { draft ->
                    optionViews.forEach { (pref, row) -> row.choiceRadio.isChecked = pref == draft.selected }
                    binding.commSave.isEnabled = draft.canSave
                }
            }
        }
    }

    private fun legalText(): CharSequence {
        val base = getString(R.string.comm_legal) + " "
        val link = getString(R.string.comm_learn_more)
        val s = SpannableString(base + link)
        val blue = ContextCompat.getColor(requireContext(), R.color.qd_core_blue600)
        s.setSpan(ForegroundColorSpan(blue), base.length, s.length, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE)
        s.setSpan(object : ClickableSpan() {
            // Política de dados: página da original (D7). Fica um endereço próprio a definir; sem rede aqui.
            override fun onClick(widget: View) { /* sem destino neste lote */ }
        }, base.length, s.length, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE)
        return s
    }

    private fun showPushSheet() {
        val dialog = BottomSheetDialog(requireContext())
        val sheet = SheetPushBinding.inflate(layoutInflater)
        // "Atualizar definições" abriria as definições do Android: não é feito automaticamente nem aqui.
        sheet.pushUpdate.setOnClickListener { dialog.dismiss() }
        sheet.pushCancel.setOnClickListener { dialog.dismiss() }
        dialog.setContentView(sheet.root)
        dialog.show()
    }

    private fun dp(v: Int) = (v * resources.displayMetrics.density).toInt()

    override fun onDestroyView() {
        super.onDestroyView()
        optionViews.clear()
        _binding = null
    }
}
