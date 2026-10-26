package com.qolari.drivereplica

import com.qolari.drivereplica.config.AppConfig
import com.qolari.drivereplica.config.Environment
import java.io.File
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/** Critérios do spec (FASE 4): config única e zero hosts hardcoded fora dela. */
class ConfigTest {

    @Test
    fun defaultBaseUrlComesFromTheEnvironment() {
        assertEquals(AppConfig.environment.baseUrl, AppConfig.defaultBaseUrl)
        assertEquals("https://driver.qolari.com", Environment.SERVER.baseUrl)
    }

    @Test
    fun resolveBaseUrlPrefersSavedValueAndTrimsIt() {
        assertEquals("http://10.0.0.5:8091", AppConfig.resolveBaseUrl("  http://10.0.0.5:8091/ "))
        assertEquals(AppConfig.defaultBaseUrl, AppConfig.resolveBaseUrl(null))
        assertEquals(AppConfig.defaultBaseUrl, AppConfig.resolveBaseUrl("   "))
    }

    @Test
    fun everyEnvironmentHasAUrl() {
        Environment.values().forEach { assertTrue(it.baseUrl.startsWith("http")) }
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
