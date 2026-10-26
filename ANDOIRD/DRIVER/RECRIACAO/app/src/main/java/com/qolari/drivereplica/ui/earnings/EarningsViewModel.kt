package com.qolari.drivereplica.ui.earnings

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.qolari.drivereplica.data.AppGraph
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

interface EarningsSource {
    suspend fun fetchWeek(): Result<WeeklyEarnings>
}

data class EarningsUiState(
    val week: WeeklyEarnings? = null,
    val refreshing: Boolean = false,
    /** Falhou e não há dados: mostra "Sem ligação de rede" (captura 122). */
    val failed: Boolean = false,
)

/**
 * Rendimentos: ao falhar com dados já carregados mantém o que tinha, sem janela nem alteração visível (capturas 116/126:
 * arrastar para atualizar offline não muda nada); sem dados mostra o texto de falta de rede.
 */
class EarningsViewModel(private val source: EarningsSource) : ViewModel() {

    private val _state = MutableStateFlow(EarningsUiState())
    val state: StateFlow<EarningsUiState> = _state.asStateFlow()

    init { refresh() }

    fun refresh() {
        viewModelScope.launch {
            _state.update { it.copy(refreshing = true) }
            source.fetchWeek()
                .onSuccess { w -> _state.value = EarningsUiState(week = w) }
                .onFailure { _state.update { s -> s.copy(refreshing = false, failed = s.week == null) } }
        }
    }

    companion object {
        val Factory = object : ViewModelProvider.Factory {
            @Suppress("UNCHECKED_CAST")
            override fun <T : ViewModel> create(modelClass: Class<T>): T = EarningsViewModel(AppGraph.repository) as T
        }
    }
}
