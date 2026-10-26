package com.qolari.userlite.data

import com.qolari.userlite.net.ApiClient
import com.qolari.userlite.net.AccountExtrasResponse
import com.qolari.userlite.net.Cash
import com.qolari.userlite.net.HistoryResponse
import com.qolari.userlite.net.HomeResponse
import com.qolari.userlite.net.HomePlaceRequest
import com.qolari.userlite.net.Payment
import com.qolari.userlite.net.Place
import com.qolari.userlite.net.PromotionsResponse
import com.qolari.userlite.net.QuoteRequest
import com.qolari.userlite.net.QuoteResponse
import com.qolari.userlite.net.RateRequest
import com.qolari.userlite.net.Receipt
import com.qolari.userlite.net.RequestTrip
import com.qolari.userlite.net.RouteRequest
import com.qolari.userlite.net.RoutePoint
import com.qolari.userlite.net.SafetyContact
import com.qolari.userlite.net.SafetyShareResponse
import com.qolari.userlite.net.ScreenShareDto
import com.qolari.userlite.net.SessionResponse
import com.qolari.userlite.net.SupportThreadDto
import com.qolari.userlite.net.SupportThreadResponse
import com.qolari.userlite.net.Trip
import com.qolari.userlite.net.UpdateAccount
import com.qolari.userlite.net.UserApi
import com.qolari.userlite.net.WalletResponse

/**
 * Único ponto de acesso à API da User Lite. Devolve [Result] em vez de lançar: os ecrãs decidem
 * como mostrar o erro (banner, estado vazio ou folha de erro).
 */
class UserRepository(private val session: SessionStore) {

    @Volatile private var token: String? = null
    private var api: UserApi? = null
    private var apiUrl: String? = null

    private suspend fun api(): UserApi {
        val s = session.current()
        token = s.token
        if (api == null || apiUrl != s.baseUrl) {
            api = ApiClient.create(s.baseUrl) { token }
            apiUrl = s.baseUrl
        }
        return api!!
    }

    suspend fun hasSession(): Boolean = session.current().token != null

    suspend fun login(phone: String, code: String): Result<SessionResponse> = runCatching {
        val tokenResponse = api().token(
            mapOf("grant_type" to "password", "username" to phone, "password" to code)
        )
        val access = tokenResponse.token ?: error("Resposta sem token")
        session.saveSession(access, tokenResponse.refresh, phone)
        token = access
        api().session()
    }

    suspend fun session(): Result<SessionResponse> = runCatching { api().session() }

    suspend fun updateAccount(firstName: String, lastName: String, email: String): Result<SessionResponse> =
        runCatching { api().updateAccount(UpdateAccount(firstName, lastName, email)) }

    suspend fun setHome(placeId: String): Result<Place> = runCatching {
        api().setHome(HomePlaceRequest(placeId)).savedPlace
    }

    suspend fun home(): Result<HomeResponse> = runCatching { api().home() }

    suspend fun places(query: String): Result<List<Place>> = runCatching { api().places(query).places }

    suspend fun savedPlaces(): Result<List<Place>> = runCatching { api().savedPlaces().places }

    suspend fun savePlace(label: String, address: String): Result<Place> = runCatching {
        api().savePlace(mapOf("label" to label, "address" to address)).savedPlace
    }

    suspend fun deleteSavedPlace(id: String): Result<Unit> = runCatching {
        api().deleteSavedPlace(id); Unit
    }

    suspend fun accountExtras(): Result<AccountExtrasResponse> = runCatching { api().accountExtras() }

    suspend fun saveBusiness(companyName: String, vat: String, email: String): Result<AccountExtrasResponse> =
        runCatching { api().saveBusiness(mapOf("companyName" to companyName, "vat" to vat, "email" to email)) }

    suspend fun saveFamily(name: String, phone: String, teen: Boolean, action: String = "add"): Result<AccountExtrasResponse> =
        runCatching {
            api().saveFamily(mapOf("name" to name, "phone" to phone, "teen" to teen.toString(), "action" to action))
        }

    suspend fun uberOne(action: String): Result<AccountExtrasResponse> = runCatching {
        api().uberOne(mapOf("action" to action))
    }

    suspend fun quote(pickup: RoutePoint, dropoff: RoutePoint): Result<QuoteResponse> =
        runCatching { api().quote(QuoteRequest(pickup, dropoff)) }

    /** Rota por estrada (backend → OSRM com fallback em linha reta). */
    suspend fun route(origin: RoutePoint, destination: RoutePoint): Result<List<Pair<Double, Double>>> =
        runCatching {
            api().route(RouteRequest(origin, destination)).polyline.map { it.latitude to it.longitude }
        }

    suspend fun registerPushToken(token: String): Result<Unit> = runCatching {
        api().pushToken(mapOf("token" to token))
        Unit
    }

    suspend fun request(
        pickup: RoutePoint,
        dropoff: RoutePoint,
        productId: Int,
        payment: String,
        promoCode: String?,
        scheduledAt: Long? = null,
        stops: List<RoutePoint> = emptyList(),
    ): Result<Trip> = runCatching {
        api().request(RequestTrip(pickup, dropoff, productId, payment, promoCode, scheduledAt, stops)).trip
            ?: error("Resposta sem viagem")
    }

    suspend fun active(): Result<Trip?> = runCatching { api().active().trip }

    suspend fun trip(uuid: String): Result<Trip?> = runCatching { api().trip(uuid).trip }

    suspend fun cancel(uuid: String, reason: String): Result<Trip?> = runCatching {
        api().cancel(uuid, mapOf("reason" to reason)).trip
    }

    suspend fun rate(uuid: String, stars: Int, comment: String = ""): Result<Trip?> = runCatching {
        api().rate(uuid, RateRequest(stars = stars, comment = comment)).trip
    }

    suspend fun tip(uuid: String, amountCents: Int): Result<Trip?> = runCatching {
        api().tip(uuid, mapOf("amountCents" to amountCents)).trip
    }

    suspend fun receipt(uuid: String): Result<Receipt?> = runCatching {
        api().receipt(uuid).receipt
    }

    suspend fun dispute(uuid: String, reason: String): Result<Unit> = runCatching {
        api().dispute(uuid, mapOf("reason" to reason)); Unit
    }

    suspend fun topUp(amountCents: Int): Result<Cash> = runCatching {
        api().topUp(mapOf("amountCents" to amountCents)).cash
    }

    suspend fun history(): Result<HistoryResponse> = runCatching { api().history() }

    suspend fun wallet(): Result<WalletResponse> = runCatching { api().wallet() }

    suspend fun selectPayment(id: String): Result<Payment> = runCatching {
        api().selectPayment(mapOf("id" to id))["payment"] ?: error("Resposta sem forma de pagamento")
    }

    suspend fun promotions(): Result<PromotionsResponse> = runCatching { api().promotions() }

    suspend fun applyPromotion(code: String): Result<Unit> = runCatching {
        api().applyPromotion(mapOf("code" to code)); Unit
    }

    suspend fun uploadLocation(lat: Double, lng: Double): Result<Unit> = runCatching {
        api().location(mapOf("lat" to lat, "lng" to lng)); Unit
    }

    suspend fun supportThreads(): Result<List<SupportThreadDto>> = runCatching {
        api().supportThreads().threads
    }

    suspend fun supportThread(uuid: String): Result<SupportThreadResponse> = runCatching {
        api().supportThread(uuid)
    }

    suspend fun createSupportThread(message: String, category: String = "outro",
                                    fileName: String? = null, contentBase64: String? = null): Result<SupportThreadResponse> =
        runCatching {
            api().createSupportThread(buildMap {
                put("category", category)
                put("message", message)
                fileName?.let { put("fileName", it) }
                contentBase64?.let { put("contentBase64", it) }
            })
        }

    suspend fun sendSupportMessage(uuid: String, message: String,
                                   fileName: String? = null, contentBase64: String? = null): Result<Unit> =
        runCatching {
            api().sendSupportMessage(uuid, buildMap {
                put("message", message)
                fileName?.let { put("fileName", it) }
                contentBase64?.let { put("contentBase64", it) }
            })
            Unit
        }

    suspend fun startScreenShare(threadUuid: String): Result<ScreenShareDto?> = runCatching {
        api().startScreenShare(threadUuid).share
    }

    suspend fun sendScreenFrame(threadUuid: String, shareUuid: String, base64: String): Result<Unit> = runCatching {
        api().sendScreenFrame(threadUuid, shareUuid, mapOf("contentBase64" to base64)); Unit
    }

    suspend fun stopScreenShare(threadUuid: String, shareUuid: String): Result<Unit> = runCatching {
        api().stopScreenShare(threadUuid, shareUuid); Unit
    }

    suspend fun safetyContacts(): Result<List<SafetyContact>> = runCatching {
        api().safetyContacts().contacts
    }

    suspend fun addSafetyContact(name: String, phone: String): Result<SafetyContact> = runCatching {
        api().addSafetyContact(mapOf("name" to name, "phone" to phone)).contact
            ?: error("Resposta sem contacto")
    }

    suspend fun deleteSafetyContact(uuid: String): Result<Unit> = runCatching {
        api().deleteSafetyContact(uuid); Unit
    }

    suspend fun safetySos(tripUuid: String?, latitude: Double?, longitude: Double?): Result<Unit> = runCatching {
        val body = com.google.gson.JsonObject().apply {
            tripUuid?.let { addProperty("tripUuid", it) }
            latitude?.let { addProperty("latitude", it) }
            longitude?.let { addProperty("longitude", it) }
        }
        api().safetySos(body); Unit
    }

    suspend fun shareTrip(tripUuid: String): Result<SafetyShareResponse> = runCatching {
        api().safetyShare(mapOf("tripUuid" to tripUuid))
    }

    suspend fun rideCheck(tripUuid: String, status: String, lat: Double? = null, lng: Double? = null): Result<Unit> =
        runCatching {
            api().rideCheck(com.google.gson.JsonObject().apply {
                addProperty("tripUuid", tripUuid)
                addProperty("status", status)
                lat?.let { addProperty("latitude", it) }
                lng?.let { addProperty("longitude", it) }
            }); Unit
        }

    suspend fun signOut() {
        session.clear()
        token = null
        api = null
        apiUrl = null
    }
}
