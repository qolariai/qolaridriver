package com.qolari.userlite.ui.wallet

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.core.view.isVisible
import androidx.recyclerview.widget.RecyclerView
import com.qolari.userlite.databinding.ItemPaymentBinding
import com.qolari.userlite.net.Payment

class PaymentAdapter(
    private var items: List<Payment> = emptyList(),
    private var selectedId: String = "cash",
    private val onClick: (Payment) -> Unit,
) : RecyclerView.Adapter<PaymentAdapter.Holder>() {

    fun submit(list: List<Payment>, selected: String) {
        items = list
        selectedId = selected
        notifyDataSetChanged()
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): Holder =
        Holder(ItemPaymentBinding.inflate(LayoutInflater.from(parent.context), parent, false))

    override fun getItemCount() = items.size

    override fun onBindViewHolder(holder: Holder, position: Int) = holder.bind(items[position])

    inner class Holder(private val binding: ItemPaymentBinding) : RecyclerView.ViewHolder(binding.root) {
        fun bind(item: Payment) {
            binding.label.text = item.label
            binding.detail.text = item.detail
            binding.check.isVisible = item.id == selectedId
            binding.root.setOnClickListener { onClick(item) }
        }
    }
}
