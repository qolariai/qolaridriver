package com.qolari.userlite.ui.legal

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.recyclerview.widget.RecyclerView
import com.qolari.userlite.databinding.ItemLegalTopicBinding

data class LegalTopic(val title: String)

object LegalTopics {
    fun all(): List<LegalTopic> = listOf(
        "Direitos de autor",
        "Termos e Condições",
        "Política de Privacidade",
        "Fornecedores de dados",
        "Informações de localização",
        "Informações de contacto",
        "Outro",
    ).map { LegalTopic(it) }
}

class LegalAdapter(
    private var items: List<LegalTopic> = emptyList(),
    private val onClick: (LegalTopic) -> Unit,
) : RecyclerView.Adapter<LegalAdapter.Holder>() {

    fun submit(list: List<LegalTopic>) {
        items = list
        notifyDataSetChanged()
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): Holder =
        Holder(ItemLegalTopicBinding.inflate(LayoutInflater.from(parent.context), parent, false))

    override fun getItemCount() = items.size

    override fun onBindViewHolder(holder: Holder, position: Int) = holder.bind(items[position])

    inner class Holder(private val binding: ItemLegalTopicBinding) : RecyclerView.ViewHolder(binding.root) {
        fun bind(item: LegalTopic) {
            binding.title.text = item.title
            binding.title.setOnClickListener { onClick(item) }
        }
    }
}
