package com.qolari.drivereplica.drive

import com.google.gson.JsonObject
import com.qolari.drivereplica.net.DriverOffer
import com.qolari.drivereplica.net.DriverTasks
import com.qolari.drivereplica.net.UnifiedOffersResponse

/** Cartão da proposta (captura 100_online_*): produto, preço, recolha, viagem e tempo para aceitar. */
data class OfferCard(
    val uuid: String,
    val product: String,
    val price: String,
    val rider: String?,
    val pickupLine: String,
    val pickupAddress: String,
    val tripLine: String?,
    val dropoffAddress: String?,
    val acceptWindowS: Int,
    val expiresAtMs: Long,
    val pickup: Pair<Double, Double>? = null,
    val dropoff: Pair<Double, Double>? = null,
)

enum class TripPhase { TO_PICKUP, AT_PICKUP, ON_TRIP }

/** Tarefa de PIN (PinVerificationTaskData): o PIN vem do servidor e compara-se no ecrã, como na original. */
data class PinTask(
    val pin: String,
    val maxAttempts: Int,
    val title: String,
    val subtitle: String,
    val digits: Int,
    val errors: List<String>,
    val verified: Boolean,
)

data class TripStop(
    val address: String = "",
    val done: Boolean = false,
    val latitude: Double? = null,
    val longitude: Double? = null,
)

data class ActiveTrip(
    val uuid: String,
    val phase: TripPhase,
    val riderName: String,
    val riderRating: Double?,
    val address: String,
    val latitude: Double?,
    val longitude: Double?,
    val fare: String?,
    val waitStartSec: Long?,
    val pin: PinTask?,
    val stops: List<TripStop> = emptyList(),
    val nextStopIndex: Int? = null,
)

/** Resumo no fim da viagem (ganhos: captura 011/062 mostra o total da semana; o da viagem vem de earnings/get-trip). */
data class TripSummary(val tripUuid: String, val total: String, val lines: List<Pair<String, String>>)

object DriveParser {

    /** Primeira proposta aberta, ou nulo. [nowMs] só serve para descartar propostas já expiradas. */
    fun offer(resp: UnifiedOffersResponse?, nowMs: Long = System.currentTimeMillis()): OfferCard? {
        val primary = resp?.data?.offers?.firstOrNull()?.driverOfferData?.primaryOffer ?: return null
        if (primary.offerStatus != null && primary.offerStatus != "OPEN") return null
        val uuid = primary.offerUUID ?: return null
        val model = primary.jobModel()
        val texts = primary.viewTexts()
        val locations = model?.getAsJsonObject("locationMap")
        fun title(ref: String) = locations?.getAsJsonObject(ref)?.str("title")
        val notification = model?.str("notificationTitle").orEmpty().split(" · ")
        val price = texts.firstOrNull { it.contains("€") } ?: notification.getOrNull(1).orEmpty()
        val expires = model?.get("expiresAtEpochMS")?.takeIf { it.isJsonPrimitive }?.asDouble?.toLong() ?: 0L
        if (expires in 1 until nowMs) return null
        val pickupLine = texts.firstOrNull { it.contains("de distância") }
            ?: model?.getAsJsonObject("etaToStartLocation")?.str("longString")?.let { "$it de distância" }.orEmpty()
        fun coord(ref: String): Pair<Double, Double>? {
            val o = locations?.getAsJsonObject(ref) ?: return null
            val la = o.get("latitude")?.takeIf { it.isJsonPrimitive }?.asDouble ?: return null
            val lo = o.get("longitude")?.takeIf { it.isJsonPrimitive }?.asDouble ?: return null
            return la to lo
        }
        return OfferCard(
            uuid = uuid,
            product = texts.firstOrNull() ?: notification.firstOrNull().orEmpty(),
            price = price,
            rider = texts.firstOrNull { it.contains("★") },
            pickupLine = pickupLine,
            pickupAddress = title("pickup").orEmpty(),
            tripLine = texts.firstOrNull { it.startsWith("Viagem de") },
            dropoffAddress = title("dropoff"),
            acceptWindowS = model?.get("acceptWindow")?.takeIf { it.isJsonPrimitive }?.asDouble?.toInt() ?: 20,
            expiresAtMs = expires,
            pickup = coord("pickup"),
            dropoff = coord("dropoff"),
        )
    }

    /** Viagem ativa a partir das DriverTasks (nulo = sem viagem). */
    fun trip(tasks: DriverTasks?): ActiveTrip? {
        val scope = tasks?.taskScopes?.firstOrNull() ?: return null
        val completion = scope.completionTask ?: return null
        val kind = completion.taskDataType ?: return null
        val uuid = completion.jobOrdering?.firstOrNull() ?: completion.taskDataMap?.keys?.firstOrNull() ?: return null
        val data = completion.taskDataMap?.get(uuid)?.getAsJsonObject(kind) ?: return null
        val entity = data.getAsJsonObject("entity")

        var lat: Double? = null
        var lng: Double? = null
        var address: String? = null
        var waitStart: Long? = null
        scope.nonBlockingTasks.orEmpty().forEach { t ->
            val (type, body) = taskData(t.driverTaskDataUnion)
            when (type) {
                "locationTaskData" -> if (address == null) {
                    lat = body?.get("latitude")?.asDouble
                    lng = body?.get("longitude")?.asDouble
                    address = body?.str("title")
                }
                "waitTimeTaskData" -> waitStart = body?.get("startTimeSec")?.asDouble?.toLong()
            }
        }
        val pin = scope.blockingTasks.orEmpty().firstNotNullOfOrNull { t ->
            val (type, body) = taskData(t.driverTaskDataUnion)
            if (type == "pinVerificationTaskData" && body != null) pinTask(body, t.isCompleted == true) else null
        }
        val phase = when {
            kind == "dropoffTaskData" -> TripPhase.ON_TRIP
            waitStart != null -> TripPhase.AT_PICKUP
            else -> TripPhase.TO_PICKUP
        }
        val stops = data.getAsJsonArray("stops")?.mapNotNull { e ->
            val o = e.takeIf { it.isJsonObject }?.asJsonObject ?: return@mapNotNull null
            TripStop(
                address = o.str("address").orEmpty(),
                done = o.get("done")?.takeIf { it.isJsonPrimitive }?.asBoolean ?: false,
                latitude = o.get("lat")?.takeIf { it.isJsonPrimitive }?.asDouble,
                longitude = o.get("lng")?.takeIf { it.isJsonPrimitive }?.asDouble,
            )
        }.orEmpty()
        val nextStop = data.get("nextStopIndex")?.takeIf { it.isJsonPrimitive }?.asInt
        return ActiveTrip(
            uuid = uuid,
            phase = phase,
            riderName = entity?.str("firstName").orEmpty(),
            riderRating = entity?.get("rating")?.takeIf { it.isJsonPrimitive }?.asDouble,
            address = address.orEmpty(),
            latitude = lat,
            longitude = lng,
            fare = data.getAsJsonObject("driverUpfrontFare")?.str("amount"),
            waitStartSec = waitStart,
            pin = pin,
            stops = stops,
            nextStopIndex = nextStop,
        )
    }

    private fun pinTask(body: JsonObject, verified: Boolean): PinTask {
        val rows = body.getAsJsonArray("viewData")?.mapNotNull { it.asJsonObject } ?: emptyList()
        fun row(type: String) = rows.firstOrNull { it.str("type") == type }?.getAsJsonObject(type)
        val texts = rows.filter { it.str("type") == "pinEntryViewTextRow" }.mapNotNull { it.getAsJsonObject("pinEntryViewTextRow")?.str("text") }
        val pin = body.str("pin").orEmpty()
        return PinTask(
            pin = pin,
            maxAttempts = body.get("maxAttemptCount")?.asInt ?: 3,
            title = texts.getOrNull(0).orEmpty(),
            subtitle = texts.getOrNull(1).orEmpty(),
            digits = row("pinEntryViewPinRow")?.get("pinDigitCount")?.asInt ?: pin.length,
            errors = row("pinEntryViewErrorTextRow")?.getAsJsonArray("errorForAttempt")?.map { it.asString } ?: emptyList(),
            verified = verified,
        )
    }

    /** (nome da união, conteúdo) de um `driverTaskDataUnion.singleTaskData.taskDataUnion`. */
    private fun taskData(union: JsonObject?): Pair<String?, JsonObject?> {
        val u = union?.getAsJsonObject("singleTaskData")?.getAsJsonObject("taskDataUnion") ?: return null to null
        val type = u.str("type")
        return type to type?.let { u.getAsJsonObject(it) }
    }

    private fun JsonObject.str(key: String): String? = get(key)?.takeIf { it.isJsonPrimitive }?.asString

    /** Resumo da viagem terminada a partir de earnings/get-trip. */
    fun summary(tripUuid: String, body: JsonObject?): TripSummary {
        val trip = body?.getAsJsonObject("trip")
        val lines = trip?.getAsJsonArray("breakdown")?.mapNotNull { e ->
            val o = e.asJsonObject
            val label = o.str("description")?.replaceFirstChar { it.uppercase() } ?: return@mapNotNull null
            label to o.str("formattedAmount").orEmpty()
        } ?: emptyList()
        return TripSummary(tripUuid, trip?.str("formattedTotal").orEmpty(), lines)
    }
}
