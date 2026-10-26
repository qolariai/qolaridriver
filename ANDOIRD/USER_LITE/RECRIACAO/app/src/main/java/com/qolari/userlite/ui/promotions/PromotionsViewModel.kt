package com.qolari.userlite.ui.promotions

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.qolari.userlite.data.AppGraph
import com.qolari.userlite.data.UserRepository
import com.qolari.userlite.net.AppliedPromo
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch

data class PromotionsUiState(
    val loading: Boolean = false,
    val applied: List<AppliedPromo> = emptyList(),
    val message: String? = null,
    val error: String? = null,
)

class PromotionsViewModel @JvmOverloads constructor(
    private val repository: UserRepository = AppGraph.repository,
) : ViewModel() {

    private val _state = MutableStateFlow(PromotionsUiState())
    val state: StateFlow<PromotionsUiState> = _state

    fun load() {
        _state.value = _state.value.copy(loading = true, error = null)
        viewModelScope.launch {
            repository.promotions()
                .onSuccess { _state.value = PromotionsUiState(loading = false, applied = it.applied, message = it.hint) }
                .onFailure { _state.value = PromotionsUiState(error = com.qolari.userlite.net.ApiClient.errorMessage(it)) }
        }
    }

    fun apply(code: String) {
        if (code.isBlank()) return
        _state.value = _state.value.copy(loading = true, error = null, message = null)
        viewModelScope.launch {
            repository.applyPromotion(code)
                .onSuccess {
                    _state.value = _state.value.copy(
                        loading = false,
                        message = "Código ${code.uppercase()} aplicado.",
                    )
                    load()
                }
                .onFailure {
                    _state.value = _state.value.copy(
                        loading = false,
                        error = com.qolari.userlite.net.ApiClient.errorMessage(it),
                    )
                }
        }
    }
}
