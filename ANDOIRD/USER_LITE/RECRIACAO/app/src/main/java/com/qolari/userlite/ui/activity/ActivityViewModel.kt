package com.qolari.userlite.ui.activity

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.qolari.userlite.data.AppGraph
import com.qolari.userlite.data.UserRepository
import com.qolari.userlite.net.HistoryTrip
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch

data class ActivityUiState(
    val loading: Boolean = true,
    val trips: List<HistoryTrip> = emptyList(),
    val error: String? = null,
)

class ActivityViewModel @JvmOverloads constructor(
    private val repository: UserRepository = AppGraph.repository,
) : ViewModel() {

    private val _state = MutableStateFlow(ActivityUiState())
    val state: StateFlow<ActivityUiState> = _state

    fun load() {
        _state.value = _state.value.copy(loading = true, error = null)
        viewModelScope.launch {
            repository.history()
                .onSuccess { _state.value = ActivityUiState(loading = false, trips = it.trips) }
                .onFailure {
                    _state.value = ActivityUiState(
                        loading = false,
                        error = com.qolari.userlite.net.ApiClient.errorMessage(it),
                    )
                }
        }
    }

    /** 0 = todas, 1 = concluídas, 2 = canceladas, 3 = sem motorista (ordem do diálogo). */
    fun filtered(which: Int): List<HistoryTrip> {
        val trips = _state.value.trips
        return when (which) {
            1 -> trips.filter { it.state == "completed" }
            2 -> trips.filter { it.state == "cancelled" }
            3 -> trips.filter { it.state == "no_drivers" }
            else -> trips
        }
    }
}
