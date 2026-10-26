package com.qolari.userlite.ui.menu

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.qolari.userlite.data.AppGraph
import com.qolari.userlite.data.UserRepository
import com.qolari.userlite.net.SessionResponse
import com.qolari.userlite.net.WalletResponse
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch

data class MenuUiState(
    val session: SessionResponse? = null,
    val wallet: WalletResponse? = null,
    val error: String? = null,
    val signedOut: Boolean = false,
)

class MenuViewModel @JvmOverloads constructor(
    private val repository: UserRepository = AppGraph.repository,
) : ViewModel() {

    private val _state = MutableStateFlow(MenuUiState())
    val state: StateFlow<MenuUiState> = _state

    fun load() {
        viewModelScope.launch {
            repository.session().onSuccess { _state.value = _state.value.copy(session = it, error = null) }
                .onFailure { _state.value = _state.value.copy(error = com.qolari.userlite.net.ApiClient.errorMessage(it)) }
            repository.wallet().onSuccess { _state.value = _state.value.copy(wallet = it) }
        }
    }

    fun signOut() {
        viewModelScope.launch {
            repository.signOut()
            _state.value = _state.value.copy(signedOut = true)
        }
    }
}
