package com.qolari.drivereplica.data

import com.google.gson.JsonArray
import com.google.gson.JsonObject
import com.qolari.drivereplica.drive.ActiveTrip
import com.qolari.drivereplica.drive.DriveParser
import com.qolari.drivereplica.drive.DriveSource
import com.qolari.drivereplica.drive.OfferCard
import com.qolari.drivereplica.drive.TripSummary
import com.qolari.drivereplica.net.ApiClient
import com.qolari.drivereplica.net.DriverApi
import com.qolari.drivereplica.net.PlaceResult
import com.qolari.drivereplica.net.SupportThreadDto
import com.qolari.drivereplica.net.SupportThreadResponse
import com.qolari.drivereplica.net.AirportQueueResponse
import com.qolari.drivereplica.net.IncentivesResponse
import com.qolari.drivereplica.net.InvoiceRow
import com.qolari.drivereplica.net.SafetyContact
import com.qolari.drivereplica.net.TaxInfo
import com.qolari.drivereplica.net.SafetyShareResponse
import com.qolari.drivereplica.net.ScreenShareDto
import com.qolari.drivereplica.net.DriverBusiness
import com.qolari.drivereplica.net.DriverPreferences
import com.qolari.drivereplica.net.PayoutDto
import com.qolari.drivereplica.net.PayoutMethodsResponse
import com.qolari.drivereplica.net.PayoutResponse
import com.qolari.drivereplica.net.StatementRow
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

    override suspend fun accept(offerUuid: String): Result<ActiveTrip?> =
        runCatching { DriveParser.trip(api().acceptOffers(uuids(offerUuid)).driverTasks) }

    override suspend fun reject(offerUuid: String, expired: Boolean): Result<Unit> = runCatching {
        if (expired) api().expireOffers(uuids(offerUuid)) else api().rejectOffers(uuids(offerUuid))
        Unit
    }

    override suspend fun arrive(tripUuid: String): Result<ActiveTrip?> =
        runCatching { DriveParser.trip(api().startWaiting(tripBody(tripUuid)).driverTasks) }

    override suspend fun confirmPin(tripUuid: String): Result<Unit> = runCatching { api().confirmPin(tripBody(tripUuid)); Unit }

    override suspend fun begin(tripUuid: String, pin: String?): Result<ActiveTrip?> =
        runCatching { DriveParser.trip(api().beginTrip(tripBody(tripUuid, pin)).driverTasks) }

    override suspend fun completeStop(tripUuid: String): Result<ActiveTrip?> =
        runCatching { DriveParser.trip(api().completeStop(tripBody(tripUuid)).driverTasks) }

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

    // ---- Veículos e Documentos (lote 5) ----

    suspend fun vehicles(): Result<List<com.qolari.drivereplica.ui.manage.VehicleItem>> =
        runCatching { com.qolari.drivereplica.ui.manage.ManageMapper.vehicles(api().vehicles()) }

    suspend fun documents(): Result<List<com.qolari.drivereplica.ui.manage.DocumentItem>> =
        runCatching { com.qolari.drivereplica.ui.manage.ManageMapper.documents(api().documents()) }

    suspend fun uploadDocument(kind: String, fileName: String, contentBase64: String): Result<Unit> = runCatching {
        api().uploadDocument(JsonObject().apply {
            addProperty("kind", kind)
            addProperty("fileName", fileName)
            addProperty("contentBase64", contentBase64)
        })
        Unit
    }

    suspend fun verifyIdentity(fileName: String, contentBase64: String): Result<Unit> = runCatching {
        api().verifyIdentity(JsonObject().apply {
            addProperty("fileName", fileName)
            addProperty("contentBase64", contentBase64)
        })
        Unit
    }

    suspend fun preferences(): Result<DriverPreferences> = runCatching {
        api().preferences().preferences
    }

    suspend fun savePreferences(body: JsonObject): Result<DriverPreferences> = runCatching {
        api().savePreferences(body).preferences
    }

    suspend fun setBreak(minutes: Int, resume: Boolean): Result<DriverPreferences> = runCatching {
        api().setBreak(JsonObject().apply {
            addProperty("minutes", minutes)
            addProperty("resume", resume)
        }).preferences
    }

    suspend fun airportQueue(): Result<AirportQueueResponse> = runCatching {
        api().airportQueue()
    }

    suspend fun airportQueueAction(action: String): Result<AirportQueueResponse> = runCatching {
        api().airportQueueAction(JsonObject().apply { addProperty("action", action) })
    }

    suspend fun incentives(): Result<IncentivesResponse> = runCatching { api().incentives() }

    suspend fun claimQuest(uuid: String): Result<IncentivesResponse> = runCatching {
        api().claimQuest(uuid)
    }

    suspend fun inviteDriver(phone: String): Result<IncentivesResponse> = runCatching {
        api().invite(JsonObject().apply { addProperty("phone", phone) })
    }

    suspend fun requestAdjustment(kind: String, amountCents: Int, note: String): Result<Unit> = runCatching {
        api().requestAdjustment(JsonObject().apply {
            addProperty("kind", kind)
            addProperty("amountCents", amountCents)
            addProperty("note", note)
        })
        Unit
    }

    suspend fun invoices(): Result<List<InvoiceRow>> = runCatching { api().invoices().invoices }

    suspend fun taxSummary(): Result<TaxInfo> = runCatching { api().taxSummary() }

    suspend fun businessProfile(): Result<DriverBusiness> = runCatching {
        api().businessProfile().business
    }

    suspend fun saveBusinessProfile(body: JsonObject): Result<DriverBusiness> = runCatching {
        api().saveBusinessProfile(body).business
    }

    suspend fun payoutMethods(): Result<PayoutMethodsResponse> = runCatching {
        api().payoutMethods()
    }

    suspend fun requestPayout(instant: Boolean): Result<PayoutResponse> = runCatching {
        if (instant) api().instantPay() else api().requestPayout()
    }

    suspend fun payoutHistory(): Result<List<PayoutDto>> = runCatching {
        api().payoutHistory().payouts
    }

    suspend fun statements(): Result<List<StatementRow>> = runCatching {
        api().statements().statements
    }

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
        fun pt(lat: Double, lng: Double) = JsonObject().apply { addProperty("latitude", lat); addProperty("longitude", lng) }
        val body = JsonObject().apply { add("origin", pt(fromLat, fromLng)); add("destination", pt(toLat, toLng)) }
        api().route(body).polyline.orEmpty().mapNotNull { p -> if (p.latitude != null && p.longitude != null) p.latitude to p.longitude else null }
    }

    suspend fun signOut() = session.clear()

    /** Pesquisa de locais (Google Geocoding no backend; fallback no seed). */
    suspend fun searchPlaces(query: String, lat: Double?, lng: Double?): Result<List<PlaceResult>> =
        runCatching { api().searchPlaces(query, lat, lng).places }

    suspend fun registerPushToken(token: String): Result<Unit> = runCatching {
        api().pushToken(JsonObject().apply { addProperty("token", token) })
        Unit
    }

    suspend fun supportThreads(): Result<List<SupportThreadDto>> =
        runCatching { api().supportThreads().threads }

    suspend fun supportThread(uuid: String): Result<SupportThreadResponse> =
        runCatching { api().supportThread(uuid) }

    suspend fun createSupportThread(
        message: String,
        category: String = "outro",
        fileName: String? = null,
        contentBase64: String? = null,
    ): Result<SupportThreadResponse> = runCatching {
        api().createSupportThread(JsonObject().apply {
            addProperty("category", category)
            addProperty("message", message)
            fileName?.let { addProperty("fileName", it) }
            contentBase64?.let { addProperty("contentBase64", it) }
        })
    }

    suspend fun sendSupportMessage(
        uuid: String,
        message: String,
        fileName: String? = null,
        contentBase64: String? = null,
    ): Result<Unit> = runCatching {
        api().supportMessage(uuid, JsonObject().apply {
            addProperty("message", message)
            fileName?.let { addProperty("fileName", it) }
            contentBase64?.let { addProperty("contentBase64", it) }
        })
        Unit
    }

    suspend fun startScreenShare(threadUuid: String): Result<ScreenShareDto?> = runCatching {
        api().startScreenShare(threadUuid).share
    }

    suspend fun sendScreenFrame(threadUuid: String, shareUuid: String, base64: String): Result<Unit> = runCatching {
        api().sendScreenFrame(threadUuid, shareUuid, JsonObject().apply {
            addProperty("contentBase64", base64)
        })
        Unit
    }

    suspend fun stopScreenShare(threadUuid: String, shareUuid: String): Result<Unit> = runCatching {
        api().stopScreenShare(threadUuid, shareUuid)
        Unit
    }
    /** Problema de mapa (botão "Comunicar um problema com o mapa"). */
    suspend fun mapReport(reason: String, note: String, latitude: Double?, longitude: Double?): Result<Unit> = runCatching {
        val body = JsonObject().apply {
            addProperty("reason", reason)
            addProperty("note", note)
            latitude?.let { addProperty("latitude", it) }
            longitude?.let { addProperty("longitude", it) }
        }
        api().mapReport(body)
        Unit
    }

    suspend fun safetyContacts(): Result<List<SafetyContact>> =
        runCatching { api().safetyContacts().contacts }

    suspend fun addSafetyContact(name: String, phone: String): Result<SafetyContact> = runCatching {
        api().addSafetyContact(JsonObject().apply {
            addProperty("name", name)
            addProperty("phone", phone)
        }).contact ?: error("Resposta sem contacto")
    }

    suspend fun deleteSafetyContact(uuid: String): Result<Unit> = runCatching {
        api().deleteSafetyContact(uuid); Unit
    }

    suspend fun safetySos(tripUuid: String?, latitude: Double?, longitude: Double?): Result<Unit> = runCatching {
        api().safetySos(JsonObject().apply {
            tripUuid?.let { addProperty("tripUuid", it) }
            latitude?.let { addProperty("latitude", it) }
            longitude?.let { addProperty("longitude", it) }
        })
        Unit
    }

    suspend fun shareTrip(tripUuid: String): Result<SafetyShareResponse> = runCatching {
        api().safetyShare(JsonObject().apply { addProperty("tripUuid", tripUuid) })
    }

    suspend fun rideCheck(tripUuid: String, status: String): Result<Unit> = runCatching {
        api().rideCheck(JsonObject().apply {
            addProperty("tripUuid", tripUuid)
            addProperty("status", status)
        })
        Unit
    }

    suspend fun startRecording(tripUuid: String, kind: String = "audio"): Result<String?> = runCatching {
        api().startRecording(JsonObject().apply {
            addProperty("tripUuid", tripUuid)
            addProperty("kind", kind)
        }).recording?.uuid
    }

    suspend fun stopRecording(uuid: String, contentBase64: String?): Result<Unit> = runCatching {
        api().stopRecording(uuid, JsonObject().apply {
            contentBase64?.let { addProperty("contentBase64", it) }
        })
        Unit
    }
}
