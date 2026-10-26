package com.qolari.userlite.ui.ride

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.core.view.isVisible
import androidx.recyclerview.widget.RecyclerView
import com.qolari.userlite.R
import com.qolari.userlite.databinding.ItemRideProductBinding
import com.qolari.userlite.net.QuoteProduct

class RideProductAdapter(
    private var items: List<QuoteProduct> = emptyList(),
    private var selectedId: Int? = null,
    private val onClick: (QuoteProduct) -> Unit,
) : RecyclerView.Adapter<RideProductAdapter.Holder>() {

    fun submit(list: List<QuoteProduct>, selected: QuoteProduct?) {
        items = list
        selectedId = selected?.id
        notifyDataSetChanged()
    }

    fun select(product: QuoteProduct) {
        selectedId = product.id
        notifyDataSetChanged()
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): Holder =
        Holder(ItemRideProductBinding.inflate(LayoutInflater.from(parent.context), parent, false))

    override fun getItemCount() = items.size

    override fun onBindViewHolder(holder: Holder, position: Int) = holder.bind(items[position])

    inner class Holder(private val binding: ItemRideProductBinding) : RecyclerView.ViewHolder(binding.root) {
        fun bind(item: QuoteProduct) {
            binding.name.text = item.name
            binding.capacity.text = binding.root.context.getString(R.string.ride_seats, item.capacity)
            binding.time.text = binding.root.context.getString(R.string.ride_eta, item.etaMin)
            binding.price.text = item.price
            binding.fastest.isVisible = item.fastest
            binding.leaf.isVisible = item.name.contains("Electric", ignoreCase = true)
            binding.icon.setImageResource(
                if (item.capacity >= 6 || item.name.contains("XL", ignoreCase = true)) R.drawable.ic_van else R.drawable.ic_car
            )
            binding.root.setBackgroundResource(
                if (item.id == selectedId) R.drawable.bg_ride_product_selected else R.drawable.bg_ride_product
            )
            binding.root.setOnClickListener { onClick(item) }
        }
    }
}
