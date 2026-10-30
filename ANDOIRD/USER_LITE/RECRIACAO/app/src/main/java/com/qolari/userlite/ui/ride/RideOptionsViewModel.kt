package com.qolari.userlite.ui.ride

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.qolari.userlite.data.AppGraph
import com.qolari.userlite.data.UserRepository
import com.qolari.userlite.net.Payment
import com.qolari.userlite.net.QuoteProduct
import com.qolari.userlite.net.QuoteResponse
import com.qolari.userlite.net.RoutePoint
import com.qolari.userlite.net.Trip
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch

data class RideOptionsUiState(
    val loading: Boolean = true,
    val quote: QuoteResponse? = null,
    val selected: QuoteProduct? = null,
    val error: String? = null,
    val payment: Payment = Payment(),
    val requesting: Boolean = false,
    val requestError: String? = null,
    val trip: Trip? = null,
)

class RideOptionsViewModel @JvmOverloads constructor(
    private val repository: UserRepository = AppGraph.repository,
) : ViewModel() {

    private val _state = MutableStateFlow(RideOptionsUiState())
    val state: StateFlow<RideOptionsUiState> = _state

    fun load(pickup: RoutePoint, dropoff: RoutePoint) {
        _state.value = RideOptionsUiState(loading = true)
        viewModelScope.launch {
            repository.quote(pickup, dropoff)
                .onSuccess {
                    _state.value = RideOptionsUiState(
                        loading = false, quote = it, selected = it.products.firstOrNull(), payment = it.payment,
                    )
                }
                .onFailure {
                    _state.value = RideOptionsUiState(
                        loading = false, error = com.qolari.userlite.net.ApiClient.errorMessage(it),
                    )
                }
        }
    }

    fun select(product: QuoteProduct) {
        _state.value = _state.value.copy(selected = product)
    }

    fun selectPayment(id: String) {
        viewModelScope.launch {
            repository.selectPayment(id)
                .onSuccess { payment -> _state.value = _state.value.copy(payment = payment) }
                .onFailure { _state.value = _state.value.copy(error = com.qolari.userlite.net.ApiClient.errorMessage(it)) }
        }
    }

    fun request(pickup: RoutePoint, dropoff: RoutePoint, promoCode: String? = null) {
        val product = _state.value.selected ?: return
        if (_state.value.requesting) return
        _state.value = _state.value.copy(requesting = true, requestError = null)
        viewModelScope.launch {
            repository.request(pickup, dropoff, product.id, _state.value.payment.id, promoCode)
                .onSuccess { _state.value = _state.value.copy(requesting = false, trip = it) }
                .onFailure {
                    _state.value = _state.value.copy(
                        requesting = false,
                        requestError = com.qolari.userlite.net.ApiClient.errorMessage(it),
                    )
                }
        }
    }
}
