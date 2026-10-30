package com.qolari.drivereplica.net

import com.google.gson.JsonObject
import retrofit2.http.Body
import retrofit2.http.POST

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

    @POST("/rt/earnings/get-activity-feed-v3")
    suspend fun activityFeed(@Body body: JsonObject = JsonObject()): ActivityFeed

    @POST("/rt/earnings/get-trip")
    suspend fun earningsTrip(@Body body: JsonObject): JsonObject

    @POST("/rt/drivers/v2/documents")
    suspend fun documents(@Body body: JsonObject = JsonObject()): DocumentsResponse

    @POST("/rt/inbox/notifications")
    suspend fun notifications(@Body body: JsonObject = JsonObject()): NotificationsResponse

    @POST("/rt/inbox/mark-read")
    suspend fun markRead(@Body body: JsonObject = JsonObject()): JsonObject

    @POST("/rt/navigation/v3/route")
    suspend fun route(@Body body: JsonObject): RouteResponse

    /** Chat da viagem (vídeo 2026-10-30). */
    @POST("/rt/trips/message")
    suspend fun tripMessage(@Body body: JsonObject): JsonObject

    /** Cancelamento do condutor com motivo (lista de 2026-10-30). */
    @POST("/rt/trips/driver-cancel")
    suspend fun driverCancelTrip(@Body body: JsonObject): JsonObject

    @POST("/rt/earner-profile/get-profile-hub")
    suspend fun profileHub(@Body body: JsonObject = JsonObject()): ProfileHub

    @POST("/rt/users/get-user-info")
    suspend fun userInfo(@Body body: JsonObject = JsonObject()): JsonObject
}
