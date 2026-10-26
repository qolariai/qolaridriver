package com.qolari.drivereplica.ui.discover

import androidx.lifecycle.ViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import java.time.LocalDate

data class DiscoverUiState(
    val days: List<LocalDate>,
    val selectedDay: LocalDate,
    val filters: Set<DiscoverFilter> = emptySet(),
    val saved: Set<String> = emptySet(),
    val rows: List<DiscoverRow> = emptyList(),
)

/**
 * Descobrir. Os botões "Lembretes / Promoções / Aeroportos" são filtros (ux_behavior.md §2): sem nenhum ligado vê-se
 * tudo; ligados, só as categorias escolhidas (Lembretes = itens guardados, Promoções = cartões, Aeroportos = picos).
 */
class DiscoverViewModel(
    private val today: LocalDate = LocalDate.now(),
    private val items: List<DiscoverItem> = DiscoverFixtures.items(today),
    private val promos: List<Promo> = DiscoverFixtures.promos,
) : ViewModel() {

    private val days = (0 until 14).map { today.plusDays(it.toLong()) }
    private val _state = MutableStateFlow(build(DiscoverUiState(days, today)))
    val state: StateFlow<DiscoverUiState> = _state.asStateFlow()

    fun toggleFilter(f: DiscoverFilter) = _state.update { s ->
        build(s.copy(filters = if (f in s.filters) s.filters - f else s.filters + f))
    }

    fun toggleSaved(id: String) = _state.update { s ->
        build(s.copy(saved = if (id in s.saved) s.saved - id else s.saved + id))
    }

    fun selectDay(day: LocalDate) = _state.update { it.copy(selectedDay = day) }

    private fun visible(s: DiscoverUiState, item: DiscoverItem): Boolean {
        if (s.filters.isEmpty()) return true
        return (DiscoverFilter.REMINDERS in s.filters && item.id in s.saved) ||
            (DiscoverFilter.AIRPORTS in s.filters && item.kind == DiscoverKind.AIRPORT)
    }

    private fun build(s: DiscoverUiState): DiscoverUiState {
        val rows = mutableListOf<DiscoverRow>(DiscoverRow.Chips)
        if (s.filters.isEmpty() || DiscoverFilter.PROMOS in s.filters) rows += DiscoverRow.Promos(promos)
        items.filter { visible(s, it) }.groupBy { it.date }.toSortedMap().forEach { (date, list) ->
            rows += DiscoverRow.DayHeader(date)
            list.forEach { rows += DiscoverRow.Item(it, it.id in s.saved) }
        }
        return s.copy(rows = rows)
    }
}
