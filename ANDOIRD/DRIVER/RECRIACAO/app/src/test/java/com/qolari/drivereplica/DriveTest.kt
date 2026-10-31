package com.qolari.drivereplica

import com.google.gson.Gson
import com.google.gson.JsonObject
import com.qolari.drivereplica.drive.AcceptResult
import com.qolari.drivereplica.drive.ActiveTrip
import com.qolari.drivereplica.drive.DriveParser
import com.qolari.drivereplica.drive.DriveSource
import com.qolari.drivereplica.drive.DriveStage
import com.qolari.drivereplica.drive.DriveViewModel
import com.qolari.drivereplica.drive.OfferCard
import com.qolari.drivereplica.drive.TripPhase
import com.qolari.drivereplica.drive.TripSummary
import com.qolari.drivereplica.net.DriverTasksResponse
import com.qolari.drivereplica.net.UnifiedOffersResponse
import java.io.File
import java.io.IOException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

/**
 * Lote 4: proposta e viagem. Os JSON em `src/test/resources/drive` são respostas REAIS do backend (geradas por
 * `tools/gen_drive_fixtures.py`), por isso o parser é validado contra o contrato e não contra o que imaginámos.
 */
@OptIn(ExperimentalCoroutinesApi::class)
class DriveTest {

    private val gson = Gson()

    private fun text(name: String) = File("src/test/resources/drive/$name").readText()
    private fun tasks(name: String) = gson.fromJson(text(name), DriverTasksResponse::class.java).driverTasks
    private fun offers() = gson.fromJson(text("offer.json"), UnifiedOffersResponse::class.java)

    @Before fun setUp() = Dispatchers.setMain(UnconfinedTestDispatcher())

    @After fun tearDown() = Dispatchers.resetMain()

    // ---- parser (respostas reais do backend) ----

    @Test
    fun offerCardComesFromTheUnifiedOffers() {
        val o = DriveParser.offer(offers(), nowMs = 0)!!
        assertTrue(o.price.contains("€"))
        assertTrue(o.product.isNotBlank())
        assertTrue(o.pickupLine.contains("de distância"))
        assertTrue(o.pickupAddress.isNotBlank())
        assertTrue(o.tripLine!!.startsWith("Viagem de"))
        assertEquals("Aeroporto", o.dropoffAddress)
        assertTrue(o.acceptWindowS > 0)
    }

    @Test
    fun anExpiredOfferIsDropped() {
        assertNull(DriveParser.offer(offers(), nowMs = Long.MAX_VALUE))
    }

    @Test
    fun emptyOffersGiveNoCard() {
        assertNull(DriveParser.offer(gson.fromJson("""{"data":{"offers":[]}}""", UnifiedOffersResponse::class.java)))
    }

    @Test
    fun noTripWhenThereAreNoTaskScopes() {
        assertNull(DriveParser.trip(tasks("tasks_idle.json")))
    }

    @Test
    fun acceptedTripIsToPickup() {
        val t = DriveParser.trip(tasks("tasks_to_pickup.json"))!!
        assertEquals(TripPhase.TO_PICKUP, t.phase)
        assertEquals("Ana", t.riderName)
        assertTrue(t.address.isNotBlank())
        assertNotNull(t.latitude)
        assertNotNull(t.fare)
        assertNull(t.waitStartSec); assertNull(t.pin)
    }

    /**
     * Folha de itinerário: o destino tem de ser o do servidor, não a recolha. Era o bug que
     * mostrava a mesma morada em "From" e "Destination" (auditoria de 2026-10-31, F-01).
     */
    @Test
    fun theTripCarriesTheDropoffAddressApartFromThePickup() {
        val t = DriveParser.trip(tasks("tasks_to_pickup.json"))!!
        assertEquals("Praca Marques de Pombal, Lisboa", t.pickupAddress)
        assertEquals("Av. Lusiada, Lisboa", t.dropoffAddress)
        assertTrue("o destino não pode ser a recolha", t.pickupAddress != t.dropoffAddress)
    }

    /** A folha de itinerário mostra a hora da viagem e o condutor, não a hora de abrir o ecrã. */
    @Test
    fun theTripCarriesTheTripTimeAndTheDriver() {
        val t = DriveParser.trip(tasks("tasks_to_pickup.json"))!!
        assertEquals(1793440000L, t.acceptedAtSec)
        assertNull("ainda não arrancou", t.startedAtSec)
        assertEquals("Carlos Silva", t.driverName)
        assertEquals("AA-11-BB", t.vehiclePlate)
        assertEquals(4, t.vehicleCapacity)
    }

    /**
     * Espera na recolha: o contador é uma contagem decrescente do tempo grátis (vídeo 2026-10-30,
     * 1:44 → 1:05) e o tempo grátis vem do servidor (`wait_free_s`, 2 min por omissão).
     */
    @Test
    fun theWaitTimerCountsDownFromTheFreeWindow() {
        val t = DriveParser.trip(tasks("tasks_at_pickup.json"))!!
        assertNotNull("chegou: há temporizador", t.waitStartSec)
        assertEquals("2 min de espera grátis", 120L, t.waitFreeSec)
    }

    @Test
    fun arrivedTripHasTheWaitTimer() {
        val t = DriveParser.trip(tasks("tasks_at_pickup.json"))!!
        assertEquals(TripPhase.AT_PICKUP, t.phase)
        assertNotNull(t.waitStartSec)
        assertNull("sem PIN pedido pelo passageiro não há tarefa de PIN", t.pin)
    }

    @Test
    fun arrivedTripWithPinCarriesTheServerTexts() {
        val pin = DriveParser.trip(tasks("tasks_at_pickup_pin.json"))!!.pin!!
        assertEquals("4821", pin.pin)
        assertEquals(4, pin.digits)
        assertEquals(3, pin.maxAttempts)
        assertEquals(3, pin.errors.size)
        assertTrue(pin.title.startsWith("Peça o PIN"))
        assertFalse(pin.verified)
    }

    @Test
    fun verifiedPinIsReportedAsDone() {
        assertTrue(DriveParser.trip(tasks("tasks_pin_verified.json"))!!.pin!!.verified)
    }

    @Test
    fun tripInProgressIsOnTripWithTheDropoff() {
        val t = DriveParser.trip(tasks("tasks_on_trip.json"))!!
        assertEquals(TripPhase.ON_TRIP, t.phase)
        assertEquals("Aeroporto", t.address)
    }

    @Test
    fun earningsSummaryHasTotalAndLines() {
        val s = DriveParser.summary("u", gson.fromJson(text("earnings_trip.json"), JsonObject::class.java))
        assertTrue(s.total.contains("€"))
        assertTrue(s.lines.isNotEmpty())
    }

    // ---- ciclo no ViewModel ----

    private val offer = OfferCard("o1", "UberX", "7,04 €", "22 min • 12,1 km", "2 min (0,7 km) de distância", "Rossio", "Viagem de 20 min (11,4 km)", "Aeroporto", 20, 0, 38.7 to -9.1, 38.8 to -9.2)
    private fun trip(phase: TripPhase, pin: com.qolari.drivereplica.drive.PinTask? = null, wait: Long? = null) =
        ActiveTrip(
            uuid = "t1", phase = phase, riderName = "Ana", riderRating = 5.0, address = "Rossio",
            latitude = 38.7, longitude = -9.1, fare = "7,04 €",
            waitStartSec = wait, pin = pin,
        )
    private val pinTask = com.qolari.drivereplica.drive.PinTask("4821", 3, "Peça o PIN", "…", 4, listOf("e1", "e2", "e3"), false)

    private class FakeDrive : DriveSource {
        var offer: OfferCard? = null
        var trip: ActiveTrip? = null
        var fail = false
        val calls = mutableListOf<String>()
        override suspend fun offers() = Result.success(offer)
        override suspend fun tasks() = if (fail) Result.failure(IOException("x")) else Result.success(trip)
        override suspend fun accept(offerUuid: String): Result<AcceptResult> { calls += "accept"; return Result.success(AcceptResult(trip)) }
        override suspend fun reject(offerUuid: String, expired: Boolean): Result<Unit> { calls += if (expired) "expire" else "reject"; return Result.success(Unit) }
        override suspend fun arrive(tripUuid: String): Result<ActiveTrip?> { calls += "arrive"; return Result.success(trip) }
        override suspend fun confirmPin(tripUuid: String): Result<Unit> { calls += "pin"; return Result.success(Unit) }
        override suspend fun begin(tripUuid: String, pin: String?): Result<ActiveTrip?> { calls += "begin:$pin"; return Result.success(trip) }
        override suspend fun end(tripUuid: String): Result<Unit> { calls += "end"; return Result.success(Unit) }
        override suspend fun rate(tripUuid: String, stars: Int): Result<Unit> { calls += "rate:$stars"; return Result.success(Unit) }
        override suspend fun summary(tripUuid: String) = Result.success(TripSummary(tripUuid, "5,00 €", emptyList()))
        override suspend fun uploadPosition(latitude: Double, longitude: Double): Result<Unit> { calls += "pos"; return Result.success(Unit) }
        var routeFails = false
        override suspend fun route(fromLat: Double, fromLng: Double, toLat: Double, toLng: Double): Result<List<Pair<Double, Double>>> {
            calls += "route"
            return if (routeFails) Result.failure(IOException("x")) else Result.success(listOf(fromLat to fromLng, toLat to toLng))
        }
        override suspend fun routeWithSteps(
            fromLat: Double, fromLng: Double, toLat: Double, toLng: Double,
        ): Result<com.qolari.drivereplica.net.RouteResponse?> = Result.success(null)
        override suspend fun lastPosition(): Pair<Double, Double>? = null
    /** "Parar novos pedidos": guarda o que foi pedido e devolve o estado resultante. */
    var pausedState = false
    override suspend fun pauseDispatch(paused: Boolean): Result<Boolean> {
        calls += "pause:$paused"
        pausedState = paused
        return Result.success(paused)
    }
    /** Modo Destino: guarda o que foi pedido e devolve o estado com os filtros. */
    var destinationState = com.qolari.drivereplica.drive.DestinationMode()
    override suspend fun setDestination(
        lat: Double?, lng: Double?, label: String,
    ): Result<com.qolari.drivereplica.drive.DestinationMode> {
        calls += "dest:$lat,$lng,$label"
        destinationState = if (lat == null || lng == null) {
            destinationState.copy(enabled = false, latitude = null, longitude = null, label = "")
        } else {
            destinationState.copy(
                enabled = true, latitude = lat, longitude = lng, label = label,
                filtersLeft = (destinationState.filtersLeft - 1).coerceAtLeast(0),
            )
        }
        return Result.success(destinationState)
    }
    override suspend fun destinationState(): Result<com.qolari.drivereplica.drive.DestinationMode> =
        Result.success(destinationState)
        override suspend fun sendMessage(tripUuid: String, text: String): Result<Unit> {
            calls += "msg:$text"; return Result.success(Unit)
        }
        override suspend fun cancel(tripUuid: String, reason: String): Result<Unit> {
            calls += "cancel:$reason"; return Result.success(Unit)
        }
    }

    private fun vm(src: FakeDrive, loc: (() -> Pair<Double, Double>?) = { null }) = DriveViewModel(src, loc, pollIntervalMs = 3_600_000, autoPoll = false)

    private suspend fun DriveViewModel.online() { setOnline(true); pollOnce() }

    @Test
    fun offlineDoesNotPoll() = runTest {
        val src = FakeDrive().apply { offer = offer() }
        val vm = vm(src)
        vm.pollOnce()
        assertEquals(DriveStage.IDLE, vm.state.value.stage)
    }

    @Test
    fun anOfferShowsTheOfferStageAndAcceptingMovesToPickup() = runTest {
        val src = FakeDrive().apply { offer = offer() }
        val vm = vm(src); vm.online()
        assertEquals(DriveStage.OFFER, vm.state.value.stage)
        src.trip = trip(TripPhase.TO_PICKUP); src.offer = null
        vm.accept()
        assertEquals(DriveStage.TO_PICKUP, vm.state.value.stage)
        assertNull(vm.state.value.offer)
        assertTrue("accept" in src.calls)
    }

    private fun offer() = offer

    @Test
    fun decliningClearsTheOfferAndTellsTheServer() = runTest {
        val src = FakeDrive().apply { offer = offer() }
        val vm = vm(src); vm.online()
        src.offer = null
        vm.decline()
        assertEquals(DriveStage.IDLE, vm.state.value.stage)
        assertTrue("reject" in src.calls)
    }

    @Test
    fun anExpiredOfferIsReportedAsExpired() = runTest {
        val src = FakeDrive().apply { offer = offer() }
        val vm = vm(src); vm.online()
        src.offer = null
        vm.expire()
        assertTrue("expire" in src.calls)
        assertEquals(DriveStage.IDLE, vm.state.value.stage)
    }

    @Test
    fun anActiveTripWinsOverAnOfferAndSurvivesReopening() = runTest {
        val src = FakeDrive().apply { offer = offer(); trip = trip(TripPhase.ON_TRIP) }
        val vm = vm(src); vm.online()
        assertEquals(DriveStage.ON_TRIP, vm.state.value.stage)
        assertNull(vm.state.value.offer)
    }

    @Test
    fun pickupNeedsTheRightPinBeforeStarting() = runTest {
        val src = FakeDrive().apply { trip = trip(TripPhase.AT_PICKUP, pinTask, wait = 1) }
        val vm = vm(src); vm.online()
        vm.startTrip()
        assertTrue("sem PIN verificado não inicia", src.calls.none { it.startsWith("begin") })
        vm.submitPin("0000")
        assertEquals("e1", vm.state.value.pinError)
        assertFalse(vm.state.value.pinVerified)
        vm.submitPin("1111")
        assertEquals("e2", vm.state.value.pinError)
        vm.submitPin("4821")
        assertTrue(vm.state.value.pinVerified)
        assertTrue("pin" in src.calls)
        src.trip = trip(TripPhase.ON_TRIP)
        vm.startTrip()
        assertTrue("begin:4821" in src.calls)
        assertEquals(DriveStage.ON_TRIP, vm.state.value.stage)
    }

    @Test
    fun noPinTaskMeansTheTripStartsDirectly() = runTest {
        val src = FakeDrive().apply { trip = trip(TripPhase.AT_PICKUP, null, wait = 1) }
        val vm = vm(src); vm.online()
        src.trip = trip(TripPhase.ON_TRIP)
        vm.startTrip()
        assertTrue("begin:null" in src.calls)
    }

    @Test
    fun attemptsAreLimitedToTheServerMaximum() = runTest {
        val src = FakeDrive().apply { trip = trip(TripPhase.AT_PICKUP, pinTask, wait = 1) }
        val vm = vm(src); vm.online()
        repeat(5) { vm.submitPin("0000") }
        assertEquals(3, vm.state.value.pinAttempts)
        vm.submitPin("4821")
        assertFalse("depois do máximo de tentativas já não aceita", vm.state.value.pinVerified)
    }

    @Test
    fun finishingTheTripGoesToRatingWithTheSummaryThenBackToIdle() = runTest {
        val src = FakeDrive().apply { trip = trip(TripPhase.ON_TRIP) }
        val vm = vm(src); vm.online()
        src.trip = null
        vm.finishTrip()
        assertEquals(DriveStage.RATING, vm.state.value.stage)
        assertEquals("5,00 €", vm.state.value.summary?.total)
        vm.pollOnce()
        assertEquals("a avaliação não desaparece com a sondagem", DriveStage.RATING, vm.state.value.stage)
        vm.rate(4)
        assertEquals(DriveStage.IDLE, vm.state.value.stage)
        assertTrue("rate:4" in src.calls)
    }

    @Test
    fun skippingTheRatingSendsNothing() = runTest {
        val src = FakeDrive().apply { trip = trip(TripPhase.ON_TRIP) }
        val vm = vm(src); vm.online()
        src.trip = null
        vm.finishTrip()
        vm.skipRating()
        assertTrue(src.calls.none { it.startsWith("rate") })
        assertEquals(DriveStage.IDLE, vm.state.value.stage)
    }

    @Test
    fun aFailedPollKeepsTheCurrentState() = runTest {
        val src = FakeDrive().apply { trip = trip(TripPhase.TO_PICKUP) }
        val vm = vm(src); vm.online()
        src.fail = true
        vm.pollOnce()
        assertEquals(DriveStage.TO_PICKUP, vm.state.value.stage)
    }

    @Test
    fun theDevicePositionIsUploadedWhileOnline() = runTest {
        val src = FakeDrive()
        val vm = vm(src) { 38.7 to -9.1 }
        vm.online()
        assertTrue("pos" in src.calls)
    }

    @Test
    fun goingOfflineResetsEverything() = runTest {
        val src = FakeDrive().apply { offer = offer() }
        val vm = vm(src); vm.online()
        vm.setOnline(false)
        assertEquals(DriveStage.IDLE, vm.state.value.stage)
        assertFalse(vm.state.value.online)
    }

    @Test
    fun theOfferCoordinatesComeFromTheBackendResponse() {
        val o = DriveParser.offer(offers(), nowMs = 0)!!
        assertNotNull(o.pickup); assertNotNull(o.dropoff)
        assertEquals(38.7742, o.dropoff!!.first, 0.001)
    }

    @Test
    fun aNewOfferFetchesItsRouteOnce() = runTest {
        val src = FakeDrive().apply { offer = offer() }
        val vm = vm(src); vm.online()
        assertEquals(2, vm.state.value.route.size)
        vm.pollOnce()
        assertEquals("a mesma proposta não pede a rota outra vez", 1, src.calls.count { it == "route" })
    }

    @Test
    fun stoppingNewRequestsKeepsTheDriverOnline() = runTest {
        val src = FakeDrive().apply { trip = trip(TripPhase.TO_PICKUP) }
        val vm = vm(src); vm.online()
        vm.setPaused(true)
        // O estado vem do servidor: "parado" e online com available=false.
        assertTrue(vm.state.value.paused)
        assertTrue("continua online", vm.state.value.online)
        assertEquals(listOf("pause:true"), src.calls.filter { it.startsWith("pause") })
    }

    @Test
    fun resumingRequestsPutsTheDriverBackInTheDispatch() = runTest {
        val src = FakeDrive().apply { trip = trip(TripPhase.TO_PICKUP); pausedState = true }
        val vm = vm(src); vm.online()
        vm.setPaused(false)
        assertFalse(vm.state.value.paused)
        assertFalse(src.pausedState)
    }

    /** Modo Destino: marcar consome um filtro e liga; desligar não gasta nem devolve. */
    @Test
    fun settingADestinationTurnsTheModeOnAndSpendsAFilter() = runTest {
        val src = FakeDrive()
        src.destinationState = src.destinationState.copy(filtersLeft = 2, filtersTotal = 2)
        val vm = vm(src); vm.online()
        vm.setDestination(38.7106, -9.1422, "Baixa-Chiado")
        val d = vm.state.value.destination
        assertTrue("liga com o destino marcado", d.enabled)
        assertEquals(38.7106, d.latitude)
        assertEquals("Baixa-Chiado", d.label)
        assertEquals("gastou um dos 2 filtros", 1, d.filtersLeft)
        assertTrue(src.calls.any { it.startsWith("dest:38.7106") })
    }

    @Test
    fun turningTheDestinationModeOffDoesNotSpendFilters() = runTest {
        val src = FakeDrive()
        src.destinationState = src.destinationState.copy(filtersLeft = 1, filtersTotal = 2)
        val vm = vm(src); vm.online()
        vm.setDestination(null, null, "")
        assertFalse(vm.state.value.destination.enabled)
        assertEquals("desligar não gasta filtro", 1, vm.state.value.destination.filtersLeft)
    }

    @Test
    fun aFailedRouteStillShowsTheOffer() = runTest {
        val src = FakeDrive().apply { offer = offer(); routeFails = true }
        val vm = vm(src); vm.online()
        assertEquals(DriveStage.OFFER, vm.state.value.stage)
        assertTrue(vm.state.value.route.isEmpty())
    }
}
