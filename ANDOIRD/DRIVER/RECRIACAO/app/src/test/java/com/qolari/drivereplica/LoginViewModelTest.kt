package com.qolari.drivereplica

import com.qolari.drivereplica.ui.login.LoginError
import com.qolari.drivereplica.ui.login.LoginViewModel
import java.io.IOException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.setMain
import okhttp3.ResponseBody.Companion.toResponseBody
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import retrofit2.HttpException
import retrofit2.Response

@OptIn(ExperimentalCoroutinesApi::class)
class LoginViewModelTest {

    private val calls = mutableListOf<Pair<String, String>>()

    private fun vm(result: Result<Unit> = Result.success(Unit)) = LoginViewModel { phone, code ->
        calls += phone to code
        result
    }

    private fun http(code: Int) = HttpException(Response.error<Any>(code, "".toResponseBody()))

    @Before fun setUp() = Dispatchers.setMain(UnconfinedTestDispatcher())

    @After fun tearDown() = Dispatchers.resetMain()

    @Test
    fun phoneKeepsOnlyNineDigits() {
        val vm = vm()
        vm.setPhone("+351 920 000 003 99")
        assertEquals("351920000", vm.state.value.phoneDigits)
        vm.setPhone("92 000 00 03")
        assertEquals("920000003", vm.state.value.phoneDigits)
        assertTrue(vm.state.value.phoneValid)
        assertEquals("+351920000003", vm.state.value.fullPhone)
    }

    @Test
    fun codeKeepsOnlyFourDigits() {
        val vm = vm()
        vm.setCode("12a345")
        assertEquals("1234", vm.state.value.code)
        assertTrue(vm.state.value.codeValid)
    }

    @Test
    fun submitSendsTheFullPhoneAndSignsIn() {
        val vm = vm()
        vm.setPhone("920000003"); vm.setCode("0000")
        vm.submit()
        assertEquals(listOf("+351920000003" to "0000"), calls)
        assertTrue(vm.state.value.signedIn)
        assertFalse(vm.state.value.loading)
    }

    @Test
    fun submitDoesNothingUntilBothFieldsAreComplete() {
        val vm = vm()
        vm.setPhone("92000"); vm.setCode("0000")
        vm.submit()
        assertTrue(calls.isEmpty())
    }

    @Test
    fun wrongCodeShowsTheErrorAndClearsTheCode() {
        val vm = vm(Result.failure(http(401)))
        vm.setPhone("920000003"); vm.setCode("1234")
        vm.submit()
        assertEquals(LoginError.WRONG_CODE, vm.state.value.error)
        assertEquals("", vm.state.value.code)
        assertFalse(vm.state.value.signedIn)
    }

    @Test
    fun errorsAreClassified() {
        assertEquals(LoginError.WRONG_CODE, LoginViewModel.classify(http(401)))
        assertEquals(LoginError.NO_ACCOUNT, LoginViewModel.classify(http(404)))
        assertEquals(LoginError.NETWORK, LoginViewModel.classify(IOException("sem rede")))
        assertEquals(LoginError.OTHER, LoginViewModel.classify(http(500)))
    }

    @Test
    fun typingAfterAnErrorClearsIt() {
        val vm = vm(Result.failure(http(401)))
        vm.setPhone("920000003"); vm.setCode("1234"); vm.submit()
        vm.setCode("1")
        assertEquals(null, vm.state.value.error)
    }

    @Test
    fun resetClearsEverything() {
        val vm = vm()
        vm.setPhone("920000003"); vm.setCode("0000"); vm.submit()
        vm.reset()
        assertEquals("", vm.state.value.phoneDigits)
        assertFalse(vm.state.value.signedIn)
    }
}
