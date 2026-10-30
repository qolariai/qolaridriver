package com.qolari.userlite.data

import com.qolari.userlite.net.ApiClient
import com.qolari.userlite.net.HistoryResponse
import com.qolari.userlite.net.HomeResponse
import com.qolari.userlite.net.HomePlaceRequest
import com.qolari.userlite.net.Payment
import com.qolari.userlite.net.Place
import com.qolari.userlite.net.PromotionsResponse
import com.qolari.userlite.net.QuoteRequest
import com.qolari.userlite.net.QuoteResponse
import com.qolari.userlite.net.RateRequest
import com.qolari.userlite.net.RequestTrip
import com.qolari.userlite.net.RoutePoint
import com.qolari.userlite.net.SessionResponse
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

    suspend fun quote(pickup: RoutePoint, dropoff: RoutePoint): Result<QuoteResponse> =
        runCatching { api().quote(QuoteRequest(pickup, dropoff)) }

    suspend fun request(
        pickup: RoutePoint,
        dropoff: RoutePoint,
        productId: Int,
        payment: String,
        promoCode: String?,
    ): Result<Trip> = runCatching {
        api().request(RequestTrip(pickup, dropoff, productId, payment, promoCode)).trip
            ?: error("Resposta sem viagem")
    }

    suspend fun active(): Result<Trip?> = runCatching { api().active().trip }

    suspend fun trip(uuid: String): Result<Trip?> = runCatching { api().trip(uuid).trip }

    suspend fun cancel(uuid: String, reason: String): Result<Trip?> = runCatching {
        api().cancel(uuid, mapOf("reason" to reason)).trip
    }

    suspend fun rate(uuid: String, stars: Int, comment: String = ""): Result<Trip?> = runCatching {
        api().rate(uuid, RateRequest(stars, comment)).trip
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

    suspend fun signOut() {
        session.clear()
        token = null
        api = null
        apiUrl = null
    }
}
