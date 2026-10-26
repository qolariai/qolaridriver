package com.qolari.userlite.ui.home

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.recyclerview.widget.RecyclerView
import com.qolari.userlite.R
import com.qolari.userlite.databinding.ItemPromoCardBinding
import com.qolari.userlite.databinding.ItemSuggestionBinding
import com.qolari.userlite.net.PromoCard
import com.qolari.userlite.net.Suggestion

class SuggestionAdapter(
    private var items: List<Suggestion> = emptyList(),
    private val onClick: (Suggestion) -> Unit,
) : RecyclerView.Adapter<SuggestionAdapter.Holder>() {

    fun submit(list: List<Suggestion>) {
        items = list
        notifyDataSetChanged()
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): Holder =
        Holder(ItemSuggestionBinding.inflate(LayoutInflater.from(parent.context), parent, false))

    override fun getItemCount() = items.size

    override fun onBindViewHolder(holder: Holder, position: Int) = holder.bind(items[position])

    inner class Holder(private val binding: ItemSuggestionBinding) : RecyclerView.ViewHolder(binding.root) {
        fun bind(item: Suggestion) {
            binding.title.text = item.title
            binding.subtitle.text = item.subtitle
            binding.icon.setImageResource(iconFor(item.icon))
            binding.root.setOnClickListener { onClick(item) }
        }
    }

    private fun iconFor(icon: String) = when (icon) {
        "box" -> R.drawable.ic_box
        "calendar" -> R.drawable.ic_calendar
        "package" -> R.drawable.ic_package
        else -> R.drawable.ic_car
    }
}

class PromoAdapter(
    private var items: List<PromoCard> = emptyList(),
    private val onClick: (PromoCard) -> Unit,
) : RecyclerView.Adapter<PromoAdapter.Holder>() {

    fun submit(list: List<PromoCard>) {
        items = list
        notifyDataSetChanged()
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): Holder =
        Holder(ItemPromoCardBinding.inflate(LayoutInflater.from(parent.context), parent, false))

    override fun getItemCount() = items.size

    override fun onBindViewHolder(holder: Holder, position: Int) = holder.bind(items[position])

    inner class Holder(private val binding: ItemPromoCardBinding) : RecyclerView.ViewHolder(binding.root) {
        fun bind(item: PromoCard) {
            binding.title.text = item.title
            binding.subtitle.text = item.subtitle
            binding.action.text = item.action
            binding.root.setOnClickListener { onClick(item) }
        }
    }
}
