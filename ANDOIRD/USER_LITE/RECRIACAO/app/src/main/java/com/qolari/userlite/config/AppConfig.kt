package com.qolari.userlite.config

/**
 * Configuração ÚNICA (spec FASE 4): base URL, estágio e constantes de rede.
 * Trocar de backend é mudar [environment]. O teste ConfigTest falha se aparecer um host fora deste ficheiro.
 */
enum class Environment(val label: String, val baseUrl: String) {
    /** Emulador -> backend no PC. */
    MOCK("Mock local", "http://10.0.2.2:8090"),

    /** PC por USB: `adb reverse tcp:8090 tcp:8090`. */
    USB("Backend no PC por USB", "http://127.0.0.1:8090"),

    /** Backend do laboratório em LAN. */
    LAN("Backend em LAN", "http://192.168.1.204:8090"),

    /** Servidor do laboratório (Hetzner). */
    SERVER("Servidor do laboratório", "https://rider.qolari.com"),
}

object AppConfig {
    /** A única linha a mudar para trocar de estágio. */
    val environment: Environment = Environment.USB

    val defaultBaseUrl: String get() = environment.baseUrl

    val tokenHeaders: List<String> = listOf("x-uber-token", "x-qolari-token")

    const val CONNECT_TIMEOUT_S = 15L
    const val READ_TIMEOUT_S = 30L

    /** Sondagem do estado da viagem (ux_behavior.md: a User não tem socket). */
    const val TRIP_POLL_INTERVAL_MS = 2_000L
    const val HOME_REFRESH_MS = 30_000L
    const val OFFER_POLL_INTERVAL_MS = 4_000L

    const val SESSION_STORE_NAME = "qolari_lite_session"

    fun resolveBaseUrl(saved: String?): String =
        saved?.trim()?.trimEnd('/')?.takeIf { it.isNotEmpty() } ?: defaultBaseUrl
}
