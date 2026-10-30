package com.qolari.userlite.ui.ride

import androidx.lifecycle.ViewModel
import com.qolari.userlite.net.QuoteProduct
import com.qolari.userlite.net.QuoteResponse
import com.qolari.userlite.net.RoutePoint
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow

/**
 * Rascunho da viagem partilhado entre Pesquisa, Escolha e Viagem. Vive na Activity
 * (`activityViewModels`), por isso sobrevive à navegação sem passar JSON em bundles.
 */
class RideViewModel : ViewModel() {

    val homePickup = RoutePoint(38.75300, -9.14500, "Casa, Lisboa")

    private val _pickup = MutableStateFlow(homePickup)
    val pickup: StateFlow<RoutePoint> = _pickup

    private val _dropoff = MutableStateFlow<RoutePoint?>(null)
    val dropoff: StateFlow<RoutePoint?> = _dropoff

    private val _quote = MutableStateFlow<QuoteResponse?>(null)
    val quote: StateFlow<QuoteResponse?> = _quote

    private val _selected = MutableStateFlow<QuoteProduct?>(null)
    val selected: StateFlow<QuoteProduct?> = _selected

    var promoCode: String? = null

    fun setPickup(point: RoutePoint) {
        _pickup.value = point
        _quote.value = null
    }

    fun setDropoff(point: RoutePoint) {
        _dropoff.value = point
        _quote.value = null
        _selected.value = null
    }

    fun setQuote(value: QuoteResponse) {
        _quote.value = value
        _selected.value = value.products.firstOrNull()
    }

    fun select(product: QuoteProduct) {
        _selected.value = product
    }

    fun reset() {
        _dropoff.value = null
        _quote.value = null
        _selected.value = null
        promoCode = null
    }
}
