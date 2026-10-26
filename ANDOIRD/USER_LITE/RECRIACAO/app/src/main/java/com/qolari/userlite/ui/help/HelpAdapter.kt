package com.qolari.userlite.ui.help

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.recyclerview.widget.RecyclerView
import com.qolari.userlite.R
import com.qolari.userlite.databinding.ItemHelpTopicBinding

data class HelpTopic(val id: String, val title: String, val icon: Int)

object HelpTopics {
    fun all(): List<HelpTopic> = listOf(
        HelpTopic("trip", "Ajuda com uma viagem", R.drawable.ic_car),
        HelpTopic("account", "Conta", R.drawable.ic_list),
        HelpTopic("subscription", "Subscrição", R.drawable.ic_list),
        HelpTopic("accessibility", "Acessibilidade", R.drawable.ic_account),
        HelpTopic("guides", "Guias", R.drawable.ic_list),
        HelpTopic("more", "Comboios, aluguer de automóveis, voos e muito mais", R.drawable.ic_list),
        HelpTopic("map", "Problema com o mapa", R.drawable.ic_list),
        HelpTopic("delivery", "Entrega do artigo", R.drawable.ic_list),
        HelpTopic("messages", "Mensagens de apoio", R.drawable.ic_list),
    )
}

class HelpAdapter(
    private var items: List<HelpTopic> = emptyList(),
    private val onClick: (HelpTopic) -> Unit,
) : RecyclerView.Adapter<HelpAdapter.Holder>() {

    fun submit(list: List<HelpTopic>) {
        items = list
        notifyDataSetChanged()
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): Holder =
        Holder(ItemHelpTopicBinding.inflate(LayoutInflater.from(parent.context), parent, false))

    override fun getItemCount() = items.size

    override fun onBindViewHolder(holder: Holder, position: Int) = holder.bind(items[position])

    inner class Holder(private val binding: ItemHelpTopicBinding) : RecyclerView.ViewHolder(binding.root) {
        fun bind(item: HelpTopic) {
            binding.title.text = item.title
            binding.icon.setImageResource(item.icon)
            binding.root.setOnClickListener { onClick(item) }
        }
    }
}
