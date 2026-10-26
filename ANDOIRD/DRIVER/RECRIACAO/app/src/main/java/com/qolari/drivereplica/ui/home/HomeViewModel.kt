package com.qolari.drivereplica.ui.home

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.qolari.drivereplica.data.AppGraph
import com.qolari.drivereplica.data.Blocker
import com.qolari.drivereplica.data.HomeSnapshot
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

/** O que o painel inicial pede ao servidor (implementado por [com.qolari.drivereplica.data.DriverRepository]). */
interface HomeSource {
    suspend fun fetchHome(): Result<HomeSnapshot>
    suspend fun goOnline(): Result<Boolean>
    suspend fun goOffline(): Result<Boolean>
}

data class HomeUiState(
    val online: Boolean = false,
    val blockers: List<Blocker> = emptyList(),
    val refreshing: Boolean = false,
    /** Já houve uma resposta do servidor. Sem ela e com falha, o ecrã mostra "Ocorreu um erro" (capturas 117/120). */
    val loaded: Boolean = false,
    val failed: Boolean = false,
) {
    val blocked: Boolean get() = blockers.isNotEmpty()
}

/** Avisos únicos: a janela "Erro" (capturas 115/125) abre-se uma vez por falha. */
enum class HomeEvent { REFRESH_FAILED, ACTION_FAILED }

/**
 * Painel inicial e mapa partilham este estado. Regras observadas na original (ux_behavior.md §4):
 * - arranque sem rede: sem janela, o ecrã mostra o estado de erro com "Tente novamente";
 * - puxar para atualizar sem rede com dados já carregados: janela "Erro" com "Tentar novamente";
 * - ficar online com ações necessárias por resolver: não avança, volta a verificar.
 */
class HomeViewModel(private val source: HomeSource) : ViewModel() {

    private val _state = MutableStateFlow(HomeUiState())
    val state: StateFlow<HomeUiState> = _state.asStateFlow()

    private val _events = MutableSharedFlow<HomeEvent>(extraBufferCapacity = 1)
    val events: SharedFlow<HomeEvent> = _events.asSharedFlow()

    init {
        refresh(userInitiated = false)
    }

    fun refresh(userInitiated: Boolean = true) {
        viewModelScope.launch {
            _state.update { it.copy(refreshing = true) }
            source.fetchHome()
                .onSuccess { s ->
                    _state.value = HomeUiState(online = s.online, blockers = s.blockers, loaded = true)
                }
                .onFailure {
                    val loadedBefore = _state.value.loaded
                    _state.update { it.copy(refreshing = false, failed = true) }
                    if (userInitiated && loadedBefore) _events.tryEmit(HomeEvent.REFRESH_FAILED)
                }
        }
    }

    fun toggleOnline() {
        val s = _state.value
        if (!s.loaded || s.refreshing) return
        if (s.blocked) {
            refresh(userInitiated = true)
            return
        }
        viewModelScope.launch {
            val result = if (s.online) source.goOffline() else source.goOnline()
            result
                .onSuccess { online -> _state.update { it.copy(online = online) } }
                .onFailure { _events.tryEmit(HomeEvent.ACTION_FAILED) }
        }
    }

    companion object {
        val Factory = object : ViewModelProvider.Factory {
            @Suppress("UNCHECKED_CAST")
            override fun <T : ViewModel> create(modelClass: Class<T>): T = HomeViewModel(AppGraph.repository) as T
        }
    }
}
