package com.qolari.drivereplica.config

/**
 * Ficheiro de configuração ÚNICO (spec FASE 4: "base URL, keys e ambientes num único ficheiro de config;
 * zero hosts hardcoded nos ecrãs"). Trocar de backend ou de estágio é mudar uma linha: [AppConfig.environment].
 *
 * Os estágios são os do spec: 1) mock local, 2) backend real em LAN, 3) servidor.
 * Chaves (Google Maps) vêm de local.properties e entram no manifest; não existem no código.
 * O teste `ConfigTest` falha se aparecer um host fora deste ficheiro.
 */
enum class Environment(val label: String, val baseUrl: String) {
    /** Emulador -> mock_server.py no PC (TESTE/backend). */
    MOCK("Mock local", "http://10.0.2.2:8091"),

    /** PC por USB: `adb reverse tcp:8091 tcp:8091` e o backend local (BACKEND/server.py). */
    USB("Backend no PC por USB", "http://127.0.0.1:8091"),

    /** Backend real do laboratório em LAN (XAMPP/Apache na porta 80 do PC). */
    LAN("Backend em LAN", "http://192.168.1.204"),

    /** Servidor do laboratório (Hetzner). */
    SERVER("Servidor do laboratório", "https://driver.qolari.com"),
}

object AppConfig {
    /** A ÚNICA linha a mudar para trocar de estágio. */
    val environment: Environment = Environment.USB

    val defaultBaseUrl: String get() = environment.baseUrl

    /** Headers de token aceites pelo backend (a Driver original usa x-uber-token; o rebrand também x-qolari-token). */
    val tokenHeaders: List<String> = listOf("x-uber-token", "x-qolari-token")

    const val CONNECT_TIMEOUT_S = 15L
    const val READ_TIMEOUT_S = 30L

    /** Intervalos de polling (ux_behavior.md / contrato): posições e ofertas. */
    const val LOCATION_UPLOAD_INTERVAL_MS = 4_000L
    const val OFFER_POLL_INTERVAL_MS = 4_000L

    const val SESSION_STORE_NAME = "qolari_session"

    /**
     * Host do Google Directions (rota real). Vive aqui, não no cliente, para cumprir
     * a regra "zero hosts hardcoded fora do AppConfig" (BUILD §9) que o `ConfigTest` impõe.
     */
    const val DIRECTIONS_HOST = "https://maps.googleapis.com"

    /** URL efetivo: o guardado pelo utilizador (ecrã de definições do lote 2) ou o do ambiente. */
    fun resolveBaseUrl(saved: String?): String =
        saved?.trim()?.trimEnd('/')?.takeIf { it.isNotEmpty() } ?: defaultBaseUrl
}
