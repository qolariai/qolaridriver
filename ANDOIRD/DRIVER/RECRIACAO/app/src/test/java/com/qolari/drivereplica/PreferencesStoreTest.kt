package com.qolari.drivereplica

import com.qolari.drivereplica.state.ContactPreference
import com.qolari.drivereplica.state.HearingOption
import com.qolari.drivereplica.state.NavApp
import com.qolari.drivereplica.state.PreferencesStore
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/** Estados iniciais = os observados nas capturas do original (ux_capture 044, 045, 046, 047). */
class PreferencesStoreTest {

    @Test
    fun defaultsMatchTheCaptures() {
        val s = PreferencesStore()
        // 044: os dois interruptores de pedidos estao desligados
        assertFalse(s.accessibility.value.vibrationForRequests)
        assertFalse(s.accessibility.value.screenFlashForRequests)
        assertEquals(HearingOption.NONE, s.accessibility.value.hearing)
        // 047: volume no maximo e os tres interruptores ligados
        assertEquals(1f, s.sounds.value.volume, 0f)
        assertTrue(s.sounds.value.seatbeltReminder && s.sounds.value.softerVoice && s.sounds.value.voiceNavigation)
        // 046: navegacao propria escolhida e navegacao automatica ligada
        assertEquals(NavApp.OWN, s.navigation.value.app)
        assertTrue(s.navigation.value.autoStart)
        // 045: "Ligue ou envie um chat" escolhido
        assertEquals(ContactPreference.CALL_OR_CHAT, s.communication.value.selected)
    }

    @Test
    fun saveButtonIsDisabledUntilTheChoiceChanges() {
        val s = PreferencesStore()
        assertFalse("ao abrir esta desativado (captura 045)", s.communication.value.canSave)
        s.selectContact(ContactPreference.CALL)
        assertTrue(s.communication.value.canSave)
        s.selectContact(ContactPreference.CALL_OR_CHAT)
        assertFalse("voltar a escolha guardada desativa-o", s.communication.value.canSave)
        s.selectContact(ContactPreference.CHAT)
        s.saveContact()
        assertFalse(s.communication.value.canSave)
        assertEquals(ContactPreference.CHAT, s.communication.value.saved)
    }

    @Test
    fun togglesAndVolumeUpdateAndClamp() {
        val s = PreferencesStore()
        s.setVibration(true); s.setHearing(HearingOption.BOTH)
        assertTrue(s.accessibility.value.vibrationForRequests)
        assertEquals(HearingOption.BOTH, s.accessibility.value.hearing)
        s.setVolume(1.7f); assertEquals(1f, s.sounds.value.volume, 0f)
        s.setVolume(-3f); assertEquals(0f, s.sounds.value.volume, 0f)
        s.setNavApp(NavApp.WAZE); s.setAutoStart(false)
        assertEquals(NavApp.WAZE, s.navigation.value.app)
        assertFalse(s.navigation.value.autoStart)
    }
}
