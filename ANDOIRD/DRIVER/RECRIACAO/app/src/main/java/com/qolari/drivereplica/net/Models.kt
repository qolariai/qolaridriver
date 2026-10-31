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
data class DriverTasksResponse(@SerializedName("driverTasks") val driverTasks: DriverTasks?, val radarPending: Boolean? = null)

data class DriverTasks(
    val driverState: DriverState?,
    val taskScopes: List<TaskScope>?,
    val meta: Meta?,
)

data class DriverState(
    val online: Boolean?,
    val available: Boolean?,
    val dispatchable: Boolean?,
    /** Posição que o servidor conhece do motorista (origem da navegação sem GPS). */
    val location: RoutePoint? = null,
    /** Modo Destino (lupa): destino marcado e filtros que restam hoje. */
    val destinationMode: DestinationModeDto? = null,
)

/** Estado do Modo Destino tal como o servidor o manda em `driverState.destinationMode`. */
data class DestinationModeDto(
    val enabled: Boolean? = null,
    val latitude: Double? = null,
    val longitude: Double? = null,
    val label: String? = null,
    val filtersLeft: Int? = null,
    val filtersTotal: Int? = null,
    val radiusKm: Double? = null,
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

/** Uma manobra da rota (painel de navegação do ecrã de recolha). */
data class RouteStep(
    /** Tipo do Google: turn-left, turn-right, roundabout, straight, merge... */
    val maneuver: String?,
    /** Rua da manobra (curta) e a instrução completa em português. */
    val road: String?,
    val instruction: String?,
    /** Instrução curta para o painel ("Vire à direita", "Na rotunda, 2.ª saída"). */
    val instructionShort: String? = null,
    val distanceMeters: Double?,
    /** Duração da manobra (segundos). */
    val durationSeconds: Double?,
    /** Fim da manobra (onde vira). */
    val lat: Double?,
    val lng: Double?,
    val polyline: List<RoutePoint>?,
)

data class RouteResponse(
    val source: String?,
    val distanceMeters: Double?,
    val durationSeconds: Double?,
    val polyline: List<RoutePoint>?,
    /** Manobras da perna (a app escolhe a atual pela posição). */
    val steps: List<RouteStep>?,
    /**
     * Limite de velocidade (km/h) da via. **Nulo quando não é dado real da via** (o servidor só
     * envia quando o OSM tem `maxspeed`); nesse caso a app esconde o selo "LIMITE".
     */
    val speedLimitKmh: Int?,
    /** "osm" (dado da via), "osm_class" (estimativa) ou "heuristic". */
    val speedLimitSource: String? = null,
)
