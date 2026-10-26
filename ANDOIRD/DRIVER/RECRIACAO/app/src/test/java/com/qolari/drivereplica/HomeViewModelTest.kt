package com.qolari.drivereplica

import com.qolari.drivereplica.data.Blocker
import com.qolari.drivereplica.data.HomeSnapshot
import com.qolari.drivereplica.ui.home.HomeEvent
import com.qolari.drivereplica.ui.home.HomeSource
import com.qolari.drivereplica.ui.home.HomeViewModel
import java.io.IOException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.launch
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

/** Regras do painel inicial observadas na original (ux_behavior.md §4), sem rede nem Android. */
@OptIn(ExperimentalCoroutinesApi::class)
class HomeViewModelTest {

    private class FakeSource(
        var home: Result<HomeSnapshot> = Result.success(HomeSnapshot(online = false, blockers = emptyList())),
        var online: Result<Boolean> = Result.success(true),
        var offline: Result<Boolean> = Result.success(false),
    ) : HomeSource {
        var fetches = 0
        var goOnlineCalls = 0
        override suspend fun fetchHome(): Result<HomeSnapshot> { fetches++; return home }
        override suspend fun goOnline(): Result<Boolean> { goOnlineCalls++; return online }
        override suspend fun goOffline(): Result<Boolean> = offline
    }

    @Before fun setUp() = Dispatchers.setMain(UnconfinedTestDispatcher())

    @After fun tearDown() = Dispatchers.resetMain()

    @Test
    fun loadsStateAtStartup() {
        val vm = HomeViewModel(FakeSource(home = Result.success(HomeSnapshot(true, listOf(Blocker("Sem veículo", null))))))
        val s = vm.state.value
        assertTrue(s.loaded); assertTrue(s.online); assertTrue(s.blocked)
        assertFalse(s.refreshing); assertFalse(s.failed)
    }

    @Test
    fun startupWithoutServerShowsTheErrorStateWithoutADialog() = runTest(UnconfinedTestDispatcher()) {
        val events = mutableListOf<HomeEvent>()
        val vm = HomeViewModel(FakeSource(home = Result.failure(IOException("sem rede"))))
        backgroundScope.launch { vm.events.collect { events += it } }
        val s = vm.state.value
        assertTrue(s.failed); assertFalse(s.loaded); assertFalse(s.refreshing)
        assertTrue("o arranque a frio não abre a janela Erro", events.isEmpty())
    }

    @Test
    fun pullToRefreshFailureAfterLoadingOpensTheErrorDialog() = runTest(UnconfinedTestDispatcher()) {
        val source = FakeSource()
        val vm = HomeViewModel(source)
        val events = mutableListOf<HomeEvent>()
        backgroundScope.launch { vm.events.collect { events += it } }
        source.home = Result.failure(IOException("sem rede"))
        vm.refresh()
        assertEquals(listOf(HomeEvent.REFRESH_FAILED), events)
        assertTrue(vm.state.value.loaded && vm.state.value.failed)
    }

    @Test
    fun goingOnlineWithBlockersRechecksInsteadOfGoingOnline() {
        val source = FakeSource(home = Result.success(HomeSnapshot(false, listOf(Blocker("Documento pendente", "carta")))))
        val vm = HomeViewModel(source)
        vm.toggleOnline()
        assertEquals(0, source.goOnlineCalls)
        assertEquals(2, source.fetches)
    }

    @Test
    fun toggleSwitchesOnlineAndOffline() {
        val vm = HomeViewModel(FakeSource())
        vm.toggleOnline()
        assertTrue(vm.state.value.online)
        vm.toggleOnline()
        assertFalse(vm.state.value.online)
    }

    @Test
    fun failedActionKeepsStateAndOpensTheErrorDialog() = runTest(UnconfinedTestDispatcher()) {
        val vm = HomeViewModel(FakeSource(online = Result.failure(IOException("x"))))
        val events = mutableListOf<HomeEvent>()
        backgroundScope.launch { vm.events.collect { events += it } }
        vm.toggleOnline()
        assertFalse(vm.state.value.online)
        assertEquals(listOf(HomeEvent.ACTION_FAILED), events)
    }

    @Test
    fun toggleIsIgnoredBeforeTheFirstResponse() {
        val source = FakeSource(home = Result.failure(IOException("x")))
        val vm = HomeViewModel(source)
        vm.toggleOnline()
        assertEquals(0, source.goOnlineCalls)
        assertEquals(1, source.fetches)
    }
}
