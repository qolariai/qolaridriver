package com.qolari.drivereplica

import com.google.gson.Gson
import com.qolari.drivereplica.net.VehiclesResponse
import com.qolari.drivereplica.ui.manage.LoadState
import com.qolari.drivereplica.ui.manage.LoadViewModel
import com.qolari.drivereplica.ui.manage.ManageMapper
import com.qolari.drivereplica.ui.manage.SafetyContent
import java.io.IOException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

/** Lote 5: veículos, documentos, segurança e carregamento de listas. */
@OptIn(ExperimentalCoroutinesApi::class)
class Lote5Test {

    @Before fun setUp() = Dispatchers.setMain(UnconfinedTestDispatcher())

    @After fun tearDown() = Dispatchers.resetMain()

    private fun vehicles(json: String) = Gson().fromJson(json, VehiclesResponse::class.java)

    @Test
    fun vehicleTitleHasYearMakeAndModel() {
        val v = ManageMapper.vehicles(vehicles("""{"vehicles":[{"uuid":"a","make":"Citroën","model":"E-C4","year":2020,"licensePlate":"AQ-62-SD","isDefault":true}]}"""))
        assertEquals("2020 Citroën E-C4", v.single().title)
        assertEquals("AQ-62-SD", v.single().plate)
        assertTrue(v.single().isDefault)
    }

    @Test
    fun vehicleWithoutYearOrMakeFallsBackToName() {
        val v = ManageMapper.vehicles(vehicles("""{"vehicles":[{"uuid":"a","name":"Carro da empresa","licensePlate":"00-AA-00"}]}"""))
        assertEquals("Carro da empresa", v.single().title)
        assertFalse(v.single().isDefault)
    }

    @Test
    fun noVehiclesGivesAnEmptyList() {
        assertTrue(ManageMapper.vehicles(null).isEmpty())
        assertTrue(ManageMapper.vehicles(vehicles("""{"vehicles":[]}""")).isEmpty())
    }

    private fun docs(json: String) = Gson().fromJson(json, com.qolari.drivereplica.net.DocumentsResponse::class.java)

    @Test
    fun documentsKeepTheBackendStatusExpiryAndNote() {
        val d = ManageMapper.documents(docs("""{"driverDocuments":[
            {"kind":"carta_conducao","title":"Carta de condução","status":"approved","expiresOn":"2029-12-31","note":""},
            {"kind":"registo_criminal","title":"Registo","status":"rejected","expiresOn":null,"note":"Ilegível"},
            {"kind":"cartao_cidadao","title":"Cartão","status":"pending"}],
            "vehicleDocuments":[{"kind":"dua","title":"DUA","status":"approved","expiresOn":"2027-06-30"}]}"""))
        assertEquals(4, d.size)
        assertEquals(com.qolari.drivereplica.ui.manage.DocStatus.APPROVED, d[0].status)
        assertEquals(com.qolari.drivereplica.ui.manage.DocStatus.REJECTED, d[1].status)
        assertEquals("Ilegível", d[1].note)
        assertEquals(com.qolari.drivereplica.ui.manage.DocStatus.PENDING, d[2].status)
        assertEquals("DUA", d[3].title)
        assertFalse(ManageMapper.documentsAllDone(d))
    }

    @Test
    fun noDocumentsMeansNothingPending() {
        assertTrue(ManageMapper.documents(null).isEmpty())
        assertTrue(ManageMapper.documentsAllDone(emptyList()))
    }

    @Test
    fun expiryIsShownAsDayMonthYear() {
        assertEquals("31/12/2029", ManageMapper.expiry("2029-12-31"))
        assertEquals("sem data", ManageMapper.expiry("sem data"))
        assertEquals(null, ManageMapper.expiry(null))
    }

    @Test
    fun profileIsMappedFromTheHub() {
        val hub = Gson().fromJson("""{"profile":{"firstName":"Carlos","rating":4.9,"acceptanceRate":92,"vehicle":{"make":"Toyota","model":"Corolla","licensePlate":"AA-11-BB"}}}""", com.qolari.drivereplica.net.ProfileHub::class.java)
        val p = ManageMapper.profile(hub)!!
        assertEquals("Carlos", p.name); assertEquals("4,90", p.rating); assertEquals("92 %", p.acceptance)
        assertEquals("Toyota Corolla · AA-11-BB", p.vehicle)
        assertEquals(null, ManageMapper.profile(null))
    }

    @Test
    fun theSafetyToolkitHasFiveToolsEndingInTheCenter() {
        assertEquals(5, SafetyContent.tools.size)
        assertEquals("Centro de segurança", SafetyContent.tools.last().title)
        assertTrue(SafetyContent.sections.all { it.second.isNotEmpty() })
    }

    @Test
    fun loadViewModelShowsDataOrFailure() {
        assertTrue(LoadViewModel { Result.success(listOf(1)) }.state.value is LoadState.Data)
        assertTrue(LoadViewModel<List<Int>> { Result.failure(IOException("x")) }.state.value is LoadState.Failed)
    }

    @Test
    fun aFailedReloadKeepsTheData() {
        var fail = false
        val vm = LoadViewModel { if (fail) Result.failure(IOException("x")) else Result.success(listOf(1)) }
        fail = true
        vm.reload()
        assertTrue(vm.state.value is LoadState.Data)
    }
}
