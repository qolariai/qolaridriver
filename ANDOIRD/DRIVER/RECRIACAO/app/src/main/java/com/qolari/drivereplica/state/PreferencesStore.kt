package com.qolari.drivereplica.state

import androidx.lifecycle.ViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update

/**
 * Preferências locais dos ecrãs de Definições (lote 1). Valores por omissão = os observados nas capturas
 * (ux_capture 044, 046, 047). Ainda não persistem (DataStore chega com o lote que liga dados) e não vão ao backend.
 */
enum class HearingOption { NONE, DEAF, HARD_OF_HEARING, BOTH }
enum class ContactPreference { CALL_OR_CHAT, CALL, CHAT }
enum class NavApp { OWN, GOOGLE_MAPS, WAZE }

data class AccessibilityPrefs(
    val vibrationForRequests: Boolean = false,
    val screenFlashForRequests: Boolean = false,
    val hearing: HearingOption = HearingOption.NONE,
)

data class SoundPrefs(
    val volume: Float = 1f,
    val seatbeltReminder: Boolean = true,
    val softerVoice: Boolean = true,
    val voiceNavigation: Boolean = true,
)

data class NavigationPrefs(
    val app: NavApp = NavApp.OWN,
    val autoStart: Boolean = true,
)

/** Comunicação: o botão "Guardar alterações" só fica ativo quando a escolha difere da guardada (captura 045). */
data class CommunicationDraft(
    val saved: ContactPreference = ContactPreference.CALL_OR_CHAT,
    val selected: ContactPreference = saved,
) {
    val canSave: Boolean get() = selected != saved
}

/** Um serviço das Preferências (print 2026-10-30, 02:10). */
data class ServiceOption(val id: String, val labelRes: Int, val iconRes: Int)

/**
 * Serviços com que o motorista aceita trabalhar. Os três primeiros vêm marcados no print
 * (Conforto, Package, UberX Priority); os restantes ficam disponíveis.
 */
data class ServicePrefs(
    val selected: Set<String> = setOf("comfort", "package", "priority"),
)

/** Contribuição de mapa enviada pelo motorista (A+ durante a recolha). */
data class MapReport(val kind: String, val atMs: Long)

class PreferencesStore {
    private val _accessibility = MutableStateFlow(AccessibilityPrefs())
    private val _sounds = MutableStateFlow(SoundPrefs())
    private val _navigation = MutableStateFlow(NavigationPrefs())
    private val _communication = MutableStateFlow(CommunicationDraft())
    private val _services = MutableStateFlow(ServicePrefs())
    private val _mapReports = MutableStateFlow<List<MapReport>>(emptyList())
    private val _stopped = MutableStateFlow(false)

    val accessibility: StateFlow<AccessibilityPrefs> = _accessibility.asStateFlow()
    val sounds: StateFlow<SoundPrefs> = _sounds.asStateFlow()
    val navigation: StateFlow<NavigationPrefs> = _navigation.asStateFlow()
    val communication: StateFlow<CommunicationDraft> = _communication.asStateFlow()

    /** Serviços com que o motorista quer trabalhar (print 2026-10-30, 02:10). */
    val services: StateFlow<ServicePrefs> = _services.asStateFlow()

    /** Relatórios de mapa já enviados (print 2026-10-30, 02:16), do mais recente para o mais antigo. */
    val mapReports: StateFlow<List<MapReport>> = _mapReports.asStateFlow()

    fun toggleService(id: String) = _services.update { s ->
        val on = id in s.selected
        s.copy(selected = if (on) s.selected - id else s.selected + id)
    }

    /** Guarda a contribuição do motorista (A+ no mapa). */
    fun addMapReport(kind: String) = _mapReports.update {
        listOf(MapReport(kind, System.currentTimeMillis())) + it
    }

    /**
     * "Parar novos pedidos" (print 2026-10-30, 01:57): o motorista deixa de receber pedidos
     * depois de acabar a viagem em curso. Volta a ligar pelo mesmo botão.
     */
    fun setStopped(stopped: Boolean) = _stopped.update { stopped }

    val stopped: StateFlow<Boolean> = _stopped.asStateFlow()

    fun setVibration(on: Boolean) = _accessibility.update { it.copy(vibrationForRequests = on) }
    fun setScreenFlash(on: Boolean) = _accessibility.update { it.copy(screenFlashForRequests = on) }
    fun setHearing(option: HearingOption) = _accessibility.update { it.copy(hearing = option) }

    fun setVolume(v: Float) = _sounds.update { it.copy(volume = v.coerceIn(0f, 1f)) }
    fun setSeatbeltReminder(on: Boolean) = _sounds.update { it.copy(seatbeltReminder = on) }
    fun setSofterVoice(on: Boolean) = _sounds.update { it.copy(softerVoice = on) }
    fun setVoiceNavigation(on: Boolean) = _sounds.update { it.copy(voiceNavigation = on) }

    fun setNavApp(app: NavApp) = _navigation.update { it.copy(app = app) }
    fun setAutoStart(on: Boolean) = _navigation.update { it.copy(autoStart = on) }

    fun selectContact(pref: ContactPreference) = _communication.update { it.copy(selected = pref) }
    fun saveContact() = _communication.update { it.copy(saved = it.selected) }
}

/** Partilhado por todos os ecrãs de Definições (ViewModel da atividade), para o estado sobreviver à navegação. */
class PreferencesViewModel : ViewModel() {
    val store = PreferencesStore()
}
