package com.qolari.userlite.ui.home

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.qolari.userlite.data.AppGraph
import com.qolari.userlite.data.UserRepository
import com.qolari.userlite.net.HomeResponse
import com.qolari.userlite.net.SessionResponse
import com.qolari.userlite.net.Trip
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch

data class HomeUiState(
    val loading: Boolean = false,
    val error: String? = null,
    val home: HomeResponse? = null,
    val session: SessionResponse? = null,
    val activeTrip: Trip? = null,
)

class HomeViewModel @JvmOverloads constructor(
    private val repository: UserRepository = AppGraph.repository,
) : ViewModel() {

    private val _state = MutableStateFlow(HomeUiState())
    val state: StateFlow<HomeUiState> = _state

    fun updateLocation(lat: Double, lng: Double) {
        viewModelScope.launch { repository.uploadLocation(lat, lng) }
    }

    fun load(quiet: Boolean = false) {
        if (_state.value.loading) return
        _state.value = _state.value.copy(loading = !quiet, error = null)
        viewModelScope.launch {
            repository.home()
                .onSuccess { home ->
                    val active = repository.active().getOrNull()
                        ?.takeIf {
                            it.state in setOf("requested", "accepted", "arrived", "in_progress") ||
                                (it.state == "completed" && it.canRate)
                        }
                    _state.value = HomeUiState(home = home, activeTrip = active)
                }
                .onFailure { fail(it) }
        }
    }

    private fun fail(error: Throwable) {
        _state.value = _state.value.copy(
            loading = false,
            error = com.qolari.userlite.net.ApiClient.errorMessage(error),
        )
    }
}
