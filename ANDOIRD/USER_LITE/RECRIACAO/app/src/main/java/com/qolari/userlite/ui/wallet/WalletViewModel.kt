package com.qolari.userlite.ui.wallet

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.qolari.userlite.data.AppGraph
import com.qolari.userlite.data.UserRepository
import com.qolari.userlite.net.WalletResponse
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch

data class WalletUiState(
    val loading: Boolean = true,
    val wallet: WalletResponse? = null,
    val error: String? = null,
)

class WalletViewModel @JvmOverloads constructor(
    private val repository: UserRepository = AppGraph.repository,
) : ViewModel() {

    private val _state = MutableStateFlow(WalletUiState())
    val state: StateFlow<WalletUiState> = _state

    fun load() {
        _state.value = _state.value.copy(loading = true, error = null)
        viewModelScope.launch {
            repository.wallet()
                .onSuccess { _state.value = WalletUiState(loading = false, wallet = it) }
                .onFailure {
                    _state.value = WalletUiState(
                        loading = false,
                        error = com.qolari.userlite.net.ApiClient.errorMessage(it),
                    )
                }
        }
    }

    fun select(id: String) {
        viewModelScope.launch {
            repository.selectPayment(id)
                .onSuccess { load() }
                .onFailure { _state.value = _state.value.copy(error = com.qolari.userlite.net.ApiClient.errorMessage(it)) }
        }
    }

    fun topUp(amountCents: Int) {
        viewModelScope.launch {
            repository.topUp(amountCents)
                .onSuccess { load() }
                .onFailure { _state.value = _state.value.copy(error = com.qolari.userlite.net.ApiClient.errorMessage(it)) }
        }
    }
}
