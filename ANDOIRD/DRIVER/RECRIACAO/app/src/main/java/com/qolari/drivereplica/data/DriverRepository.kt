package com.qolari.drivereplica.data

import com.google.gson.JsonArray
import com.google.gson.JsonObject
import com.qolari.drivereplica.drive.AcceptResult
import com.qolari.drivereplica.drive.ActiveTrip
import com.qolari.drivereplica.drive.DriveParser
import com.qolari.drivereplica.drive.DriveSource
import com.qolari.drivereplica.drive.OfferCard
import com.qolari.drivereplica.drive.TripSummary
import com.qolari.drivereplica.net.ApiClient
import com.qolari.drivereplica.net.DriverApi
import com.qolari.drivereplica.net.RouteResponse
import com.qolari.drivereplica.ui.earnings.EarningsMapper
import com.qolari.drivereplica.ui.earnings.EarningsSource
import com.qolari.drivereplica.ui.earnings.WeeklyEarnings
import com.qolari.drivereplica.ui.home.HomeSource

/** Um motivo que impede de ficar online ("Ações necessárias" na captura 060). */
data class Blocker(val title: String, val message: String?)

/** O que o painel inicial precisa do servidor: estado online e bloqueios. */
data class HomeSnapshot(val online: Boolean, val blockers: List<Blocker>)

/**
 * Único ponto de acesso à API do motorista. Devolve [Result] em vez de lançar: os ecrãs decidem como mostrar o erro
 * (banner, janela "Erro" ou estado vazio, ver ux_behavior.md §4). O token é lido da sessão local em cada chamada.
 */
class DriverRepository(private val session: SessionStore) : HomeSource, EarningsSource, DriveSource {

    @Volatile private var token: String? = null
    private var api: DriverApi? = null
    private var apiUrl: String? = null

    private suspend fun api(): DriverApi {
        val s = session.current()
        token = s.token
        if (api == null || apiUrl != s.baseUrl) {
            api = ApiClient.create(s.baseUrl) { token }
            apiUrl = s.baseUrl
        }
        return api!!
    }

    suspend fun hasSession(): Boolean = session.current().token != null

    /** Entrar com telefone e código recebido por mensagem (no laboratório o código é fixo no backend). */
    suspend fun login(phone: String, code: String): Result<Unit> = runCatching {
        val r = api().token(mapOf("grant_type" to "password", "username" to phone, "password" to code))
        val access = r.token ?: error("Resposta sem token")
        session.saveSession(access, r.refreshToken, phone)
        token = access
    }

    override suspend fun fetchHome(): Result<HomeSnapshot> = runCatching {
        val api = api()
        val online = api.appLaunch().driverTasks?.driverState?.online == true
        val issues = api.blockers().issues.orEmpty().map { Blocker(it.title.orEmpty(), it.message) }
        HomeSnapshot(online, issues)
    }

    override suspend fun goOnline(): Result<Boolean> = runCatching { api().goOnline().driverTasks?.driverState?.online == true }

    override suspend fun goOffline(): Result<Boolean> = runCatching { api().goOffline().driverTasks?.driverState?.online == true }

    /** Semana atual (ganhos e viagens) mais o saldo; o saldo é opcional: se falhar, o resumo mostra-se na mesma. */
    override suspend fun fetchWeek(): Result<WeeklyEarnings> = runCatching {
        val api = api()
        val view = api.weeklyEarnings()
        val balance = runCatching { api.balanceSummary() }.getOrNull()
        EarningsMapper.map(view, balance)
    }

    // ---- proposta e viagem (lote 4) ----

    override suspend fun offers(): Result<OfferCard?> = runCatching { DriveParser.offer(api().unifiedOffers()) }

    override suspend fun tasks(): Result<ActiveTrip?> = runCatching { DriveParser.trip(api().available().driverTasks) }

    private fun uuids(vararg ids: String) = JsonObject().apply { add("offerUUIDs", JsonArray().apply { ids.forEach { add(it) } }) }

    private fun tripBody(uuid: String, pin: String? = null) = JsonObject().apply {
        addProperty("uuid", uuid)
        pin?.let { addProperty("pin", it) }
    }

    override suspend fun accept(offerUuid: String): Result<AcceptResult> = runCatching {
        val r = api().acceptOffers(uuids(offerUuid))
        AcceptResult(DriveParser.trip(r.driverTasks), radarPending = r.radarPending == true)
    }

    override suspend fun reject(offerUuid: String, expired: Boolean): Result<Unit> = runCatching {
        if (expired) api().expireOffers(uuids(offerUuid)) else api().rejectOffers(uuids(offerUuid))
        Unit
    }

    override suspend fun arrive(tripUuid: String): Result<ActiveTrip?> =
        runCatching { DriveParser.trip(api().startWaiting(tripBody(tripUuid)).driverTasks) }

    override suspend fun confirmPin(tripUuid: String): Result<Unit> = runCatching { api().confirmPin(tripBody(tripUuid)); Unit }

    override suspend fun begin(tripUuid: String, pin: String?): Result<ActiveTrip?> =
        runCatching { DriveParser.trip(api().beginTrip(tripBody(tripUuid, pin)).driverTasks) }

    override suspend fun end(tripUuid: String): Result<Unit> = runCatching { api().endTrip(tripBody(tripUuid)); Unit }

    override suspend fun rate(tripUuid: String, stars: Int): Result<Unit> = runCatching {
        api().driverRate(JsonObject().apply { addProperty("uuid", tripUuid); addProperty("rating", stars) })
        Unit
    }

    override suspend fun summary(tripUuid: String): Result<TripSummary> =
        runCatching { DriveParser.summary(tripUuid, api().earningsTrip(tripBody(tripUuid))) }

    override suspend fun uploadPosition(latitude: Double, longitude: Double): Result<Unit> = runCatching {
        val loc = JsonObject().apply { addProperty("latitude", latitude); addProperty("longitude", longitude) }
        api().uploadPositions(JsonObject().apply {
            add("uploadLocationRequest", JsonObject().apply { add("locations", JsonArray().apply { add(loc) }) })
        })
        Unit
    }

    /** Chat da viagem: entra como mensagem do condutor (TripEvent no servidor). */
    override suspend fun sendMessage(tripUuid: String, text: String): Result<Unit> = runCatching {
        api().tripMessage(JsonObject().apply {
            addProperty("uuid", tripUuid)
            addProperty("message", text)
            addProperty("sender", "driver")
        })
        Unit
    }

    /** Cancelamento do condutor com o motivo escolhido na lista. */
    override suspend fun cancel(tripUuid: String, reason: String): Result<Unit> = runCatching {
        api().driverCancelTrip(JsonObject().apply {
            addProperty("uuid", tripUuid)
            addProperty("reason", reason)
        })
        Unit
    }

    // ---- Veículos e Documentos (lote 5) ----

    suspend fun vehicles(): Result<List<com.qolari.drivereplica.ui.manage.VehicleItem>> =
        runCatching { com.qolari.drivereplica.ui.manage.ManageMapper.vehicles(api().vehicles()) }

    suspend fun documents(): Result<List<com.qolari.drivereplica.ui.manage.DocumentItem>> =
        runCatching { com.qolari.drivereplica.ui.manage.ManageMapper.documents(api().documents()) }

    suspend fun profile(): Result<com.qolari.drivereplica.ui.manage.ProfileSummary?> =
        runCatching { com.qolari.drivereplica.ui.manage.ManageMapper.profile(api().profileHub()) }

    /** Notificações da Caixa de entrada; atualiza o contador da barra. */
    val unread = kotlinx.coroutines.flow.MutableStateFlow(0)

    suspend fun notifications(): Result<List<com.qolari.drivereplica.ui.inbox.InboxItem>> = runCatching {
        val r = api().notifications()
        unread.value = r.unreadCount ?: 0
        com.qolari.drivereplica.ui.inbox.InboxMapper.items(r)
    }

    suspend fun markNotificationsRead(): Result<Unit> = runCatching { api().markRead(); unread.value = 0; Unit }

    override suspend fun route(fromLat: Double, fromLng: Double, toLat: Double, toLng: Double): Result<List<Pair<Double, Double>>> = runCatching {
        api().route(body(fromLat, fromLng, toLat, toLng)).polyline.orEmpty().mapNotNull { p ->
            if (p.latitude != null && p.longitude != null) p.latitude to p.longitude else null
        }
    }

    override suspend fun routeWithSteps(
        fromLat: Double, fromLng: Double, toLat: Double, toLng: Double,
    ): Result<RouteResponse?> = runCatching { api().route(body(fromLat, fromLng, toLat, toLng)) }

    /**
     * Última posição do motorista conhecida pelo servidor (`driverState.location`).
     * Serve para a navegação arrancar quando o telemóvel está sem fix de GPS.
     */
    override suspend fun lastPosition(): Pair<Double, Double>? = runCatching {
        val loc = api().available().driverTasks?.driverState?.location
        val lat = loc?.latitude
        val lng = loc?.longitude
        if (lat != null && lng != null) lat to lng else null
    }.getOrNull()

    /**
     * "Parar novos pedidos": o servidor mantém o motorista online (sessão aberta) mas com
     * `available = false`, o que o tira do despacho. Devolve o estado novo (true = parado).
     */
    override suspend fun pauseDispatch(paused: Boolean): Result<Boolean> = runCatching {
        val body = JsonObject().apply { addProperty("paused", paused) }
        val st = api().pauseDispatch(body).driverTasks?.driverState
        // online + available=false  => parado; online + available=true => a receber pedidos.
        st != null && st.online == true && st.available == false
    }

    private fun body(fromLat: Double, fromLng: Double, toLat: Double, toLng: Double) = JsonObject().apply {
        fun pt(lat: Double, lng: Double) = JsonObject().apply { addProperty("latitude", lat); addProperty("longitude", lng) }
        add("origin", pt(fromLat, fromLng))
        add("destination", pt(toLat, toLng))
    }

    suspend fun signOut() = session.clear()
}
