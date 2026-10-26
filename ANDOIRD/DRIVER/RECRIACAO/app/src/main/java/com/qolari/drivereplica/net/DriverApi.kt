package com.qolari.drivereplica.net

import com.google.gson.JsonObject
import retrofit2.http.Body
import retrofit2.http.DELETE
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path

/** Contrato: ui_spec_android/contract_main_flow.md (validado no BACKEND do laboratório). */
interface DriverApi {

    @POST("/rt/identity/oauth2/token")
    suspend fun token(@Body body: Map<String, String>): TokenResponse

    @POST("/rt/drivers/app-launch")
    suspend fun appLaunch(@Body body: JsonObject = JsonObject()): DriverTasksResponse

    @POST("/rt/drivers/v2/fetch-online-blockers")
    suspend fun blockers(@Body body: JsonObject = JsonObject()): BlockersResponse

    @POST("/rt/drivers/v2/vehicles")
    suspend fun vehicles(@Body body: JsonObject = JsonObject()): VehiclesResponse

    @POST("/rt/drivers/v2/go-online")
    suspend fun goOnline(@Body body: JsonObject = JsonObject()): DriverTasksResponse

    @POST("/rt/drivers/v2/go-offline")
    suspend fun goOffline(@Body body: JsonObject = JsonObject()): DriverTasksResponse

    @POST("/rt/drivers/v2/available")
    suspend fun available(@Body body: JsonObject = JsonObject()): DriverTasksResponse

    @POST("/rt/unifiedlocation/uploadpositions")
    suspend fun uploadPositions(@Body body: JsonObject): JsonObject

    @POST("/rt/drivers/unified-offers-v3")
    suspend fun unifiedOffers(@Body body: JsonObject = JsonObject()): UnifiedOffersResponse

    @POST("/rt/drivers/accept-offers")
    suspend fun acceptOffers(@Body body: JsonObject): DriverTasksResponse

    @POST("/rt/drivers/reject-offers")
    suspend fun rejectOffers(@Body body: JsonObject): DriverTasksResponse

    @POST("/rt/drivers/expire-offers")
    suspend fun expireOffers(@Body body: JsonObject): DriverTasksResponse

    @POST("/rt/drivers/get-upfront-offer")
    suspend fun getUpfrontOffer(@Body body: JsonObject = JsonObject()): JsonObject

    @POST("/rt/trips/v2/start-waiting")
    suspend fun startWaiting(@Body body: JsonObject): DriverTasksResponse

    @POST("/rt/trips/v2/confirm-pin-is-verified")
    suspend fun confirmPin(@Body body: JsonObject): JsonObject

    @POST("/rt/trips/v2/begin")
    suspend fun beginTrip(@Body body: JsonObject): DriverTasksResponse

    @POST("/rt/trips/v2/complete-stop")
    suspend fun completeStop(@Body body: JsonObject): DriverTasksResponse

    @POST("/rt/trips/v2/end")
    suspend fun endTrip(@Body body: JsonObject): DriverTasksResponse

    @POST("/rt/trips/v2/driver-cancel")
    suspend fun driverCancel(@Body body: JsonObject): DriverTasksResponse

    @POST("/rt/trips/v2/driver-rate")
    suspend fun driverRate(@Body body: JsonObject): JsonObject

    @POST("/rt/earnings/get-daily-earnings-view")
    suspend fun dailyEarnings(@Body body: JsonObject = JsonObject()): EarningsView

    @POST("/rt/earnings/get-weekly-earnings-view")
    suspend fun weeklyEarnings(@Body body: JsonObject = JsonObject()): EarningsView

    @POST("/rt/earnings/get-balance-summary")
    suspend fun balanceSummary(@Body body: JsonObject = JsonObject()): BalanceSummary

    @POST("/rt/earnings/get-payout-methods")
    suspend fun payoutMethods(@Body body: JsonObject = JsonObject()): PayoutMethodsResponse

    @POST("/rt/earnings/request-payout")
    suspend fun requestPayout(@Body body: JsonObject = JsonObject()): PayoutResponse

    @POST("/rt/earnings/instant-pay")
    suspend fun instantPay(@Body body: JsonObject = JsonObject()): PayoutResponse

    @POST("/rt/earnings/get-payout-history")
    suspend fun payoutHistory(@Body body: JsonObject = JsonObject()): PayoutHistoryResponse

    @POST("/rt/earnings/get-statements")
    suspend fun statements(@Body body: JsonObject = JsonObject()): StatementsResponse

    @POST("/rt/earnings/get-activity-feed-v3")
    suspend fun activityFeed(@Body body: JsonObject = JsonObject()): ActivityFeed

    @POST("/rt/earnings/get-trip")
    suspend fun earningsTrip(@Body body: JsonObject): JsonObject

    @POST("/rt/drivers/v2/documents")
    suspend fun documents(@Body body: JsonObject = JsonObject()): DocumentsResponse

    @POST("/rt/drivers/v2/documents/upload")
    suspend fun uploadDocument(@Body body: JsonObject): JsonObject

    @POST("/rt/drivers/v2/verify-identity")
    suspend fun verifyIdentity(@Body body: JsonObject): JsonObject

    @GET("/rt/drivers/v2/preferences")
    suspend fun preferences(): PreferencesResponse

    @POST("/rt/drivers/v2/preferences")
    suspend fun savePreferences(@Body body: JsonObject): PreferencesResponse

    @POST("/rt/drivers/v2/break")
    suspend fun setBreak(@Body body: JsonObject): PreferencesResponse

    @GET("/rt/drivers/v2/airport-queue")
    suspend fun airportQueue(): AirportQueueResponse

    @POST("/rt/drivers/v2/airport-queue")
    suspend fun airportQueueAction(@Body body: JsonObject): AirportQueueResponse

    @GET("/rt/drivers/v2/incentives")
    suspend fun incentives(): IncentivesResponse

    @POST("/rt/drivers/v2/quests/{uuid}/claim")
    suspend fun claimQuest(@Path("uuid") uuid: String): IncentivesResponse

    @POST("/rt/drivers/v2/referrals")
    suspend fun invite(@Body body: JsonObject): IncentivesResponse

    @POST("/rt/earnings/request-adjustment")
    suspend fun requestAdjustment(@Body body: JsonObject): JsonObject

    @POST("/rt/earnings/get-invoices")
    suspend fun invoices(@Body body: JsonObject = JsonObject()): InvoicesResponse

    @POST("/rt/earnings/get-tax-info")
    suspend fun taxSummary(@Body body: JsonObject = JsonObject()): TaxInfo

    @GET("/rt/drivers/v2/business-profile")
    suspend fun businessProfile(): DriverBusinessResponse

    @POST("/rt/drivers/v2/business-profile")
    suspend fun saveBusinessProfile(@Body body: JsonObject): DriverBusinessResponse

    @POST("/rt/inbox/notifications")
    suspend fun notifications(@Body body: JsonObject = JsonObject()): NotificationsResponse

    @POST("/rt/inbox/mark-read")
    suspend fun markRead(@Body body: JsonObject = JsonObject()): JsonObject

    @POST("/rt/support/map-report")
    suspend fun mapReport(@Body body: JsonObject): JsonObject

    @POST("/rt/devices/push-token")
    suspend fun pushToken(@Body body: JsonObject): JsonObject

    @retrofit2.http.GET("/rt/location/search")
    suspend fun searchPlaces(
        @retrofit2.http.Query("q") q: String,
        @retrofit2.http.Query("lat") lat: Double? = null,
        @retrofit2.http.Query("lng") lng: Double? = null,
    ): PlacesResponse

    @POST("/rt/support/threads")
    suspend fun createSupportThread(@Body body: JsonObject): SupportThreadResponse

    @GET("/rt/support/threads")
    suspend fun supportThreads(): SupportThreadsResponse

    @GET("/rt/support/threads/{uuid}")
    suspend fun supportThread(@Path("uuid") uuid: String): SupportThreadResponse

    @POST("/rt/support/threads/{uuid}/messages")
    suspend fun supportMessage(@Path("uuid") uuid: String, @Body body: JsonObject): JsonObject

    @POST("/rt/support/threads/{uuid}/screen-share/start")
    suspend fun startScreenShare(@Path("uuid") uuid: String): ScreenShareResponse

    @POST("/rt/support/threads/{uuid}/screen-share/{share}/frame")
    suspend fun sendScreenFrame(@Path("uuid") uuid: String, @Path("share") share: String,
                                @Body body: JsonObject): JsonObject

    @POST("/rt/support/threads/{uuid}/screen-share/{share}/stop")
    suspend fun stopScreenShare(@Path("uuid") uuid: String, @Path("share") share: String): ScreenShareResponse

    @POST("/rt/navigation/v3/route")
    suspend fun route(@Body body: JsonObject): RouteResponse

    @POST("/rt/earner-profile/get-profile-hub")
    suspend fun profileHub(@Body body: JsonObject = JsonObject()): ProfileHub

    @POST("/rt/users/get-user-info")
    suspend fun userInfo(@Body body: JsonObject = JsonObject()): JsonObject

    @GET("/rt/safety/contacts")
    suspend fun safetyContacts(): SafetyContactsResponse

    @POST("/rt/safety/contacts")
    suspend fun addSafetyContact(@Body body: JsonObject): SafetyContactResponse

    @DELETE("/rt/safety/contacts/{uuid}")
    suspend fun deleteSafetyContact(@Path("uuid") uuid: String): JsonObject

    @POST("/rt/safety/sos")
    suspend fun safetySos(@Body body: JsonObject): JsonObject

    @POST("/rt/safety/share")
    suspend fun safetyShare(@Body body: JsonObject): SafetyShareResponse

    @POST("/rt/safety/ride-check")
    suspend fun rideCheck(@Body body: JsonObject): JsonObject

    @POST("/rt/safety/recording/start")
    suspend fun startRecording(@Body body: JsonObject): RecordingResponse

    @POST("/rt/safety/recording/{uuid}/stop")
    suspend fun stopRecording(@Path("uuid") uuid: String, @Body body: JsonObject): RecordingResponse
}
