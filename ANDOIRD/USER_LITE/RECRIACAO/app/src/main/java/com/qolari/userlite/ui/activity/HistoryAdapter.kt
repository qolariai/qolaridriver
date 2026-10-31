package com.qolari.userlite.ui.activity

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.recyclerview.widget.RecyclerView
import com.qolari.userlite.R
import com.qolari.userlite.databinding.ItemHistoryTripBinding
import com.qolari.userlite.net.HistoryTrip

class HistoryAdapter(
    private var items: List<HistoryTrip> = emptyList(),
    private val onClick: ((HistoryTrip) -> Unit)? = null,
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
                "requested" -> binding.root.context.getString(R.string.activity_trip_state_requested)
                "accepted" -> binding.root.context.getString(R.string.activity_trip_state_accepted)
                "arrived" -> binding.root.context.getString(R.string.activity_trip_state_arrived)
                "in_progress" -> binding.root.context.getString(R.string.activity_trip_state_in_progress)
                else -> item.state
            }
            binding.route.text = listOf(item.pickup, item.dropoff)
                .filter { it.isNotBlank() }
                .joinToString(" → ")
                .ifBlank { binding.root.context.getString(R.string.activity_route_unknown) }
            binding.product.text = item.product
            // Só uma viagem concluída tem valor cobrado; cancelada/sem motorista não custou nada.
            val charged = item.state == "completed" && !item.fare.label.isBlank()
            binding.fare.text = if (charged) item.fare.label else binding.root.context.getString(R.string.activity_no_charge)
            binding.fare.setTextColor(
                binding.root.context.getColor(if (charged) R.color.ql_black else R.color.ql_gray_500)
            )
            binding.root.setOnClickListener { onClick?.invoke(item) }
        }
    }
}
