package com.qolari.drivereplica

import com.qolari.drivereplica.drive.NavStop
import com.qolari.drivereplica.drive.Navigation
import com.qolari.drivereplica.net.RouteStep
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Fase 2 — painel de navegação até à recolha (vídeo 2026-10-30, 0:00→1:52).
 *
 * Fixa as regras que o vídeo mostra e que o clone tem de respeitar:
 *  - a 1.ª secção diz o NOME DA VIA + "em direção a" + destino (não "Vire à esquerda");
 *  - a distância vem partida em número grande + unidade pequena;
 *  - a 2.ª secção alterna entre a próxima manobra e a paragem;
 *  - as distâncias arredondam a 5 m abaixo de 100 m (140, 50, 40, 30, 25, 20).
 */
class NavigationPanelTest {

    private fun step(
        maneuver: String = "",
        road: String = "",
        short: String = "Vire à esquerda",
        meters: Double,
        lat: Double? = null,
        lng: Double? = null,
    ) = RouteStep(maneuver, road, short, short, meters, 10.0, lat, lng, null)

    private val stop = NavStop("Praça Marquês de Pombal", "Lisboa", "pickup")

    @Test
    fun firstSectionShowsTheRoadAndTheDestination() {
        val steps = listOf(
            step("", "Avenida Duque de Loulé", meters = 140.0),
            step("turn-right", "Praça do Marquês de Pombal", meters = 200.0),
        )
        val nav = Navigation.build(steps, null, null, null, 340.0, 120.0, stop = stop)!!
        // Sem GPS o foco é o passo 0, mas como é "em frente" mostra-se a viragem seguinte.
        assertEquals("turn-right", nav.current!!.maneuver)
        // A via é onde o motorista está, o destino é a rua da manobra — não repetem.
        assertEquals("Avenida Duque de Loulé", nav.current!!.via)
        assertEquals("Praça do Marquês de Pombal", nav.current!!.toward)
    }

    @Test
    fun distanceIsSplitIntoValueAndUnit() {
        val nav = Navigation.build(
            listOf(step("turn-right", "Rua X", meters = 140.0)),
            null, null, null, 140.0, 30.0, stop = stop,
        )!!
        assertEquals("140", nav.current!!.distanceValue)
        assertEquals("m", nav.current!!.distanceUnit)

        val km = Navigation.build(
            listOf(step("turn-right", "Rua X", meters = 1200.0)),
            null, null, null, 1200.0, 300.0, stop = stop,
        )!!
        assertEquals("1,2", km.current!!.distanceValue)
        assertEquals("km", km.current!!.distanceUnit)
    }

    @Test
    fun distancesRoundToFiveMetresBelowOneHundred() {
        // O vídeo mostra 140, 50, 40, 30, 25 e 20 m — nunca saltos de 10 abaixo dos 100 m.
        assertEquals("140 m", Navigation.fmtDistance(137.0))
        assertEquals("25 m", Navigation.fmtDistance(24.0))
        assertEquals("20 m", Navigation.fmtDistance(22.0))
        assertEquals("50 m", Navigation.fmtDistance(48.0))
        assertEquals("1,2 km", Navigation.fmtDistance(1234.0))
    }

    @Test
    fun secondSectionShowsTheNextManeuverWhileOneExists() {
        val steps = listOf(
            step("", "Avenida Duque de Loulé", meters = 140.0),
            step("turn-right", "Praça do Marquês", meters = 200.0),
            step("turn-left", "Rua Castilho", meters = 300.0),
        )
        val nav = Navigation.build(steps, null, null, null, 640.0, 200.0, stop = stop)!!
        assertFalse("há outra manobra à frente: mostra a manobra", nav.secondaryIsStop)
    }

    @Test
    fun secondSectionShowsTheStopWhenTheManeuverIsTheLast() {
        val steps = listOf(step("turn-right", "Avenida da Liberdade", meters = 60.0))
        val nav = Navigation.build(steps, null, null, null, 60.0, 20.0, stop = stop)!!
        assertTrue("última manobra: mostra a paragem", nav.secondaryIsStop)
        assertEquals("Praça Marquês de Pombal", nav.stop!!.address)
        assertEquals("Lisboa", nav.stop!!.city)
    }

    @Test
    fun stopIsSquareGreenForPickupAndRedForDropoff() {
        assertEquals("pickup", stop.kind)
        assertEquals("dropoff", NavStop("Destino", "Lisboa", "dropoff").kind)
    }

    @Test
    fun noManeuversMeansNoPanel() {
        assertNull(Navigation.build(emptyList(), null, null, null, 0.0, 0.0, stop = stop))
        assertNull(Navigation.build(null, null, null, null, 0.0, 0.0, stop = stop))
    }

    @Test
    fun roadNameReplacesTheInstructionText() {
        // O painel do vídeo mostra "Praça do Marquês de Pombal", não "Vire à direita".
        val nav = Navigation.build(
            listOf(step("turn-right", "Praça do Marquês de Pombal", meters = 50.0)),
            null, null, null, 50.0, 15.0, stop = stop,
        )!!
        assertEquals("Praça do Marquês de Pombal", nav.current!!.road)
    }

    @Test
    fun aManeuverWithoutOsmNameFallsBackToTheInstruction() {
        val nav = Navigation.build(
            listOf(step("turn-right", "", short = "Vire à direita", meters = 40.0)),
            null, null, null, 40.0, 12.0, stop = stop,
        )!!
        assertEquals("Vire à direita", nav.current!!.road)
    }
}
