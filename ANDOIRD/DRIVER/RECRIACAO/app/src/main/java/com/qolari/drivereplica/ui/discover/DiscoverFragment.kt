package com.qolari.drivereplica.ui.discover

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.qolari.drivereplica.R
import com.qolari.drivereplica.databinding.FragmentDiscoverBinding
import com.qolari.drivereplica.databinding.ItemDayCellBinding
import kotlinx.coroutines.launch
import java.time.LocalDate

/**
 * Separador Descobrir (Views; capturas 010, 036, 061, 080, 081). Título e faixa de dias fixos; ao tocar num dia a lista
 * salta para esse dia e, ao fazer scroll, o dia da faixa acompanha a lista. Conteúdo de exemplo (D7).
 */
class DiscoverFragment : Fragment() {

    private var _binding: FragmentDiscoverBinding? = null
    private val binding get() = _binding!!
    private val viewModel: DiscoverViewModel by viewModels()
    private val cells = mutableMapOf<LocalDate, ItemDayCellBinding>()
    private lateinit var adapter: DiscoverAdapter

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentDiscoverBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        adapter = DiscoverAdapter(onSave = viewModel::toggleSaved)
        val manager = LinearLayoutManager(requireContext())
        binding.discoverList.layoutManager = manager
        binding.discoverList.adapter = adapter
        binding.discoverList.addOnScrollListener(object : RecyclerView.OnScrollListener() {
            override fun onScrolled(rv: RecyclerView, dx: Int, dy: Int) {
                adapter.dayAt(manager.findFirstVisibleItemPosition())?.let(viewModel::selectDay)
            }
        })
        buildDayStrip(viewModel.state.value.days)
        with(binding.chipsHeader) {
            chipReminders.setOnClickListener { viewModel.toggleFilter(DiscoverFilter.REMINDERS) }
            chipPromos.setOnClickListener { viewModel.toggleFilter(DiscoverFilter.PROMOS) }
            chipAirports.setOnClickListener { viewModel.toggleFilter(DiscoverFilter.AIRPORTS) }
        }

        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                viewModel.state.collect { s ->
                    adapter.submit(s.rows)
                    binding.chipsHeader.chipReminders.isSelected = DiscoverFilter.REMINDERS in s.filters
                    binding.chipsHeader.chipPromos.isSelected = DiscoverFilter.PROMOS in s.filters
                    binding.chipsHeader.chipAirports.isSelected = DiscoverFilter.AIRPORTS in s.filters
                    cells.forEach { (day, c) -> c.mark(day == s.selectedDay) }
                    cells[s.selectedDay]?.root?.let { cell ->
                        binding.dayStripScroll.post {
                            binding.dayStripScroll.smoothScrollTo(
                                (cell.left - binding.dayStripScroll.width / 2 + cell.width / 2).coerceAtLeast(0), 0,
                            )
                        }
                    }
                }
            }
        }
    }

    private fun buildDayStrip(days: List<LocalDate>) {
        days.forEach { day ->
            val c = ItemDayCellBinding.inflate(layoutInflater, binding.dayStrip, false)
            c.dayName.text = PtDates.short(day)
            c.dayNumber.text = day.dayOfMonth.toString()
            c.root.setOnClickListener {
                viewModel.selectDay(day)
                val pos = adapter.positionOfDay(day)
                if (pos >= 0) (binding.discoverList.layoutManager as LinearLayoutManager).scrollToPositionWithOffset(pos, 0)
            }
            binding.dayStrip.addView(c.root)
            cells[day] = c
        }
    }

    private fun ItemDayCellBinding.mark(selected: Boolean) {
        val ink = requireContext().getColor(R.color.qd_ink)
        val dim = requireContext().getColor(R.color.qd_core_gray600)
        dayName.setTextColor(if (selected) ink else dim)
        dayNumber.setTextColor(if (selected) ink else dim)
        dayNumber.setTypeface(null, if (selected) android.graphics.Typeface.BOLD else android.graphics.Typeface.NORMAL)
        dayName.setTypeface(null, if (selected) android.graphics.Typeface.BOLD else android.graphics.Typeface.NORMAL)
        dayUnderline.visibility = if (selected) View.VISIBLE else View.INVISIBLE
    }

    override fun onDestroyView() {
        cells.clear()
        _binding = null
        super.onDestroyView()
    }
}
