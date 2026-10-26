package com.qolari.userlite.ui.login

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.qolari.userlite.data.AppGraph
import com.qolari.userlite.data.UserRepository
import com.qolari.userlite.net.SessionResponse
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch

data class LoginUiState(
    val loading: Boolean = false,
    val error: String? = null,
    val session: SessionResponse? = null,
)

class LoginViewModel @JvmOverloads constructor(
    private val repository: UserRepository = AppGraph.repository,
) : ViewModel() {

    private val _state = MutableStateFlow(LoginUiState())
    val state: StateFlow<LoginUiState> = _state

    fun clearError() {
        _state.value = _state.value.copy(error = null)
    }

    fun login(phone: String, code: String) {
        if (_state.value.loading) return
        _state.value = LoginUiState(loading = true)
        viewModelScope.launch {
            repository.login(phone, code)
                .onSuccess { _state.value = LoginUiState(session = it) }
                .onFailure {
                    _state.value = LoginUiState(
                        error = com.qolari.userlite.net.ApiClient.errorMessage(it)
                            .takeIf { msg -> msg.isNotBlank() } ?: "Não foi possível entrar."
                    )
                }
        }
    }
}
