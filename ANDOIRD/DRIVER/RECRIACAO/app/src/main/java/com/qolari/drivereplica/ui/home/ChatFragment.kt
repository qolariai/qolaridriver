package com.qolari.drivereplica.ui.home

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.LinearLayout
import android.widget.TextView
import androidx.core.content.ContextCompat
import androidx.fragment.app.Fragment
import androidx.fragment.app.activityViewModels
import com.qolari.drivereplica.R
import com.qolari.drivereplica.databinding.FragmentChatBinding
import com.qolari.drivereplica.drive.DriveViewModel

/**
 * Chat com o passageiro (vídeo 2026-10-30): abre pelo ícone de telefone do ecrã de espera.
 *
 * O condutor pode **escrever** ou **ligar** (ícone do telefone no topo). As mensagens ficam na
 * sessão da viagem (o servidor guarda-as em `TripEvent` e a app do passageiro vê-as).
 */
class ChatFragment : Fragment(R.layout.fragment_chat) {

    private val drive: DriveViewModel by activityViewModels { DriveViewModel.Factory }
    private var binding: FragmentChatBinding? = null

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        val b = FragmentChatBinding.inflate(inflater, container, false)
        binding = b
        b.chatBack.setOnClickListener { parentFragmentManager.popBackStack() }
        b.chatTitle.text = drive.state.value.trip?.riderName.orEmpty()
        b.chatCall.setOnClickListener { call() }
        b.chatSend.setOnClickListener { send() }
        render()
        return b.root
    }

    private fun send() {
        val b = binding ?: return
        val text = b.chatInput.text?.toString()?.trim().orEmpty()
        if (text.isEmpty()) return
        drive.sendMessage(text)
        b.chatInput.setText("")
        render()
    }

    /** Liga para o passageiro (marcador do telemóvel com o número do servidor). */
    private fun call() {
        val phone = drive.state.value.trip?.riderPhone
        if (phone.isNullOrBlank()) return
        runCatching {
            startActivity(Intent(Intent.ACTION_DIAL, Uri.parse("tel:$phone")))
        }
    }

    /** Desenha as mensagens: as do condutor à direita, as do passageiro à esquerda. */
    private fun render() {
        val b = binding ?: return
        val messages = drive.state.value.messages
        b.chatMessages.removeAllViews()
        messages.forEach { m ->
            val row = TextView(requireContext()).apply {
                text = m.text
                textSize = 16f
                // O balão do condutor é preto, logo o texto tem de ser branco (estava preto
                // sobre preto e a mensagem ficava invisível).
                setTextColor(
                    ContextCompat.getColor(
                        requireContext(),
                        if (m.mine) R.color.qd_core_white else R.color.qd_ink,
                    ),
                )
                setPadding(28, 22, 28, 22)
                setBackgroundResource(if (m.mine) R.drawable.bg_chat_mine else R.drawable.bg_chat_theirs)
                layoutParams = LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.WRAP_CONTENT,
                    LinearLayout.LayoutParams.WRAP_CONTENT,
                ).apply {
                    topMargin = (6 * resources.displayMetrics.density).toInt()
                    gravity = if (m.mine) android.view.Gravity.END else android.view.Gravity.START
                }
            }
            b.chatMessages.addView(row)
        }
        b.chatScroll.post { b.chatScroll.fullScroll(View.FOCUS_DOWN) }
    }

    override fun onDestroyView() {
        binding = null
        super.onDestroyView()
    }
}
