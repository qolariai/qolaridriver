package com.qolari.userlite.ui.search

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.qolari.userlite.data.AppGraph
import com.qolari.userlite.data.UserRepository
import com.qolari.userlite.net.Place
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch

data class SearchUiState(
    val places: List<Place> = emptyList(),
    val loading: Boolean = false,
    val error: String? = null,
)

class SearchViewModel @JvmOverloads constructor(
    private val repository: UserRepository = AppGraph.repository,
) : ViewModel() {

    private val _state = MutableStateFlow(SearchUiState())
    val state: StateFlow<SearchUiState> = _state

    private val _savedPlace = MutableStateFlow<Place?>(null)
    val savedPlace: StateFlow<Place?> = _savedPlace

    init {
        viewModelScope.launch {
            repository.home().onSuccess { _savedPlace.value = it.savedPlace }
        }
    }
    private var job: Job? = null

    fun search(query: String) {
        job?.cancel()
        job = viewModelScope.launch {
            _state.value = _state.value.copy(loading = true, error = null)
            delay(if (query.isBlank()) 0 else 220)
            repository.places(query)
                .onSuccess { _state.value = SearchUiState(places = it) }
                .onFailure {
                    _state.value = SearchUiState(
                        error = com.qolari.userlite.net.ApiClient.errorMessage(it),
                    )
                }
        }
    }
}
