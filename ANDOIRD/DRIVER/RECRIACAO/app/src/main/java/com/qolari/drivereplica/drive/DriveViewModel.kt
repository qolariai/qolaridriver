package com.qolari.drivereplica.drive

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.qolari.drivereplica.config.AppConfig
import com.qolari.drivereplica.data.AppGraph
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch

/** Operações do motorista durante a sessão online (implementado por [com.qolari.drivereplica.data.DriverRepository]). */
interface DriveSource {
    suspend fun offers(): Result<OfferCard?>
    suspend fun tasks(): Result<ActiveTrip?>
    suspend fun accept(offerUuid: String): Result<ActiveTrip?>
    suspend fun reject(offerUuid: String, expired: Boolean): Result<Unit>
    suspend fun arrive(tripUuid: String): Result<ActiveTrip?>
    suspend fun confirmPin(tripUuid: String): Result<Unit>
    suspend fun begin(tripUuid: String, pin: String?): Result<ActiveTrip?>
    suspend fun completeStop(tripUuid: String): Result<ActiveTrip?>
    suspend fun end(tripUuid: String): Result<Unit>
    suspend fun rate(tripUuid: String, stars: Int): Result<Unit>
    suspend fun summary(tripUuid: String): Result<TripSummary>
    suspend fun uploadPosition(latitude: Double, longitude: Double): Result<Unit>
    suspend fun route(fromLat: Double, fromLng: Double, toLat: Double, toLng: Double): Result<List<Pair<Double, Double>>>
}

enum class DriveStage { IDLE, OFFER, TO_PICKUP, AT_PICKUP, ON_TRIP, RATING }

data class DriveUiState(
    val online: Boolean = false,
    val stage: DriveStage = DriveStage.IDLE,
    val offer: OfferCard? = null,
    val trip: ActiveTrip? = null,
    val summary: TripSummary? = null,
    val busy: Boolean = false,
    val pinAttempts: Int = 0,
    val pinError: String? = null,
    val pinVerified: Boolean = false,
    /** Rota recolha -> destino da proposta, para desenhar no mapa. */
    val route: List<Pair<Double, Double>> = emptyList(),
)

/** Avisos únicos para o ecrã (a janela "Erro" já existe no lote 2). */
enum class DriveEvent { ACTION_FAILED }

/**
 * Ciclo da proposta e da viagem, por sondagem ao servidor a cada [AppConfig.OFFER_POLL_INTERVAL_MS]:
 * proposta -> aceitar -> recolher (chegar, PIN) -> iniciar -> deixar -> terminar -> avaliar.
 * As tarefas do servidor mandam: o estado do ecrã deriva das DriverTasks e não de contagens locais, por isso uma
 * viagem em curso volta a aparecer depois de reabrir a app. O PIN compara-se localmente (como a original) e depois
 * avisa o servidor com confirm-pin-is-verified.
 */
class DriveViewModel(
    private val source: DriveSource,
    private val location: () -> Pair<Double, Double>? = { null },
    private val pollIntervalMs: Long = AppConfig.OFFER_POLL_INTERVAL_MS,
    /** Desligado nos testes: a sondagem em ciclo avançava o tempo virtual sem fim. */
    private val autoPoll: Boolean = true,
) : ViewModel() {

    private val _state = MutableStateFlow(DriveUiState())
    val state: StateFlow<DriveUiState> = _state.asStateFlow()

    private val _events = MutableSharedFlow<DriveEvent>(extraBufferCapacity = 1)
    val events: SharedFlow<DriveEvent> = _events.asSharedFlow()

    private var loop: Job? = null
    private var routeKey: String? = null
    private var lastRouteAt: Long = 0
    private var lastRouteOrigin: Pair<Double, Double>? = null

    fun setOnline(online: Boolean) {
        if (_state.value.online == online && (loop != null || !autoPoll) == online) return
        if (!online) {
            routeKey = null
            lastRouteAt = 0
            lastRouteOrigin = null
        }
        _state.update { if (online) it.copy(online = true) else DriveUiState() }
        loop?.cancel()
        loop = if (online && autoPoll) viewModelScope.launch {
            while (isActive) {
                pollOnce()
                delay(pollIntervalMs)
            }
        } else null
    }

    /** Uma ronda: posição, viagem ativa e (sem viagem) proposta. Público para os testes. */
    suspend fun pollOnce() {
        if (!_state.value.online) return
        location()?.let { (lat, lng) -> source.uploadPosition(lat, lng) }
        val trip = source.tasks().getOrElse { return }
        if (trip != null) {
            applyTrip(trip)
            return
        }
        val offer = source.offers().getOrNull()
        val newRoute = if (offer != null && _state.value.offer?.uuid != offer.uuid) fetchRoute(offer) else null
        _state.update { s ->
            when {
                s.stage == DriveStage.RATING -> s
                offer != null -> s.copy(stage = DriveStage.OFFER, offer = offer, trip = null, route = newRoute ?: if (s.offer?.uuid == offer.uuid) s.route else emptyList())
                else -> s.copy(stage = DriveStage.IDLE, offer = null, trip = null)
            }
        }
    }

    /** Rota da proposta; sem coordenadas ou com falha, a proposta mostra-se na mesma sem traço. */
    private suspend fun fetchRoute(offer: OfferCard): List<Pair<Double, Double>>? {
        val a = offer.pickup ?: return null
        val b = offer.dropoff ?: return null
        return source.route(a.first, a.second, b.first, b.second).getOrNull()
    }

    private fun applyTrip(trip: ActiveTrip) {
        _state.update { s ->
            val stage = when (trip.phase) {
                TripPhase.TO_PICKUP -> DriveStage.TO_PICKUP
                TripPhase.AT_PICKUP -> DriveStage.AT_PICKUP
                TripPhase.ON_TRIP -> DriveStage.ON_TRIP
            }
            s.copy(stage = stage, trip = trip, offer = null, busy = false, pinVerified = s.pinVerified || trip.pin?.verified == true)
        }
        // Rota real até ao ponto da viagem (recolha ou destino). Refresca com o movimento
        // do motorista (>=100 m) ou a cada 15 s, não só na mudança de fase.
        val from = location()
        val target = if (trip.latitude != null && trip.longitude != null) trip.latitude to trip.longitude else null
        val key = "${trip.uuid}:${trip.phase}"
        val nowMs = System.currentTimeMillis()
        val moved = lastRouteOrigin?.let { meters(it, from) > 100.0 } ?: true
        val stale = nowMs - lastRouteAt >= ROUTE_REFRESH_MS
        if (from != null && target != null && (routeKey != key || moved || stale)) {
            routeKey = key
            lastRouteAt = nowMs
            lastRouteOrigin = from
            viewModelScope.launch {
                source.route(from.first, from.second, target.first, target.second)
                    .onSuccess { points -> _state.update { it.copy(route = points) } }
            }
        }
    }

    private fun meters(a: Pair<Double, Double>, b: Pair<Double, Double>?): Double {
        if (b == null) return Double.MAX_VALUE
        val dLat = (a.first - b.first) * 111_320.0
        val dLng = (a.second - b.second) * 111_320.0 * kotlin.math.cos(Math.toRadians(a.first))
        return kotlin.math.sqrt(dLat * dLat + dLng * dLng)
    }

    private fun act(block: suspend () -> Unit) {
        if (_state.value.busy) return
        _state.update { it.copy(busy = true) }
        viewModelScope.launch {
            block()
            _state.update { it.copy(busy = false) }
        }
    }

    private fun failed() { _events.tryEmit(DriveEvent.ACTION_FAILED) }

    fun accept() {
        val offer = _state.value.offer ?: return
        act {
            source.accept(offer.uuid)
                .onSuccess { trip -> if (trip != null) applyTrip(trip) else _state.update { it.copy(stage = DriveStage.IDLE, offer = null) } }
                .onFailure { failed(); _state.update { it.copy(stage = DriveStage.IDLE, offer = null) } }
        }
    }

    fun decline() = dismissOffer(expired = false)

    /** O tempo da proposta acabou no ecrã (expire-offers). */
    fun expire() = dismissOffer(expired = true)

    private fun dismissOffer(expired: Boolean) {
        val offer = _state.value.offer ?: return
        _state.update { it.copy(stage = DriveStage.IDLE, offer = null) }
        viewModelScope.launch { source.reject(offer.uuid, expired) }
    }

    fun arrive() {
        val trip = _state.value.trip ?: return
        act { source.arrive(trip.uuid).onSuccess { t -> if (t != null) applyTrip(t) }.onFailure { failed() } }
    }

    fun completeStop() {
        val trip = _state.value.trip ?: return
        act {
            source.completeStop(trip.uuid)
                .onSuccess { t -> if (t != null) applyTrip(t) }
                .onFailure { failed() }
        }
    }

    /** Compara com o PIN do servidor; certo = avisa o servidor; errado = mostra o texto da tentativa. */
    fun submitPin(code: String) {
        val s = _state.value
        val trip = s.trip ?: return
        val pin = trip.pin ?: return
        if (s.pinVerified || s.pinAttempts >= pin.maxAttempts) return
        if (code == pin.pin) {
            act {
                source.confirmPin(trip.uuid)
                    .onSuccess { _state.update { it.copy(pinVerified = true, pinError = null) } }
                    .onFailure { failed() }
            }
        } else {
            val attempt = s.pinAttempts + 1
            val message = pin.errors.getOrNull(attempt - 1) ?: pin.errors.lastOrNull() ?: ""
            _state.update { it.copy(pinAttempts = attempt, pinError = message) }
        }
    }

    /** "Recolher": só avança com o PIN verificado, se a viagem o pedir. */
    fun startTrip() {
        val s = _state.value
        val trip = s.trip ?: return
        if (trip.pin != null && !s.pinVerified) return
        act { source.begin(trip.uuid, trip.pin?.pin).onSuccess { t -> if (t != null) applyTrip(t) }.onFailure { failed() } }
    }

    /** "Terminar": acaba a viagem e passa à avaliação com o resumo dos ganhos. */
    fun finishTrip() {
        val trip = _state.value.trip ?: return
        act {
            source.end(trip.uuid)
                .onSuccess {
                    val summary = source.summary(trip.uuid).getOrNull()
                    _state.update { it.copy(stage = DriveStage.RATING, summary = summary, trip = null, pinAttempts = 0, pinError = null, pinVerified = false) }
                }
                .onFailure { failed() }
        }
    }

    fun rate(stars: Int) {
        val summary = _state.value.summary
        _state.update { it.copy(stage = DriveStage.IDLE, summary = null) }
        if (summary != null && stars in 1..5) viewModelScope.launch { source.rate(summary.tripUuid, stars) }
    }

    fun skipRating() = rate(0)

    companion object {
        private const val ROUTE_REFRESH_MS = 15_000L

        val Factory = object : ViewModelProvider.Factory {
            @Suppress("UNCHECKED_CAST")
            override fun <T : ViewModel> create(modelClass: Class<T>): T = DriveViewModel(AppGraph.repository, AppGraph.location::lastKnown) as T
        }
    }
}
