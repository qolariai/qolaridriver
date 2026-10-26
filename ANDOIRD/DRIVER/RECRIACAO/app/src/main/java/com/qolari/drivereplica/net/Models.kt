package com.qolari.drivereplica.net

import com.google.gson.JsonObject
import com.google.gson.annotations.SerializedName

// ---- auth ----
data class TokenRequest(
    @SerializedName("grant_type") val grantType: String,
    val username: String? = null,
    val password: String? = null,
    @SerializedName("refresh_token") val refreshToken: String? = null,
)

data class TokenResponse(
    @SerializedName("accessToken") val accessToken: String?,
    @SerializedName("refreshToken") val refreshToken: String?,
    @SerializedName("expiresIn") val expiresIn: Long?,
    @SerializedName("sessionID") val sessionId: String?,
    @SerializedName("access_token") val accessTokenSnake: String?,
) {
    val token: String? get() = accessToken ?: accessTokenSnake
}

// ---- DriverTasks ----
data class DriverTasksResponse(@SerializedName("driverTasks") val driverTasks: DriverTasks?)

data class DriverTasks(
    val driverState: DriverState?,
    val taskScopes: List<TaskScope>?,
    val meta: Meta?,
)

data class DriverState(
    val online: Boolean?,
    val available: Boolean?,
    val dispatchable: Boolean?,
)

data class Meta(val lastModifiedTimeMs: Double?)

data class TaskScope(
    val blockingTasks: List<DriverTask>?,
    val nonBlockingTasks: List<DriverTask>?,
    val completionTask: CompletionTask?,
)

data class DriverTask(
    val taskId: String?,
    val isCompleted: Boolean?,
    val driverTaskDataUnion: JsonObject?,
) {
    /** driverTaskDataUnion.singleTaskData.taskDataUnion -> {type, <type>: data} */
    fun inner(): Pair<String?, JsonObject?> {
        val std = driverTaskDataUnion?.getAsJsonObject("singleTaskData") ?: return null to null
        val u = std.getAsJsonObject("taskDataUnion") ?: return null to null
        val type = u.get("type")?.asString
        return type to if (type != null) u.getAsJsonObject(type) else null
    }
}

data class CompletionTask(
    val taskId: String?,
    val isCompleted: Boolean?,
    val taskDataType: String?, // "pickupTaskData" | "dropoffTaskData"
    val jobOrdering: List<String>?,
    val coalescedDataUnion: JsonObject?,
    val taskDataMap: Map<String, JsonObject>?,
) {
    /** taskDataMap[job].<taskDataType> -> {entity, driverUpfrontFare,...} */
    fun tripData(): JsonObject? {
        val job = jobOrdering?.firstOrNull() ?: taskDataMap?.keys?.firstOrNull() ?: return null
        val entry = taskDataMap?.get(job) ?: return null
        val type = entry.get("type")?.asString ?: taskDataType ?: return null
        return entry.getAsJsonObject(type)
    }

    /** coalescedDataUnion.<pickup|dropoff>CoalescedTaskData -> {product, info} */
    fun coalesced(): JsonObject? {
        val u = coalescedDataUnion ?: return null
        val type = u.get("type")?.asString ?: return null
        return u.getAsJsonObject(type)
    }
}

// ---- ofertas ----
data class UnifiedOffersResponse(
    val data: UnifiedOffers?,
    val etag: String?,
    val pollingInterval: Long?,
)

data class UnifiedOffers(
    val meta: Meta?,
    val offers: List<UnifiedOffer>?,
)

data class UnifiedOffer(
    val offerUUIDs: List<String>?,
    val driverOfferData: DriverOfferData?,
)

data class DriverOfferData(
    val type: String?,
    val primaryOffer: DriverOffer?,
)

data class DriverOffer(
    val offerUUID: String?,
    val jobUUID: String?,
    val offerType: String?,
    val offerStatus: String?,
    val metaData: JsonObject?,
    val offerView: JsonObject?,
) {
    fun jobModel(): JsonObject? = metaData?.getAsJsonObject("jobOfferModel")

    /** textos das labels do offerView (clusters -> elements -> label.text.text) */
    fun viewTexts(): List<String> {
        val out = mutableListOf<String>()
        fun texts(node: com.google.gson.JsonElement?) {
            if (node is JsonObject) {
                node.get("text")?.takeIf { it.isJsonPrimitive }?.asString
                    ?.let { out.add(it); return }
                for ((_, v) in node.entrySet()) texts(v)
            } else if (node?.isJsonArray == true) {
                for (v in node.asJsonArray) texts(v)
            }
        }
        val view = offerView?.getAsJsonObject("jobOfferViewV3")?.getAsJsonObject("coreInfo")
            ?.getAsJsonObject("simpleView")?.getAsJsonArray("clusters")
        texts(view)
        return out.distinct()
    }
}

// ---- vários ----
data class BlockersResponse(
    val issues: List<Issue>?,
    val futureBlockers: List<com.google.gson.JsonElement>?,
)

data class Issue(val issueData: IssueData?) {
    val title: String? get() = issueData?.displayContent?.get("title")?.asString
        ?: issueData?.displayContent?.get("subtitle")?.asString
    val message: String? get() = issueData?.displayContent?.get("message")?.asString
}

data class IssueData(val displayContent: Map<String, com.google.gson.JsonElement>?)

data class VehiclesResponse(val vehicles: List<Vehicle>?)

data class Vehicle(
    val uuid: String?,
    val name: String?,
    val make: String?,
    val model: String?,
    val licensePlate: String?,
    val isDefault: Boolean?,
    val year: Int? = null,
) {
    val label: String get() = listOfNotNull(name ?: listOfNotNull(make, model).joinToString(" ").ifBlank { null },
        licensePlate).joinToString(" · ")
}

data class EarningsView(
    val startAt: Double?,
    val endAt: Double?,
    val formattedTotal: String?,
    val formattedTripEarning: String?,
    val formattedCommission: String?,
    val tripCount: Int?,
    val currencyCode: String?,
    val trips: List<EarningsTrip>?,
    val onlineSeconds: Long? = null,
)

data class EarningsTrip(
    val uuid: String?,
    val pickupAddress: String?,
    val dropoffAddress: String?,
    val processedAt: Double?,
    val formattedTotal: String?,
    val formattedDistance: String?,
    val vehicleType: String?,
)

data class BalanceSummary(
    val balance: String?,
    val balanceAmount: Double?,
    val currencyCode: String?,
    val cashOutEnabled: Boolean?,
)

data class ActivityFeed(val items: List<ActivityItem>?)

data class ActivityItem(
    val uuid: String?,
    val kind: String?,
    val amount: String?,
    val timestamp: Double?,
    val description: String?,
    val tripUUID: String?,
)

data class ProfileHub(val profile: Profile?)

data class Profile(
    val uuid: String?,
    val firstName: String?,
    val lastName: String?,
    val rating: Double?,
    val tripCount: Int?,
    val acceptanceRate: Int?,
    val memberSince: Double?,
    val vehicle: JsonObject?,
    val fleet: String?,
) {
    val vehicleLabel: String? get() {
        val v = vehicle ?: return null
        return listOfNotNull(
            v.get("name")?.asString ?: listOfNotNull(
                v.get("make")?.asString, v.get("model")?.asString).joinToString(" ").ifBlank { null },
            v.get("licensePlate")?.asString
        ).joinToString(" · ").ifBlank { null }
    }
}

data class ApiError(val code: String?, val message: String?)

// ---- lote 5+: documentos, notificações, rota ----
data class DocumentDto(val uuid: String?, val kind: String?, val title: String?, val status: String?, val expiresOn: String?, val note: String?)

data class DocumentsResponse(val driverDocuments: List<DocumentDto>?, val vehicleDocuments: List<DocumentDto>?)

data class NotificationDto(val uuid: String?, val title: String?, val body: String?, val createdAt: Double?, val read: Boolean?)

data class NotificationsResponse(val notifications: List<NotificationDto>?, val unreadCount: Int?)

data class RoutePoint(val latitude: Double?, val longitude: Double?)

data class RouteResponse(val source: String?, val distanceMeters: Double?, val durationSeconds: Double?, val polyline: List<RoutePoint>?)

/** Resultado da pesquisa de locais (Google Geocoding ou seed). */
data class PlaceResult(
    val id: String = "",
    val name: String = "",
    val line1: String = "",
    val line2: String = "",
    val full: String = "",
    val lat: Double = 0.0,
    val lng: Double = 0.0,
    val provider: String = "",
)

data class PlacesResponse(val places: List<PlaceResult> = emptyList())

data class SupportThreadDto(
    val uuid: String = "",
    val category: String = "",
    val status: String = "open",
    val lastMessage: String = "",
    val unread: Int = 0,
    val updatedAt: Long = 0,
)

data class SupportMessageDto(
    val id: Int = 0,
    val sender: String = "user",
    val body: String = "",
    val createdAt: Long = 0,
    val fileName: String = "",
    val hasFile: Boolean = false,
)

data class SupportThreadsResponse(val threads: List<SupportThreadDto> = emptyList())

data class SupportThreadResponse(
    val thread: SupportThreadDto? = null,
    val messages: List<SupportMessageDto> = emptyList(),
)

data class SafetyContact(
    val uuid: String = "",
    val name: String = "",
    val phone: String = "",
    val createdAt: Long = 0,
)

data class SafetyContactsResponse(
    val contacts: List<SafetyContact> = emptyList(),
    val limit: Int = 10,
)

data class SafetyContactResponse(val contact: SafetyContact? = null)

data class SafetyShareResponse(
    val token: String = "",
    val path: String = "",
    val url: String = "",
    val expiresAt: Long = 0,
)

data class DriverPreferences(
    val destinationMode: Boolean = false,
    val destinationAddress: String = "",
    val destinationLat: Double? = null,
    val destinationLng: Double? = null,
    val areaMode: Boolean = false,
    val areaLabel: String = "",
    val areaLat: Double? = null,
    val areaLng: Double? = null,
    val areaRadiusKm: Double = 5.0,
    val autoAccept: Boolean = false,
    val breakUntil: Long? = null,
    val breakActive: Boolean = false,
)

data class PreferencesResponse(val preferences: DriverPreferences = DriverPreferences())

data class AirportQueueResponse(
    val joined: Boolean = false,
    val position: Int? = null,
    val waiting: Int = 0,
    val joinedAt: Long? = null,
    val airport: String = "",
)

data class QuestDto(
    val uuid: String = "",
    val title: String = "",
    val description: String = "",
    val target: Int = 0,
    val progress: Int = 0,
    val reward: String = "",
    val rewardCents: Int = 0,
    val claimed: Boolean = false,
    val canClaim: Boolean = false,
)

data class ReferralInfo(
    val code: String = "",
    val invited: Int = 0,
    val pending: Int = 0,
    val reward: String = "",
)

data class IncentivesResponse(
    val points: Int = 0,
    val tier: String = "Blue",
    val nextTierPoints: Int? = null,
    val trips: Int = 0,
    val quests: List<QuestDto> = emptyList(),
    val referral: ReferralInfo = ReferralInfo(),
)

data class InvoiceRow(
    val month: String = "",
    val total: String = "",
    val totalCents: Int = 0,
    val net: String = "",
    val tax: String = "",
    val status: String = "",
)

data class InvoicesResponse(val invoices: List<InvoiceRow> = emptyList(), val currencyCode: String = "EUR")

data class TaxInfo(
    val year: Int = 0,
    val gross: String = "",
    val grossCents: Int = 0,
    val net: String = "",
    val netCents: Int = 0,
    val tax: String = "",
    val note: String = "",
)

data class DriverDelegate(val name: String = "", val phone: String = "", val role: String = "")

data class DriverBusiness(
    val active: Boolean = false,
    val companyName: String = "",
    val vat: String = "",
    val email: String = "",
    val delegates: List<DriverDelegate> = emptyList(),
)

data class DriverBusinessResponse(val business: DriverBusiness = DriverBusiness())

data class ScreenShareDto(
    val uuid: String = "",
    val active: Boolean = false,
    val frameAt: Long? = null,
    val hasFrame: Boolean = false,
    val createdAt: Long = 0,
)

data class ScreenShareResponse(val share: ScreenShareDto? = null)

data class RecordingDto(
    val uuid: String = "",
    val tripUuid: String = "",
    val kind: String = "audio",
    val startedAt: Long = 0,
    val endedAt: Long? = null,
    val durationS: Int = 0,
    val hasFile: Boolean = false,
)

data class RecordingResponse(val recording: RecordingDto? = null)

data class PayoutMethod(
    val id: String = "",
    val label: String = "",
    val detail: String = "",
    val instant: Boolean = false,
)

data class PayoutMethodsResponse(
    val balance: String = "",
    val balanceAmount: String = "0.00",
    val currencyCode: String = "EUR",
    val methods: List<PayoutMethod> = emptyList(),
)

data class PayoutDto(
    val uuid: String = "",
    val amount: String = "",
    val amountCents: Int = 0,
    val status: String = "",
    val reference: String = "",
    val createdAt: Long = 0,
    val paidAt: Long? = null,
)

data class PayoutResponse(
    val payout: PayoutDto? = null,
    val balance: String = "",
    val balanceAmount: String = "",
)

data class PayoutHistoryResponse(val payouts: List<PayoutDto> = emptyList())

data class StatementRow(
    val month: String = "",
    val gross: String = "",
    val grossCents: Int = 0,
    val commission: String = "",
    val fleetFee: String = "",
    val net: String = "",
    val netCents: Int = 0,
    val trips: Int = 0,
)

data class StatementsResponse(
    val statements: List<StatementRow> = emptyList(),
    val currencyCode: String = "EUR",
)
