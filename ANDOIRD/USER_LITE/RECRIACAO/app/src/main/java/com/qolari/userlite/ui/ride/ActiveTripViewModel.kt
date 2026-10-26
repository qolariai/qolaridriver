package com.qolari.userlite.ui.ride

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.qolari.userlite.config.AppConfig
import com.qolari.userlite.data.AppGraph
import com.qolari.userlite.data.UserRepository
import com.qolari.userlite.net.Trip
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch

data class ActiveTripUiState(
    val loading: Boolean = true,
    val trip: Trip? = null,
    val error: String? = null,
    val canceling: Boolean = false,
    val rating: Boolean = false,
    val rated: Boolean = false,
    val empty: Boolean = false,
)

class ActiveTripViewModel @JvmOverloads constructor(
    private val repository: UserRepository = AppGraph.repository,
) : ViewModel() {

    private val _state = MutableStateFlow(ActiveTripUiState())
    val state: StateFlow<ActiveTripUiState> = _state
    private var poll: Job? = null

    private val terminal = setOf("completed", "cancelled", "no_drivers")

    fun start() {
        if (poll?.isActive == true) return
        poll = viewModelScope.launch {
            while (isActive) {
                repository.active()
                    .onSuccess { trip ->
                        if (trip == null) {
                            _state.value = _state.value.copy(loading = false, empty = true)
                            break
                        }
                        _state.value = _state.value.copy(loading = false, trip = trip, error = null, empty = false)
                        if (trip.state in terminal) break
                    }
                    .onFailure {
                        if (_state.value.trip == null) {
                            _state.value = _state.value.copy(
                                loading = false,
                                error = com.qolari.userlite.net.ApiClient.errorMessage(it),
                            )
                        }
                    }
                delay(AppConfig.TRIP_POLL_INTERVAL_MS)
            }
        }
    }

    fun refresh() {
        poll?.cancel()
        _state.value = _state.value.copy(loading = true, error = null, empty = false)
        start()
    }

    fun stop() {
        poll?.cancel()
    }

    fun cancel(uuid: String) {
        if (_state.value.canceling) return
        _state.value = _state.value.copy(canceling = true, error = null)
        viewModelScope.launch {
            repository.cancel(uuid, "cancelada pelo passageiro")
                .onSuccess { _state.value = _state.value.copy(canceling = false, trip = it) }
                .onFailure {
                    _state.value = _state.value.copy(
                        canceling = false,
                        error = com.qolari.userlite.net.ApiClient.errorMessage(it),
                    )
                }
        }
    }

    fun rate(uuid: String, stars: Int) {
        if (_state.value.rating) return
        _state.value = _state.value.copy(rating = true, error = null)
        viewModelScope.launch {
            repository.rate(uuid, stars)
                .onSuccess { _state.value = _state.value.copy(rating = false, rated = true, trip = it) }
                .onFailure {
                    _state.value = _state.value.copy(
                        rating = false,
                        error = com.qolari.userlite.net.ApiClient.errorMessage(it),
                    )
                }
        }
    }

    override fun onCleared() {
        poll?.cancel()
        super.onCleared()
    }
}
