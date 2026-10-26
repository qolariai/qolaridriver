package com.qolari.userlite.ui.account

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.qolari.userlite.data.AppGraph
import com.qolari.userlite.data.UserRepository
import com.qolari.userlite.net.Place
import com.qolari.userlite.net.SessionResponse
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch

data class AccountUiState(
    val session: SessionResponse? = null,
    val home: Place? = null,
    val places: List<Place> = emptyList(),
    val saving: Boolean = false,
    val error: String? = null,
    val signedOut: Boolean = false,
)

class AccountViewModel @JvmOverloads constructor(
    private val repository: UserRepository = AppGraph.repository,
) : ViewModel() {

    private val _state = MutableStateFlow(AccountUiState())
    val state: StateFlow<AccountUiState> = _state

    init {
        load()
    }

    fun load() {
        viewModelScope.launch {
            val session = repository.session().getOrNull() ?: _state.value.session
            val home = repository.home().getOrNull()?.savedPlace ?: _state.value.home
            val places = repository.places("").getOrNull().orEmpty()
            _state.value = _state.value.copy(session = session, home = home, places = places)
        }
    }

    fun saveAccount(firstName: String, lastName: String, email: String, done: (Boolean, String?) -> Unit) {
        if (_state.value.saving) return
        _state.value = _state.value.copy(saving = true, error = null)
        viewModelScope.launch {
            repository.updateAccount(firstName, lastName, email)
                .onSuccess {
                    _state.value = _state.value.copy(saving = false, session = it)
                    done(true, null)
                }
                .onFailure {
                    val message = com.qolari.userlite.net.ApiClient.errorMessage(it)
                    _state.value = _state.value.copy(saving = false, error = message)
                    done(false, message)
                }
        }
    }

    fun saveHome(placeId: String, done: (Place?) -> Unit) {
        if (_state.value.saving) return
        _state.value = _state.value.copy(saving = true, error = null)
        viewModelScope.launch {
            repository.setHome(placeId)
                .onSuccess {
                    _state.value = _state.value.copy(saving = false, home = it)
                    done(it)
                }
                .onFailure {
                    _state.value = _state.value.copy(
                        saving = false,
                        error = com.qolari.userlite.net.ApiClient.errorMessage(it),
                    )
                    done(null)
                }
        }
    }

    fun signOut() {
        viewModelScope.launch {
            repository.signOut()
            _state.value = _state.value.copy(signedOut = true)
        }
    }
}
