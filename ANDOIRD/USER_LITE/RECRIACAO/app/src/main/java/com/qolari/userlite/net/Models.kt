package com.qolari.userlite.net

import com.google.gson.annotations.SerializedName

data class TokenResponse(
    val accessToken: String? = null,
    @SerializedName("access_token") val accessTokenSnake: String? = null,
    val refreshToken: String? = null,
    @SerializedName("refresh_token") val refreshTokenSnake: String? = null,
) {
    val token: String? get() = accessToken ?: accessTokenSnake
    val refresh: String? get() = refreshToken ?: refreshTokenSnake
}

data class CityInfo(val name: String = "", val currency: String = "EUR")

data class Payment(
    val id: String = "cash",
    val label: String = "Dinheiro",
    val detail: String = "",
)

data class SessionResponse(
    val riderUUID: String = "",
    val firstName: String = "",
    val name: String = "",
    val phone: String = "",
    val email: String = "",
    val rating: Double = 5.0,
    val city: CityInfo = CityInfo(),
    val memberSince: Long = 0,
    val payment: Payment = Payment(),
)

data class Place(
    val id: String = "",
    val name: String = "",
    val line1: String = "",
    val line2: String = "",
    val full: String = "",
    val lat: Double = 0.0,
    val lng: Double = 0.0,
    val distance_m: Int? = null,
) {
    val address: String get() = listOf(line1, line2).filter { it.isNotBlank() }.joinToString(", ").ifBlank { full }
}

data class Suggestion(
    val id: String = "",
    val title: String = "",
    val subtitle: String = "",
    val icon: String = "",
)

data class PromoCard(val id: String = "", val title: String = "", val subtitle: String = "", val action: String = "")

data class Cash(val cents: Int = 0, val label: String = "0,00 €", val currency: String = "EUR")

data class HomeResponse(
    val greeting: String = "",
    val firstName: String = "",
    val headline: String = "",
    val etaMin: Int = 1,
    val savedPlace: Place = Place(),
    val city: String = "",
    val cash: Cash = Cash(),
    val suggestions: List<Suggestion> = emptyList(),
    val promos: List<PromoCard> = emptyList(),
)

data class PlacesResponse(val places: List<Place> = emptyList())

data class UpdateAccount(
    val firstName: String,
    val lastName: String = "",
    val email: String = "",
)

data class HomePlaceRequest(val placeId: String)

data class RateRequest(val stars: Int, val comment: String = "")

data class SavedPlaceResponse(val savedPlace: Place = Place())

data class RoutePoint(val lat: Double = 0.0, val lng: Double = 0.0, val address: String = "")

data class QuoteRequest(val pickup: RoutePoint, val dropoff: RoutePoint)

data class QuoteProduct(
    val id: Int = 0,
    val uuid: String = "",
    val name: String = "",
    val description: String = "",
    val capacity: Int = 4,
    val etaMin: Int = 1,
    val cents: Int = 0,
    val price: String = "",
    val currency: String = "EUR",
    val distanceKm: Double = 0.0,
    val durationMin: Int = 0,
    val fastest: Boolean = false,
)

data class QuotePromo(val code: String = "", val description: String = "")

data class QuoteResponse(
    val pickup: RoutePoint = RoutePoint(),
    val dropoff: RoutePoint = RoutePoint(),
    val products: List<QuoteProduct> = emptyList(),
    val payment: Payment = Payment(),
    val promo: QuotePromo? = null,
)

data class RequestTrip(
    val pickup: RoutePoint,
    val dropoff: RoutePoint,
    val productId: Int,
    val payment: String = "cash",
    val promoCode: String? = null,
)

data class Vehicle(
    val make: String = "",
    val model: String = "",
    val color: String = "",
    val colorHex: String = "#222222",
    val plate: String = "",
    val label: String = "",
)

data class TripDriver(
    val uuid: String = "",
    val name: String = "",
    val rating: Double = 5.0,
    val phone: String = "",
    val lat: Double? = null,
    val lng: Double? = null,
    val vehicle: Vehicle? = null,
)

data class Fare(
    val cents: Int = 0,
    val label: String = "",
    val currency: String = "EUR",
    val discount: String? = null,
)

data class Trip(
    val uuid: String = "",
    val state: String = "requested",
    val createdAt: Long = 0,
    val product: TripProduct = TripProduct(),
    val pickup: RoutePoint = RoutePoint(),
    val dropoff: RoutePoint = RoutePoint(),
    val pin: String? = null,
    val driver: TripDriver? = null,
    val driverEtaMin: Int? = null,
    val tripEtaMin: Int? = null,
    val fare: Fare = Fare(),
    val payment: String = "cash",
    val canCancel: Boolean = false,
    val canRate: Boolean = false,
    val myRating: Int? = null,
    val cancelledBy: String? = null,
    val cancelReason: String? = null,
    val distanceKm: Double = 0.0,
    val durationMin: Int = 0,
)

data class TripProduct(val id: Int = 0, val name: String = "")

data class TripResponse(val trip: Trip? = null)

data class HistoryTrip(
    val uuid: String = "",
    val date: String = "",
    val state: String = "",
    val pickup: String = "",
    val dropoff: String = "",
    val product: String = "",
    val fare: Fare = Fare(),
    val distanceKm: Double = 0.0,
)

data class HistoryResponse(val trips: List<HistoryTrip> = emptyList())

data class WalletResponse(
    val cash: Cash = Cash(),
    val payment: Payment = Payment(),
    val profiles: List<Payment> = emptyList(),
)

data class PromotionsResponse(
    val applied: List<AppliedPromo> = emptyList(),
    val hint: String = "",
)

data class AppliedPromo(val code: String = "", val description: String = "", val valid: Boolean = true)

data class ApiError(val code: String? = null, val message: String? = null)
