package com.qolari.userlite.ui.search

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.recyclerview.widget.RecyclerView
import com.qolari.userlite.databinding.ItemPlaceBinding
import com.qolari.userlite.net.Place

class PlaceAdapter(
    private var items: List<Place> = emptyList(),
    private val onClick: (Place) -> Unit,
) : RecyclerView.Adapter<PlaceAdapter.Holder>() {

    fun submit(list: List<Place>) {
        items = list
        notifyDataSetChanged()
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): Holder =
        Holder(ItemPlaceBinding.inflate(LayoutInflater.from(parent.context), parent, false))

    override fun getItemCount() = items.size

    override fun onBindViewHolder(holder: Holder, position: Int) = holder.bind(items[position])

    inner class Holder(private val binding: ItemPlaceBinding) : RecyclerView.ViewHolder(binding.root) {
        fun bind(item: Place) {
            binding.name.text = item.name
            binding.detail.text = listOf(item.line1, item.line2).filter { it.isNotBlank() }
                .distinct().joinToString(", ")
            binding.root.setOnClickListener { onClick(item) }
        }
    }
}
