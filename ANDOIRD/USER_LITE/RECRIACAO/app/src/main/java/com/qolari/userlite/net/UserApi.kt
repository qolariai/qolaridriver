package com.qolari.userlite.net

import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path
import retrofit2.http.Query

/** Contrato desenhado para a app Lite (ANDOIRD/USER_LITE/endpoints.json). */
interface UserApi {

    @POST("/rt/identity/oauth2/token")
    suspend fun token(@Body body: Map<String, String>): TokenResponse

    @GET("/rt/lite/session")
    suspend fun session(): SessionResponse

    @retrofit2.http.PATCH("/rt/lite/account")
    suspend fun updateAccount(@Body body: UpdateAccount): SessionResponse

    @POST("/rt/lite/account/home")
    suspend fun setHome(@Body body: HomePlaceRequest): SavedPlaceResponse

    @GET("/rt/lite/home")
    suspend fun home(): HomeResponse

    @GET("/rt/lite/places")
    suspend fun places(@Query("q") query: String = ""): PlacesResponse

    @POST("/rt/lite/quote")
    suspend fun quote(@Body body: QuoteRequest): QuoteResponse

    @POST("/rt/lite/request")
    suspend fun request(@Body body: RequestTrip): TripResponse

    @GET("/rt/lite/active")
    suspend fun active(): TripResponse

    @GET("/rt/lite/trips/{uuid}")
    suspend fun trip(@Path("uuid") uuid: String): TripResponse

    @POST("/rt/lite/trips/{uuid}/cancel")
    suspend fun cancel(@Path("uuid") uuid: String, @Body body: Map<String, String>): TripResponse

    @POST("/rt/lite/trips/{uuid}/rate")
    suspend fun rate(@Path("uuid") uuid: String, @Body body: RateRequest): TripResponse

    @GET("/rt/lite/history")
    suspend fun history(): HistoryResponse

    @GET("/rt/lite/wallet")
    suspend fun wallet(): WalletResponse

    @POST("/rt/lite/payments/select")
    suspend fun selectPayment(@Body body: Map<String, String>): Map<String, Payment>

    @GET("/rt/lite/promotions")
    suspend fun promotions(): PromotionsResponse

    @POST("/rt/lite/promotions/apply")
    suspend fun applyPromotion(@Body body: Map<String, String>): AppliedPromo

    @POST("/rt/lite/location")
    suspend fun location(@Body body: Map<String, Double>): Map<String, Boolean>
}
