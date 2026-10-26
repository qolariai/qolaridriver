package com.qolari.drivereplica

import com.qolari.drivereplica.net.BalanceSummary
import com.qolari.drivereplica.net.EarningsTrip
import com.qolari.drivereplica.net.EarningsView
import com.qolari.drivereplica.ui.discover.DiscoverFilter
import com.qolari.drivereplica.ui.discover.DiscoverFixtures
import com.qolari.drivereplica.ui.discover.DiscoverKind
import com.qolari.drivereplica.ui.discover.DiscoverRow
import com.qolari.drivereplica.ui.discover.DiscoverViewModel
import com.qolari.drivereplica.ui.discover.PtDates
import com.qolari.drivereplica.ui.earnings.EarningsMapper
import com.qolari.drivereplica.ui.earnings.EarningsSource
import com.qolari.drivereplica.ui.earnings.EarningsViewModel
import com.qolari.drivereplica.ui.earnings.WeeklyEarnings
import com.qolari.drivereplica.net.NotificationsResponse
import com.qolari.drivereplica.ui.inbox.InboxMapper
import java.io.IOException
import java.time.LocalDate
import java.time.ZoneId
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

/** Lote 3: mapeamento dos ganhos, regras de Rendimentos, filtros de Descobrir e datas em português. */
@OptIn(ExperimentalCoroutinesApi::class)
class Lote3Test {

    private val utc = ZoneId.of("UTC")

    @Before fun setUp() = Dispatchers.setMain(UnconfinedTestDispatcher())

    @After fun tearDown() = Dispatchers.resetMain()

    private fun ms(date: String, hour: Int = 12): Double =
        LocalDate.parse(date).atTime(hour, 0).atZone(utc).toInstant().toEpochMilli().toDouble()

    private fun trip(at: Double, total: String) = EarningsTrip("u", "A", "B", at, total, "5,0 km", "UberX")

    // ---- Rendimentos ----

    @Test
    fun parseMoneyHandlesTheBackendFormat() {
        assertEquals(12.34f, EarningsMapper.parseMoney("12,34 €"), 0.001f)
        assertEquals(1234.5f, EarningsMapper.parseMoney("1 234,50 €"), 0.001f)
        assertEquals(-3.0f, EarningsMapper.parseMoney("-3,00 €"), 0.001f)
        assertEquals(0f, EarningsMapper.parseMoney(null), 0f)
    }

    @Test
    fun weekIsSummarisedPerDayFromItsTrips() {
        // semana de segunda 2026-10-12 a segunda 2026-10-19 (fim exclusivo)
        val view = EarningsView(
            startAt = ms("2026-10-12", 0), endAt = ms("2026-10-19", 0), formattedTotal = "50,00 €",
            formattedTripEarning = "60,00 €", formattedCommission = "-10,00 €", tripCount = 3, currencyCode = "EUR",
            trips = listOf(trip(ms("2026-10-12"), "10,00 €"), trip(ms("2026-10-12", 18), "5,50 €"), trip(ms("2026-10-14"), "20,00 €")),
        )
        val w = EarningsMapper.map(view, BalanceSummary("7,25 €", 7.25, "EUR", false), utc, LocalDate.parse("2026-10-14"))
        assertEquals("12/10 - 18/10", w.periodLabel)
        assertEquals("50,00 €", w.formattedTotal)
        assertEquals(3, w.tripCount)
        assertEquals(listOf(15.5f, 0f, 20f, 0f, 0f, 0f, 0f), w.dayTotals)
        assertEquals(2, w.todayIndex)
        assertEquals("7,25 €", w.balance)
        assertEquals(3, w.recent.size)
    }

    @Test
    fun todayOutsideTheWeekHasNoHighlight() {
        val view = EarningsView(ms("2026-10-12", 0), ms("2026-10-19", 0), "0,00 €", null, null, 0, "EUR", emptyList())
        assertEquals(-1, EarningsMapper.map(view, null, utc, LocalDate.parse("2026-11-01")).todayIndex)
    }

    private class FakeEarnings(var result: Result<WeeklyEarnings>) : EarningsSource {
        override suspend fun fetchWeek() = result
    }

    private val week = WeeklyEarnings("12/10 - 18/10", "1,00 €", 1, List(7) { 0f }, 0, null, emptyList())

    @Test
    fun earningsFailureWithoutDataShowsTheNoNetworkText() {
        val vm = EarningsViewModel(FakeEarnings(Result.failure(IOException("x"))))
        assertTrue(vm.state.value.failed); assertNull(vm.state.value.week)
    }

    @Test
    fun earningsRefreshFailureKeepsTheData() {
        val source = FakeEarnings(Result.success(week))
        val vm = EarningsViewModel(source)
        assertNotNull(vm.state.value.week)
        source.result = Result.failure(IOException("x"))
        vm.refresh()
        assertNotNull("arrastar para atualizar offline não altera nada (captura 126)", vm.state.value.week)
        assertFalse(vm.state.value.failed)
        assertFalse(vm.state.value.refreshing)
    }

    // ---- Descobrir ----

    private val today = LocalDate.parse("2026-10-16") // sexta-feira

    private fun discover() = DiscoverViewModel(today)

    private fun DiscoverViewModel.itemRows() = state.value.rows.filterIsInstance<DiscoverRow.Item>()

    @Test
    fun withoutFiltersEverythingIsShown() {
        val vm = discover()
        val rows = vm.state.value.rows
        assertEquals(DiscoverRow.Chips, rows.first())
        assertTrue(rows[1] is DiscoverRow.Promos)
        assertEquals(DiscoverFixtures.items(today).size, vm.itemRows().size)
        assertEquals(today, (rows[2] as DiscoverRow.DayHeader).date)
    }

    @Test
    fun airportsFilterKeepsOnlyAirportPeaksAndHidesPromos() {
        val vm = discover()
        vm.toggleFilter(DiscoverFilter.AIRPORTS)
        assertTrue(vm.itemRows().isNotEmpty())
        assertTrue(vm.itemRows().all { it.item.kind == DiscoverKind.AIRPORT })
        assertTrue(vm.state.value.rows.none { it is DiscoverRow.Promos })
    }

    @Test
    fun promosFilterShowsOnlyTheCards() {
        val vm = discover()
        vm.toggleFilter(DiscoverFilter.PROMOS)
        assertTrue(vm.state.value.rows.any { it is DiscoverRow.Promos })
        assertTrue(vm.itemRows().isEmpty())
    }

    @Test
    fun remindersFilterShowsOnlySavedItems() {
        val vm = discover()
        val id = vm.itemRows().first { it.item.kind == DiscoverKind.EVENT }.item.id
        vm.toggleSaved(id)
        vm.toggleFilter(DiscoverFilter.REMINDERS)
        assertEquals(listOf(id), vm.itemRows().map { it.item.id })
        assertTrue(vm.itemRows().single().saved)
        vm.toggleSaved(id)
        assertTrue(vm.itemRows().isEmpty())
    }

    @Test
    fun filtersResetWhenTurnedOffAgain() {
        val vm = discover()
        vm.toggleFilter(DiscoverFilter.AIRPORTS); vm.toggleFilter(DiscoverFilter.AIRPORTS)
        assertEquals(DiscoverFixtures.items(today).size, vm.itemRows().size)
        assertTrue(vm.state.value.filters.isEmpty())
    }

    @Test
    fun selectedDayStartsToday() {
        assertEquals(today, discover().state.value.selectedDay)
        assertEquals(14, discover().state.value.days.size)
    }

    @Test
    fun datesAreInEuropeanPortuguese() {
        assertEquals("Sexta-feira, 16/Out", PtDates.header(today))
        assertEquals("Sex", PtDates.short(today))
        assertEquals("Domingo, 18/Out", PtDates.header(today.plusDays(2)))
    }

    // ---- Caixa de entrada ----

    @Test
    fun inboxAgeIsRelative() {
        val now = 10_000_000_000L
        assertEquals("Agora", InboxMapper.age(now - 20_000, now))
        assertEquals("Há 5 min", InboxMapper.age(now - 5 * 60_000, now))
        assertEquals("Há 3 h", InboxMapper.age(now - 3 * 3_600_000L, now))
        assertEquals("Há 1 dia", InboxMapper.age(now - 86_400_000L, now))
        assertEquals("Há 2 semanas", InboxMapper.age(now - 15 * 86_400_000L, now))
        assertEquals("Há 1 mês", InboxMapper.age(now - 31 * 86_400_000L, now))
    }

    @Test
    fun inboxItemsMapTitleBodyAndUnread() {
        val resp = com.google.gson.Gson().fromJson("""{"notifications":[{"title":"Viagem concluída","body":"A → B","createdAt":1000,"read":false},{"title":"Olá","body":"","createdAt":1000,"read":true}],"unreadCount":1}""", NotificationsResponse::class.java)
        val items = InboxMapper.items(resp, nowMs = 1000 + 3_600_000)
        assertEquals("Viagem concluída: A → B", items[0].title)
        assertTrue(items[0].unread); assertFalse(items[1].unread)
        assertEquals("Há 1 h", items[0].age)
        assertTrue(InboxMapper.items(null).isEmpty())
    }

    // ---- horas online ----

    @Test
    fun onlineHoursAreFormatted() {
        assertEquals("22 h 54 m", EarningsMapper.hours(82_440))
        assertEquals("0 h 0 m", EarningsMapper.hours(0))
    }

    @Test
    fun onlineLabelOnlyWhenTheServerSendsIt() {
        val base = EarningsView(ms("2026-10-12", 0), ms("2026-10-19", 0), "0,00 €", null, null, 0, "EUR", emptyList())
        assertNull(EarningsMapper.map(base, null, utc, LocalDate.parse("2026-10-14")).onlineLabel)
        assertEquals("1 h 0 m", EarningsMapper.map(base.copy(onlineSeconds = 3600), null, utc, LocalDate.parse("2026-10-14")).onlineLabel)
    }
}
