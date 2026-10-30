package com.qolari.drivereplica.ui.discover

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.core.view.isVisible
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.PagerSnapHelper
import androidx.recyclerview.widget.RecyclerView
import com.qolari.drivereplica.R
import com.qolari.drivereplica.databinding.ItemDiscoverDayBinding
import com.qolari.drivereplica.databinding.ItemDiscoverEventBinding
import com.qolari.drivereplica.databinding.ItemDiscoverPromosBinding
import com.qolari.drivereplica.databinding.ItemPromoCardBinding

/** Lista de Descobrir: cartões de promoções (com pontos), cabeçalhos de dia e eventos. Os filtros são fixos no cabeçalho. */
class DiscoverAdapter(
    private val onSave: (String) -> Unit,
) : RecyclerView.Adapter<RecyclerView.ViewHolder>() {

    private var rows: List<DiscoverRow> = emptyList()

    fun submit(newRows: List<DiscoverRow>) {
        rows = newRows
        notifyDataSetChanged()
    }

    fun positionOfDay(date: java.time.LocalDate): Int =
        rows.indexOfFirst { it is DiscoverRow.DayHeader && it.date == date }

    /** Dia a que pertence a linha [position] (o do cabeçalho anterior), ou nulo antes do primeiro dia. */
    fun dayAt(position: Int): java.time.LocalDate? {
        for (i in position downTo 0) {
            (rows.getOrNull(i) as? DiscoverRow.DayHeader)?.let { return it.date }
        }
        return null
    }

    override fun getItemCount() = rows.size

    override fun getItemViewType(position: Int) = when (rows[position]) {
        is DiscoverRow.Promos -> 0
        is DiscoverRow.DayHeader -> 1
        is DiscoverRow.Item -> 2
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): RecyclerView.ViewHolder {
        val inflater = LayoutInflater.from(parent.context)
        return when (viewType) {
            0 -> PromosHolder(ItemDiscoverPromosBinding.inflate(inflater, parent, false))
            1 -> DayHolder(ItemDiscoverDayBinding.inflate(inflater, parent, false))
            else -> EventHolder(ItemDiscoverEventBinding.inflate(inflater, parent, false))
        }
    }

    override fun onBindViewHolder(holder: RecyclerView.ViewHolder, position: Int) {
        when (val row = rows[position]) {
            is DiscoverRow.Promos -> (holder as PromosHolder).bind(row.promos)
            is DiscoverRow.DayHeader -> (holder as DayHolder).b.dayHeaderText.text = PtDates.header(row.date)
            is DiscoverRow.Item -> (holder as EventHolder).bind(row)
        }
    }

    private inner class PromosHolder(val b: ItemDiscoverPromosBinding) : RecyclerView.ViewHolder(b.root) {
        private val snap = PagerSnapHelper()
        private val manager = LinearLayoutManager(b.root.context, LinearLayoutManager.HORIZONTAL, false)

        init {
            b.promoList.layoutManager = manager
            snap.attachToRecyclerView(b.promoList)
            b.promoList.addOnScrollListener(object : RecyclerView.OnScrollListener() {
                override fun onScrolled(rv: RecyclerView, dx: Int, dy: Int) {
                    val v = snap.findSnapView(manager) ?: return
                    b.promoDots.selected = manager.getPosition(v)
                }
            })
        }

        fun bind(promos: List<Promo>) {
            b.promoDots.count = promos.size
            b.promoList.adapter = object : RecyclerView.Adapter<PromoHolder>() {
                override fun getItemCount() = promos.size
                override fun onCreateViewHolder(p: ViewGroup, t: Int) =
                    PromoHolder(ItemPromoCardBinding.inflate(LayoutInflater.from(p.context), p, false))
                override fun onBindViewHolder(h: PromoHolder, i: Int) {
                    h.b.promoTitle.text = promos[i].title
                    h.b.promoSubtitle.text = promos[i].subtitle
                }
            }
        }
    }

    private class PromoHolder(val b: ItemPromoCardBinding) : RecyclerView.ViewHolder(b.root)

    private class DayHolder(val b: ItemDiscoverDayBinding) : RecyclerView.ViewHolder(b.root)

    private inner class EventHolder(val b: ItemDiscoverEventBinding) : RecyclerView.ViewHolder(b.root) {
        fun bind(row: DiscoverRow.Item) {
            val i = row.item
            b.eventTime.text = i.time
            b.eventTitle.text = i.title
            b.eventPlace.text = i.place
            b.eventPlace.isVisible = !i.place.isNullOrBlank()
            b.eventTag.text = i.tag
            val airport = i.kind == DiscoverKind.AIRPORT
            b.eventThumbCard.isVisible = !airport
            b.eventPlane.isVisible = airport
            b.eventSave.setText(if (row.saved) R.string.discover_saved else R.string.discover_save)
            b.eventSave.isSelected = row.saved
            b.eventSave.setOnClickListener { onSave(i.id) }
        }
    }
}
