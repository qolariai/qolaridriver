package com.qolari.userlite.ui.activity

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.recyclerview.widget.RecyclerView
import com.qolari.userlite.R
import com.qolari.userlite.databinding.ItemHistoryTripBinding
import com.qolari.userlite.net.HistoryTrip

class HistoryAdapter(
    private var items: List<HistoryTrip> = emptyList(),
) : RecyclerView.Adapter<HistoryAdapter.Holder>() {

    fun submit(list: List<HistoryTrip>) {
        items = list
        notifyDataSetChanged()
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): Holder =
        Holder(ItemHistoryTripBinding.inflate(LayoutInflater.from(parent.context), parent, false))

    override fun getItemCount() = items.size

    override fun onBindViewHolder(holder: Holder, position: Int) = holder.bind(items[position])

    inner class Holder(private val binding: ItemHistoryTripBinding) : RecyclerView.ViewHolder(binding.root) {
        fun bind(item: HistoryTrip) {
            binding.date.text = item.date
            binding.state.text = when (item.state) {
                "completed" -> binding.root.context.getString(R.string.activity_trip_state_completed)
                "cancelled" -> binding.root.context.getString(R.string.activity_trip_state_cancelled)
                "no_drivers" -> binding.root.context.getString(R.string.activity_trip_state_no_drivers)
                else -> item.state
            }
            binding.route.text = "${item.pickup.ifBlank { "—" }} → ${item.dropoff.ifBlank { "—" }}"
            binding.product.text = item.product
            binding.fare.text = item.fare.label
        }
    }
}
