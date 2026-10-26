package com.qolari.userlite.ui.promotions

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.core.view.isVisible
import androidx.recyclerview.widget.RecyclerView
import com.qolari.userlite.databinding.ItemAppliedPromoBinding
import com.qolari.userlite.net.AppliedPromo

class AppliedPromoAdapter(
    private var items: List<AppliedPromo> = emptyList(),
) : RecyclerView.Adapter<AppliedPromoAdapter.Holder>() {

    fun submit(list: List<AppliedPromo>) {
        items = list
        notifyDataSetChanged()
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): Holder =
        Holder(ItemAppliedPromoBinding.inflate(LayoutInflater.from(parent.context), parent, false))

    override fun getItemCount() = items.size

    override fun onBindViewHolder(holder: Holder, position: Int) = holder.bind(items[position])

    inner class Holder(private val binding: ItemAppliedPromoBinding) : RecyclerView.ViewHolder(binding.root) {
        fun bind(item: AppliedPromo) {
            binding.code.text = item.code
            binding.description.text = item.description
            binding.valid.isVisible = item.valid
        }
    }
}
