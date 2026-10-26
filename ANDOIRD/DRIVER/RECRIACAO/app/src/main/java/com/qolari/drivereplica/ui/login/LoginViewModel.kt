package com.qolari.drivereplica.ui.login

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.qolari.drivereplica.data.AppGraph
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import retrofit2.HttpException
import java.io.IOException

enum class LoginError { WRONG_CODE, NO_ACCOUNT, NETWORK, OTHER }

data class LoginUiState(
    val phoneDigits: String = "",
    val code: String = "",
    val loading: Boolean = false,
    val error: LoginError? = null,
    val signedIn: Boolean = false,
) {
    val phoneValid: Boolean get() = phoneDigits.length == PHONE_DIGITS
    val codeValid: Boolean get() = code.length == CODE_DIGITS
    /** Número completo para o servidor (o prefixo de Portugal é fixo no ecrã, D6). */
    val fullPhone: String get() = "$COUNTRY_PREFIX$phoneDigits"

    companion object {
        const val PHONE_DIGITS = 9
        const val CODE_DIGITS = 4
        const val COUNTRY_PREFIX = "+351"
    }
}

/**
 * Login nativo (D6: a original usa uma página web com reCAPTCHA): telefone e depois código de 4 dígitos.
 * Partilhado pelos ecrãs de telefone e de código. [signIn] devolve falha com [HttpException] (401 = código errado,
 * 404 = sem conta) ou [IOException] (sem rede).
 */
class LoginViewModel(private val signIn: suspend (phone: String, code: String) -> Result<Unit>) : ViewModel() {

    private val _state = MutableStateFlow(LoginUiState())
    val state: StateFlow<LoginUiState> = _state.asStateFlow()

    fun setPhone(raw: String) = _state.update {
        it.copy(phoneDigits = raw.filter(Char::isDigit).take(LoginUiState.PHONE_DIGITS), error = null)
    }

    fun setCode(raw: String) = _state.update {
        it.copy(code = raw.filter(Char::isDigit).take(LoginUiState.CODE_DIGITS), error = null)
    }

    /** Depois de navegar para a Página inicial: limpa o estado para o próximo login. */
    fun reset() { _state.value = LoginUiState() }

    fun submit() {
        val s = _state.value
        if (s.loading || !s.phoneValid || !s.codeValid) return
        _state.update { it.copy(loading = true, error = null) }
        viewModelScope.launch {
            signIn(s.fullPhone, s.code)
                .onSuccess { _state.update { it.copy(loading = false, signedIn = true) } }
                .onFailure { e -> _state.update { it.copy(loading = false, error = classify(e), code = "") } }
        }
    }

    companion object {
        fun classify(e: Throwable): LoginError = when {
            e is HttpException && e.code() == 401 -> LoginError.WRONG_CODE
            e is HttpException && e.code() == 404 -> LoginError.NO_ACCOUNT
            e is IOException -> LoginError.NETWORK
            else -> LoginError.OTHER
        }

        val Factory = object : ViewModelProvider.Factory {
            @Suppress("UNCHECKED_CAST")
            override fun <T : ViewModel> create(modelClass: Class<T>): T =
                LoginViewModel { phone, code -> AppGraph.repository.login(phone, code) } as T
        }
    }
}
