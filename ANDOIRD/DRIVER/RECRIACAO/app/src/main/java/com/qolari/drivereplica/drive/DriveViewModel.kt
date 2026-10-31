package com.qolari.drivereplica.drive

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.qolari.drivereplica.config.AppConfig
import com.qolari.drivereplica.data.AppGraph
import com.qolari.drivereplica.net.RouteResponse
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

/** Resultado de aceitar: ou já há viagem, ou (Radar) o toque entrou no emparelhamento. */
data class AcceptResult(val trip: ActiveTrip?, val radarPending: Boolean = false)

/** Operações do motorista durante a sessão online (implementado por [com.qolari.drivereplica.data.DriverRepository]). */
interface DriveSource {
    suspend fun offers(): Result<OfferCard?>
    suspend fun tasks(): Result<ActiveTrip?>
    suspend fun accept(offerUuid: String): Result<AcceptResult>
    suspend fun reject(offerUuid: String, expired: Boolean): Result<Unit>
    suspend fun arrive(tripUuid: String): Result<ActiveTrip?>
    suspend fun confirmPin(tripUuid: String): Result<Unit>
    suspend fun begin(tripUuid: String, pin: String?): Result<ActiveTrip?>
    suspend fun end(tripUuid: String): Result<Unit>
    suspend fun rate(tripUuid: String, stars: Int): Result<Unit>
    suspend fun summary(tripUuid: String): Result<TripSummary>
    suspend fun uploadPosition(latitude: Double, longitude: Double): Result<Unit>
    /** Chat da viagem: o servidor guarda e o passageiro vê (vídeo 2026-10-30). */
    suspend fun sendMessage(tripUuid: String, text: String): Result<Unit>
    /** Cancelamento com motivo escolhido pelo condutor (print de 2026-10-30). */
    suspend fun cancel(tripUuid: String, reason: String): Result<Unit>
    suspend fun route(fromLat: Double, fromLng: Double, toLat: Double, toLng: Double): Result<List<Pair<Double, Double>>>
    /** Rota com manobras: usada na navegação para a recolha (painel preto + limite). */
    suspend fun routeWithSteps(fromLat: Double, fromLng: Double, toLat: Double, toLng: Double): Result<RouteResponse?>
    /** Última posição que o servidor conhece do motorista (para navegar sem fix de GPS). */
    suspend fun lastPosition(): Pair<Double, Double>?

    /**
     * "Parar novos pedidos" / "Retomar pedidos": o motorista fica online mas fora do despacho.
     * Devolve o estado novo (true = parado).
     */
    suspend fun pauseDispatch(paused: Boolean): Result<Boolean>

    /** Modo Destino: marcar (lat/lng) ou desligar (nulos). */
    suspend fun setDestination(lat: Double?, lng: Double?, label: String): Result<DestinationMode>

    /** Modo Destino: estado atual (destino marcado + filtros que restam hoje). */
    suspend fun destinationState(): Result<DestinationMode>
}

enum class DriveStage { IDLE, OFFER, TO_PICKUP, AT_PICKUP, ON_TRIP, RATING }

/** Uma mensagem do chat da viagem (vídeo 2026-10-30). */
data class TripMessage(val text: String, val mine: Boolean)

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
    /** Radar: o motorista tocou e está à espera do emparelhamento ("A verificar…"). */
    val radarPending: Boolean = false,
    /** Modo Destino (lupa): destino marcado e filtros que restam hoje. */
    val destination: DestinationMode = DestinationMode(),
    /** Rota recolha -> destino da proposta, para desenhar no mapa. */
    val route: List<Pair<Double, Double>> = emptyList(),
    /** Navegação para a recolha (manobras, ETA e limite da via). */
    val navigation: NavigationInfo? = null,
    /** Chat com o passageiro (texto), mostrado no ecrã de contacto. */
    val messages: List<TripMessage> = emptyList(),
    /**
     * "Parar novos pedidos" (botão do planeador): true = online mas sem receber propostas.
     * O servidor manda este estado em `driverState.available`; a app só o espelha.
     */
    val paused: Boolean = false,
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

    fun setOnline(online: Boolean) {
        if (_state.value.online == online && (loop != null || !autoPoll) == online) return
        _state.update { if (online) it.copy(online = true) else DriveUiState() }
        loop?.cancel()
        loop = if (online && autoPoll) viewModelScope.launch {
            while (isActive) {
                pollOnce()
                delay(pollIntervalMs)
            }
        } else null
    }

    /** Última posição conhecida (GPS ou a que o servidor já tem), para a navegação não ficar vazia. */
    private var lastKnownPosition: Pair<Double, Double>? = null

    /** Uma ronda: posição, viagem ativa e (sem viagem) proposta. Público para os testes. */
    suspend fun pollOnce() {
        if (!_state.value.online) return
        // Modo Destino: mantém os filtros que restam atualizados (mudam à meia-noite e a cada
        // marcação). Vem do driverState, na mesma chamada que o tasks() já faz.
        source.destinationState().getOrNull()?.let { m ->
            _state.update { it.copy(destination = m) }
        }
        val here = location()
        here?.let { (lat, lng) ->
            lastKnownPosition = here
            source.uploadPosition(lat, lng)
        }
        val trip = source.tasks().getOrElse { return }
        if (trip != null) {
            applyTrip(trip)
            // Duas fases (vídeo 2026-10-30): navegação até à recolha e, já com o cliente a bordo,
            // navegação até ao destino. Cada uma pede a SUA rota.
            loadNavigation(trip, here)
            return
        }
        val offer = source.offers().getOrNull()
        val newRoute = if (offer != null && _state.value.offer?.uuid != offer.uuid) fetchRoute(offer) else null
        _state.update { s ->
            when {
                s.stage == DriveStage.RATING -> s
                offer != null -> s.copy(stage = DriveStage.OFFER, offer = offer, trip = null,
                    radarPending = if (s.offer?.uuid == offer.uuid) s.radarPending else false,
                    route = newRoute ?: if (s.offer?.uuid == offer.uuid) s.route else emptyList())
                else -> s.copy(stage = DriveStage.IDLE, offer = null, trip = null, radarPending = false)
            }
        }
    }

    /**
     * Navegação até à recolha: pede a rota com manobras ao servidor e guarda a manobra atual.
     * Repete só quando o motorista andou o suficiente, para não fazer um pedido por segundo.
     */
    private var navKey: String? = null

    private suspend fun loadNavigation(trip: ActiveTrip, here: Pair<Double, Double>?) {
        val to = if (trip.latitude != null && trip.longitude != null) trip.latitude to trip.longitude else return
        // Origem: GPS se houver. Sem fix (dentro de casa, GPS off) usa a ultima posicao conhecida:
        // a navegacao nao pode ficar vazia so por nao haver sinal neste instante.
        val from = here ?: lastKnownPosition ?: source.lastPosition() ?: return
        lastKnownPosition = from
        val key = "${trip.uuid}-${trip.phase}-${from.first.toString().take(5)},${from.second.toString().take(5)}"
        if (key == navKey) return
        navKey = key
        val resp = source.routeWithSteps(from.first, from.second, to.first, to.second).getOrNull() ?: return
        // Uma só perna por fase (decisão de 2026-10-30):
        //   fase 1 (a caminho do cliente) -> rota até à recolha;
        //   fase 2 (viagem a decorrer)    -> rota até ao destino.
        // O percurso completo (motorista -> cliente -> destino) só existe no cartão do pedido.
        val points = resp.polyline.orEmpty().mapNotNull { p ->
            if (p.latitude != null && p.longitude != null) p.latitude to p.longitude else null
        }
        val info = Navigation.build(
            resp.steps, from.first, from.second, resp.speedLimitKmh, resp.distanceMeters, resp.durationSeconds,
            stop = stopFor(trip),
        )
        _state.update { it.copy(route = points, navigation = info) }
    }

    /**
     * Paragem da 2.ª secção do painel (vídeo 2026-10-30): verde com a recolha enquanto se vai
     * buscar o passageiro, vermelha com o destino já em viagem.
     */
    private fun stopFor(trip: ActiveTrip): NavStop = when (trip.phase) {
        TripPhase.ON_TRIP -> navStop(trip.address, trip.city, "dropoff")
        else -> navStop(trip.pickupAddress.orEmpty().ifBlank { trip.address }, trip.city, "pickup")
    }

    /**
     * Separa a morada da cidade como no painel do vídeo ("Rua X" / "Amadora").
     * A morada do servidor já traz a cidade no fim ("Rua da Quinta Grande, Amadora"), pelo que
     * se aproveita essa parte em vez de mostrar a cidade da viagem (que pode ser outra).
     */
    private fun navStop(address: String, fallbackCity: String?, kind: String): NavStop {
        val clean = address.trim()
        val comma = clean.lastIndexOf(',')
        val tail = if (comma > 0) clean.substring(comma + 1).trim() else ""
        val street = if (comma > 0 && tail.length in 2..28) clean.substring(0, comma).trim() else clean
        val city = if (comma > 0 && tail.length in 2..28) tail else fallbackCity.orEmpty()
        return NavStop(street, city, kind)
    }

    /** Rota da proposta; sem coordenadas ou com falha, a proposta mostra-se na mesma sem traço. */
    private suspend fun fetchRoute(offer: OfferCard): List<Pair<Double, Double>>? {
        val a = offer.pickup ?: return null
        val b = offer.dropoff ?: return null
        // A rota do servidor é a perna cliente -> destino. Se falhar NÃO se inventa uma reta:
        // a regra do projeto proíbe desenhar rotas à mão, e uma linha reta entre a recolha e o
        // destino não corresponde a estrada nenhuma. O cartão mostra-se sem traço.
        return source.route(a.first, a.second, b.first, b.second).getOrNull()
            ?.takeIf { it.size > 1 }
    }

    private fun applyTrip(trip: ActiveTrip) = _state.update { s ->
        val stage = when (trip.phase) {
            TripPhase.TO_PICKUP -> DriveStage.TO_PICKUP
            TripPhase.AT_PICKUP -> DriveStage.AT_PICKUP
            TripPhase.ON_TRIP -> DriveStage.ON_TRIP
        }
        s.copy(stage = stage, trip = trip, offer = null, busy = false, pinVerified = s.pinVerified || trip.pin?.verified == true)
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
        // Radar: o toque entra no emparelhamento; o cartão fica bloqueado em "A verificar…".
        val radar = offer.kind == com.qolari.drivereplica.drive.OfferKind.RADAR
        if (radar) _state.update { it.copy(radarPending = true) }
        act {
            source.accept(offer.uuid)
                .onSuccess { r ->
                    when {
                        r.trip != null -> {
                            _state.update { it.copy(radarPending = false) }
                            applyTrip(r.trip)
                        }
                        // Radar: toque aceite, à espera do emparelhamento no servidor.
                        r.radarPending -> _state.update { it.copy(radarPending = true) }
                        else -> _state.update { it.copy(stage = DriveStage.IDLE, offer = null, radarPending = false) }
                    }
                }
                .onFailure {
                    failed()
                    _state.update { it.copy(stage = DriveStage.IDLE, offer = null, radarPending = false) }
                }
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


    /** Mensagem do condutor no chat da viagem (o passageiro vê-a na app dele). */
    fun sendMessage(text: String) {
        if (text.isBlank()) return
        _state.update { it.copy(messages = it.messages + TripMessage(text.trim(), mine = true)) }
        val trip = _state.value.trip ?: return
        viewModelScope.launch { source.sendMessage(trip.uuid, text.trim()) }
    }

    /** Cancelamento com motivo (lista do print de 2026-10-30). */
    fun cancelForReason(reason: String) {
        val trip = _state.value.trip ?: return
        viewModelScope.launch {
            source.cancel(trip.uuid, reason)
            // Limpa tudo da viagem: sem isto o traço e o painel ficavam no mapa depois de cancelar.
            navKey = null
            lastKnownPosition = null
            _state.update { DriveUiState(online = it.online) }
        }
    }

    /**
     * "Parar novos pedidos" / "Retomar pedidos" (botao do planeador de viagem).
     * Continua online - so sai do despacho. O estado que fica no ecra e o que o servidor
     * devolveu, nao o que se pediu: se a chamada falhar, o botao nao mente.
     */
    fun setPaused(paused: Boolean) {
        if (_state.value.busy) return
        _state.update { it.copy(busy = true) }
        viewModelScope.launch {
            source.pauseDispatch(paused)
                .onSuccess { stopped -> _state.update { it.copy(paused = stopped, busy = false) } }
                .onFailure {
                    failed()
                    _state.update { it.copy(busy = false) }
                }
        }
    }

    /**
     * Modo Destino (lupa): marcar para onde quer ir, ou desligar com lat/lng nulos.
     * O estado que fica no ecrã é o que o servidor devolveu (inclui os filtros que restam),
     * para o ecrã nunca mentir sobre quantos ainda tem.
     */
    fun setDestination(lat: Double?, lng: Double?, label: String) {
        if (_state.value.busy) return
        _state.update { it.copy(busy = true) }
        viewModelScope.launch {
            source.setDestination(lat, lng, label)
                .onSuccess { m ->
                    _state.update { it.copy(destination = m, busy = false) }
                    if (m.enabled) pollOnce()   // o filtro muda já os pedidos que chegam
                }
                .onFailure {
                    failed()
                    _state.update { it.copy(busy = false) }
                }
        }
    }

    companion object {
        val Factory = object : ViewModelProvider.Factory {
            @Suppress("UNCHECKED_CAST")
            override fun <T : ViewModel> create(modelClass: Class<T>): T = DriveViewModel(AppGraph.repository, AppGraph.location::lastKnown) as T
        }
    }
}
