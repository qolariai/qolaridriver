package com.qolari.userlite.ui.home

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.qolari.userlite.data.AppGraph
import com.qolari.userlite.data.SessionStore
import com.qolari.userlite.data.UserRepository
import com.qolari.userlite.net.HomeResponse
import com.qolari.userlite.net.SessionResponse
import com.qolari.userlite.net.Trip
import com.qolari.userlite.ui.ride.SeenTrips
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
    private val terminalStore: SessionStore = AppGraph.session,
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
            val seen = SeenTrips.lastTerminal ?: terminalStore.lastTerminal()
            repository.home()
                .onSuccess { home ->
                    // O /rt/lite/active devolve também o desfecho recente (completed/cancelled/no_drivers)
                    // para a app mostrar o fim e a avaliação antes de voltar ao início. Não filtrar só
                    // os estados ativos: isso perdia a avaliação quando a app era reaberta.
                    val active = repository.active().getOrNull()
                        ?.takeIf {
                            it.state in setOf(
                                "requested", "accepted", "arrived", "in_progress",
                            ) || (it.state in setOf("completed", "cancelled", "no_drivers") &&
                                it.uuid != seen)
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
