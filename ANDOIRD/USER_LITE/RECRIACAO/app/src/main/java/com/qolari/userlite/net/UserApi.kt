package com.qolari.userlite.net

import retrofit2.http.Body
import retrofit2.http.DELETE
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

    @GET("/rt/lite/places/saved")
    suspend fun savedPlaces(): PlacesResponse

    @POST("/rt/lite/places/saved")
    suspend fun savePlace(@Body body: Map<String, String>): SavedPlaceResponse

    @DELETE("/rt/lite/places/saved/{id}")
    suspend fun deleteSavedPlace(@Path("id") id: String): Map<String, Boolean>

    @GET("/rt/lite/account/extras")
    suspend fun accountExtras(): AccountExtrasResponse

    @POST("/rt/lite/account/business")
    suspend fun saveBusiness(@Body body: Map<String, String>): AccountExtrasResponse

    @POST("/rt/lite/account/family")
    suspend fun saveFamily(@Body body: Map<String, String>): AccountExtrasResponse

    @POST("/rt/lite/account/uber-one")
    suspend fun uberOne(@Body body: Map<String, String>): AccountExtrasResponse

    @POST("/rt/lite/quote")
    suspend fun quote(@Body body: QuoteRequest): QuoteResponse

    @POST("/rt/lite/route")
    suspend fun route(@Body body: RouteRequest): RouteResponse

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

    @POST("/rt/lite/trips/{uuid}/tip")
    suspend fun tip(@Path("uuid") uuid: String, @Body body: Map<String, Int>): TripResponse

    @GET("/rt/lite/trips/{uuid}/receipt")
    suspend fun receipt(@Path("uuid") uuid: String): ReceiptResponse

    @POST("/rt/lite/trips/{uuid}/dispute")
    suspend fun dispute(@Path("uuid") uuid: String, @Body body: Map<String, String>): DisputeResponse

    @POST("/rt/lite/wallet/topup")
    suspend fun topUp(@Body body: Map<String, Int>): TopUpResponse

    @POST("/rt/devices/push-token")
    suspend fun pushToken(@Body body: Map<String, String>): Map<String, Boolean>

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

    @GET("/rt/support/threads")
    suspend fun supportThreads(): SupportThreadsResponse

    @POST("/rt/support/threads")
    suspend fun createSupportThread(@Body body: Map<String, String>): SupportThreadResponse

    @GET("/rt/support/threads/{uuid}")
    suspend fun supportThread(@Path("uuid") uuid: String): SupportThreadResponse

    @POST("/rt/support/threads/{uuid}/messages")
    suspend fun sendSupportMessage(@Path("uuid") uuid: String, @Body body: Map<String, String>): com.google.gson.JsonObject

    @POST("/rt/support/threads/{uuid}/screen-share/start")
    suspend fun startScreenShare(@Path("uuid") uuid: String): ScreenShareResponse

    @POST("/rt/support/threads/{uuid}/screen-share/{share}/frame")
    suspend fun sendScreenFrame(@Path("uuid") uuid: String, @Path("share") share: String,
                                @Body body: Map<String, String>): com.google.gson.JsonObject

    @POST("/rt/support/threads/{uuid}/screen-share/{share}/stop")
    suspend fun stopScreenShare(@Path("uuid") uuid: String, @Path("share") share: String): ScreenShareResponse

    @GET("/rt/safety/contacts")
    suspend fun safetyContacts(): SafetyContactsResponse

    @POST("/rt/safety/contacts")
    suspend fun addSafetyContact(@Body body: Map<String, String>): SafetyContactResponse

    @DELETE("/rt/safety/contacts/{uuid}")
    suspend fun deleteSafetyContact(@Path("uuid") uuid: String): Map<String, Boolean>

    @POST("/rt/safety/sos")
    suspend fun safetySos(@Body body: com.google.gson.JsonObject): com.google.gson.JsonObject

    @POST("/rt/safety/share")
    suspend fun safetyShare(@Body body: Map<String, String>): SafetyShareResponse

    @POST("/rt/safety/ride-check")
    suspend fun rideCheck(@Body body: com.google.gson.JsonObject): com.google.gson.JsonObject
}
