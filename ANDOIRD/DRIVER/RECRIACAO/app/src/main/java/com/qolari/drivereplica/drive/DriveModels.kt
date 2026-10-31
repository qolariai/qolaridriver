package com.qolari.drivereplica.drive

import com.google.gson.JsonObject
import com.qolari.drivereplica.net.DriverOffer
import com.qolari.drivereplica.net.DriverTasks
import com.qolari.drivereplica.net.UnifiedOffersResponse

/** Tipo de pedido: exclusivo (so este motorista) ou Radar (varios ao mesmo tempo). */
enum class OfferKind { EXCLUSIVE, RADAR }

/** Cartão da proposta (vídeo 2026-10-29): produto, preço, totais, recolha, viagem e tempo para aceitar. */
data class OfferCard(
    val uuid: String,
    val product: String,
    val price: String,
    /** "34 min • 13,4 km": recolha + viagem somadas, como na referência. Nulo se o servidor não as enviar. */
    val totals: String?,
    val pickupLine: String,
    val pickupAddress: String,
    val tripLine: String?,
    val dropoffAddress: String?,
    val acceptWindowS: Int,
    val expiresAtMs: Long,
    val pickup: Pair<Double, Double>? = null,
    val dropoff: Pair<Double, Double>? = null,
    /** Exclusivo ou Radar (etiqueta "Exclusivo"/"Radar" no cartão). */
    val kind: OfferKind = OfferKind.EXCLUSIVE,
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
    /** Tempo grátis de espera na recolha (s), do servidor; o ecrã faz a contagem decrescente. */
    val waitFreeSec: Long? = null,
    val pin: PinTask?,
    /** Morada da recolha (2.ª secção do painel enquanto se vai buscar o passageiro). */
    val pickupAddress: String? = null,
    /** Cidade da paragem ("Lisboa"), como no painel do vídeo de 2026-10-30. */
    val city: String? = null,
    /** Nome do produto ("UberX Priority"), para o botão "Começar/Concluir <produto>". */
    val product: String? = null,
    /** Destino final, para desenhar o 2.º leg do percurso (vermelho) na ida à recolha. */
    val dropoffLat: Double? = null,
    val dropoffLng: Double? = null,
    /** Coordenadas da recolha, para o pino verde da fase 1 (vídeo 2026-10-30). */
    val pickupLat: Double? = null,
    val pickupLng: Double? = null,
    /** Telefone do passageiro, para o botão de chamada do ecrã de espera. */
    val riderPhone: String? = null,
    /** Destino final por extenso (folha de itinerário, campo "Destination"). */
    val dropoffAddress: String? = null,
    /** Hora de aceitação visualizável (folha de itinerário, campo "Time"). Epoch em segundos. */
    val acceptedAtSec: Long? = null,
    /** Hora de início da viagem. Epoch em segundos. */
    val startedAtSec: Long? = null,
    /** Nome do condutor (bloco "Driver" da folha de itinerário). */
    val driverName: String? = null,
    /** Matrícula do veículo (bloco "Driver"). */
    val vehiclePlate: String? = null,
    /** Lotação do veículo (bloco "Driver"). */
    val vehicleCapacity: Int? = null,
)

/** Resumo no fim da viagem (ganhos: captura 011/062 mostra o total da semana; o da viagem vem de earnings/get-trip). */
data class TripSummary(val tripUuid: String, val total: String, val lines: List<Pair<String, String>>)

/**
 * Modo Destino (lupa do mapa): o ponto para onde o motorista quer ir. Com isto ligado o
 * servidor só lhe oferece viagens cujo destino fica dentro de [radiusKm].
 */
data class DestinationMode(
    val enabled: Boolean = false,
    val latitude: Double? = null,
    val longitude: Double? = null,
    val label: String = "",
    val filtersLeft: Int = 0,
    val filtersTotal: Int = 0,
    val radiusKm: Double = 0.0,
)

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
            totals = model?.getAsJsonObject("tripTotals")?.str("shortString"),
            pickupLine = pickupLine,
            pickupAddress = title("pickup").orEmpty(),
            tripLine = texts.firstOrNull { it.startsWith("Viagem de") },
            dropoffAddress = title("dropoff"),
            acceptWindowS = model?.get("acceptWindow")?.takeIf { it.isJsonPrimitive }?.asDouble?.toInt() ?: 20,
            expiresAtMs = expires,
            pickup = coord("pickup"),
            dropoff = coord("dropoff"),
            kind = if (model?.str("offerKind") == "radar") OfferKind.RADAR else OfferKind.EXCLUSIVE,
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
        var waitFree: Long? = null
        scope.nonBlockingTasks.orEmpty().forEach { t ->
            val (type, body) = taskData(t.driverTaskDataUnion)
            when (type) {
                "locationTaskData" -> if (address == null) {
                    lat = body?.get("latitude")?.asDouble
                    lng = body?.get("longitude")?.asDouble
                    address = body?.str("title")
                }
                "waitTimeTaskData" -> {
                    waitStart = body?.get("startTimeSec")?.asDouble?.toLong()
                    waitFree = body?.get("freeWaitSec")?.takeIf { it.isJsonPrimitive }?.asDouble?.toLong()
                }
            }
        }
        val pin = scope.blockingTasks.orEmpty().firstNotNullOfOrNull { t ->
            val (type, body) = taskData(t.driverTaskDataUnion)
            if (type == "pinVerificationTaskData" && body != null) pinTask(body, t.isCompleted == true) else null
        }
        // tripInfo: morada da recolha, cidade e produto (2.ª secção do painel, vídeo 2026-10-30).
        val tripInfo = completion.coalescedDataUnion?.let { c ->
            c.getAsJsonObject(c.str("type").orEmpty())?.getAsJsonObject("tripInfo")
        }
        val phase = when {
            kind == "dropoffTaskData" -> TripPhase.ON_TRIP
            waitStart != null -> TripPhase.AT_PICKUP
            else -> TripPhase.TO_PICKUP
        }
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
            waitFreeSec = waitFree,
            pin = pin,
            pickupAddress = tripInfo?.str("pickupAddress"),
            city = tripInfo?.str("city"),
            product = tripInfo?.str("productName"),
            dropoffLat = tripInfo?.get("dropoffLat")?.takeIf { it.isJsonPrimitive }?.asDouble,
            dropoffLng = tripInfo?.get("dropoffLng")?.takeIf { it.isJsonPrimitive }?.asDouble,
            pickupLat = tripInfo?.get("pickupLat")?.takeIf { it.isJsonPrimitive }?.asDouble,
            pickupLng = tripInfo?.get("pickupLng")?.takeIf { it.isJsonPrimitive }?.asDouble,
            riderPhone = tripInfo?.str("riderPhone"),
            dropoffAddress = tripInfo?.str("dropoffAddress"),
            acceptedAtSec = tripInfo?.get("acceptedAt")?.takeIf { it.isJsonPrimitive }?.asDouble?.toLong(),
            startedAtSec = tripInfo?.get("startedAt")?.takeIf { it.isJsonPrimitive }?.asDouble?.toLong(),
            driverName = tripInfo?.str("driverName"),
            vehiclePlate = tripInfo?.str("vehiclePlate"),
            vehicleCapacity = tripInfo?.get("vehicleCapacity")?.takeIf { it.isJsonPrimitive }?.asInt,
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
