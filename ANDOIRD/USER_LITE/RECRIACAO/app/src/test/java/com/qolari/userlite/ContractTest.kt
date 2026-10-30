package com.qolari.userlite

import com.google.gson.Gson
import com.qolari.userlite.config.AppConfig
import com.qolari.userlite.config.Environment
import com.qolari.userlite.net.HistoryResponse
import com.qolari.userlite.net.HomeResponse
import com.qolari.userlite.net.QuoteResponse
import com.qolari.userlite.net.TripResponse
import com.qolari.userlite.ui.ride.RideViewModel
import java.io.File
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/** Contrato e config: fixtures densas com a forma real do backend desenhado. */
class ContractTest {

    private val gson = Gson()

    private fun json(name: String): String =
        javaClass.classLoader!!.getResourceAsStream("contract/$name")!!.bufferedReader().readText()

    @Test
    fun homeFixtureParsesAllFields() {
        val home = gson.fromJson(json("home.json"), HomeResponse::class.java)
        assertEquals("Ana", home.firstName)
        assertTrue(home.headline.contains("3 min"))
        assertEquals("Casa", home.savedPlace.name)
        assertEquals("R. José Gomes Ferreira", home.savedPlace.line1)
        assertEquals(1, home.suggestions.size)
        assertEquals("bemvindo", home.promos.first().id)
    }

    @Test
    fun quoteFixtureParsesProductsAndPayment() {
        val quote = gson.fromJson(json("quote.json"), QuoteResponse::class.java)
        assertEquals(2, quote.products.size)
        assertEquals("Qolari X", quote.products[0].name)
        assertTrue(quote.products[0].fastest)
        assertFalse(quote.products[1].fastest)
        assertEquals("7,93 €", quote.products[0].price)
        assertEquals("cash", quote.payment.id)
        assertEquals("BEMVINDO", quote.promo?.code)
        assertEquals("Praça do Rossio, Lisboa", quote.dropoff.address)
    }

    @Test
    fun tripFixtureHasDriverPinAndVehicle() {
        val trip = gson.fromJson(json("trip.json"), TripResponse::class.java).trip!!
        assertEquals("arrived", trip.state)
        assertEquals("4821", trip.pin)
        assertEquals("Carlos", trip.driver?.name)
        assertEquals("AA-00-BB", trip.driver?.vehicle?.plate)
        assertEquals(0, trip.driverEtaMin)
        assertTrue(trip.canCancel)
        assertFalse(trip.canRate)
        assertEquals("7,93 €", trip.fare.label)
    }

    @Test
    fun historyFixtureKeepsEmptyAndFilledStates() {
        val history = gson.fromJson(json("history.json"), HistoryResponse::class.java)
        assertEquals(2, history.trips.size)
        assertEquals("completed", history.trips[0].state)
        assertEquals("cancelled", history.trips[1].state)
    }

    @Test
    fun rideDraftSelectsAndResetsWithoutLeakingState() {
        val quote = gson.fromJson(json("quote.json"), QuoteResponse::class.java)
        val draft = RideViewModel()
        assertEquals("Casa, Lisboa", draft.pickup.value.address)

        draft.setQuote(quote)
        assertEquals(quote.products.first(), draft.selected.value)

        draft.select(quote.products[1])
        assertEquals(quote.products[1], draft.selected.value)

        draft.setDropoff(quote.dropoff)
        assertEquals(quote.dropoff, draft.dropoff.value)
        assertNull("mudar o destino invalida a cotação", draft.quote.value)

        draft.setQuote(quote)
        assertNotNull(draft.quote.value)
        draft.reset()
        assertNull(draft.dropoff.value)
        assertNull(draft.quote.value)
        assertNull(draft.selected.value)
    }

    @Test
    fun configHasOnePlaceForHosts() {
        assertEquals(AppConfig.environment.baseUrl, AppConfig.defaultBaseUrl)
        assertEquals("https://rider.qolari.com", Environment.SERVER.baseUrl)
        assertEquals("http://127.0.0.1:8090", Environment.USB.baseUrl)
        assertTrue(AppConfig.resolveBaseUrl("  http://10.0.0.5:8090/ ").endsWith(":8090"))
        assertEquals(AppConfig.defaultBaseUrl, AppConfig.resolveBaseUrl("  "))
    }

    @Test
    fun noHostIsHardcodedOutsideAppConfig() {
        val src = File("src/main")
        assertTrue("pasta src/main nao encontrada a partir de ${File(".").absolutePath}", src.isDirectory)
        val url = Regex("(https?|wss?)://[A-Za-z0-9.\\-]+")
        val allowed = listOf("schemas.android.com", "www.w3.org")
        val offenders = src.walkTopDown()
            .filter { it.isFile && it.extension in setOf("kt", "xml") && it.name != "AppConfig.kt" }
            .flatMap { f -> url.findAll(f.readText()).map { f.name to it.value } }
            .filter { (_, u) -> allowed.none { u.contains(it) } }
            .toList()
        assertTrue("hosts fora de AppConfig.kt: $offenders", offenders.isEmpty())
    }
}
