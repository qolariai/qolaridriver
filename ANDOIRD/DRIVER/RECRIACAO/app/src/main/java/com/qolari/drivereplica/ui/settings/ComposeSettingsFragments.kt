package com.qolari.drivereplica.ui.settings

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.painterResource
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Slider
import androidx.compose.material3.SliderDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.colorResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextDecoration
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.os.bundleOf
import androidx.fragment.app.activityViewModels
import androidx.navigation.fragment.findNavController
import com.qolari.drivereplica.BuildConfig
import com.qolari.drivereplica.R
import com.qolari.drivereplica.state.HearingOption
import com.qolari.drivereplica.state.PreferencesViewModel
import com.qolari.drivereplica.ui.compose.BodyText
import com.qolari.drivereplica.ui.compose.ComposeFragment
import com.qolari.drivereplica.ui.compose.Gap
import com.qolari.drivereplica.ui.compose.QolariSwitch
import com.qolari.drivereplica.ui.compose.ScreenHeading
import com.qolari.drivereplica.ui.compose.SectionTitle
import com.qolari.drivereplica.ui.compose.SettingsRow
import com.qolari.drivereplica.ui.compose.TestPillButton
import com.qolari.drivereplica.ui.compose.TopBar
import com.qolari.drivereplica.ui.manage.InfoFragment

/** Ecrãs de Definições que a original faz em Compose (ux_capture/toolkit_por_ecra.csv): 043, 044, 047, 049 e 077. */

class SettingsFragment : ComposeFragment() {
    @Composable
    override fun Content() {
        val nav = findNavController()
        val privacyTitle = stringResource(R.string.settings_privacy)
        val privacyBody = stringResource(R.string.help_body_privacy)
        val backTo = arguments?.getInt(ARG_BACK_TO, 0) ?: 0
        Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState())) {
            TopBar(stringResource(R.string.settings_title)) {
                if (backTo != 0) nav.popBackStack(backTo, false) else nav.popBackStack()
            }
            SectionTitle(stringResource(R.string.settings_section_account))
            // "Gerir conta" leva ao Menu (é lá que a conta e a sessão são geridas). "Editar endereço"
            // não tem equivalente no âmbito funcional: a entrada foi removida, não ficou inerte.
            SettingsRow(stringResource(R.string.settings_manage_account), iconRes = R.drawable.ic_person) {
                nav.navigate(R.id.menuTab)
            }
            SettingsRow(privacyTitle, iconRes = R.drawable.ic_lock) {
                nav.navigate(
                    R.id.infoFragment,
                    bundleOf(InfoFragment.ARG_TITLE to privacyTitle, InfoFragment.ARG_BODY to privacyBody),
                )
            }
            SectionTitle(stringResource(R.string.settings_section_general))
            SettingsRow(stringResource(R.string.settings_accessibility), iconRes = R.drawable.ic_accessibility) {
                nav.navigate(R.id.accessibilityFragment)
            }
            SettingsRow(stringResource(R.string.settings_communication), iconRes = R.drawable.ic_phone) {
                nav.navigate(R.id.communicationFragment)
            }
            SettingsRow(stringResource(R.string.settings_navigation), iconRes = R.drawable.ic_navigation) {
                nav.navigate(R.id.navigationSettingsFragment)
            }
            SettingsRow(stringResource(R.string.settings_sounds), iconRes = R.drawable.ic_speaker) {
                nav.navigate(R.id.soundsFragment)
            }
        }
    }

    companion object {
        const val ARG_BACK_TO = "backTo"
    }
}

class AccessibilityFragment : ComposeFragment() {
    private val prefs: PreferencesViewModel by activityViewModels()

    @Composable
    override fun Content() {
        val nav = findNavController()
        val a by prefs.store.accessibility.collectAsState()
        Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState())) {
            TopBar(null) { nav.popBackStack() }
            ScreenHeading(stringResource(R.string.settings_accessibility))
            Text(
                buildAnnotatedString {
                    append(stringResource(R.string.a11y_intro))
                    withStyle(SpanStyle(textDecoration = TextDecoration.Underline)) { append(stringResource(R.string.a11y_intro_link)) }
                },
                color = colorResource(R.color.qd_ink), fontSize = 14.sp, lineHeight = 20.sp,
                modifier = Modifier.padding(start = 16.dp, end = 16.dp),
            )
            Gap(24)
            SettingsRow(
                stringResource(R.string.a11y_hearing), iconRes = R.drawable.ic_info,
                subtitle = stringResource(R.string.a11y_hearing_desc),
            ) { nav.navigate(R.id.hearingFragment) }
            SettingsRow(
                stringResource(R.string.a11y_vibration), iconRes = R.drawable.ic_phone,
                subtitle = stringResource(R.string.a11y_vibration_desc),
                trailing = { QolariSwitch(a.vibrationForRequests) { prefs.store.setVibration(it) } },
            )
            SettingsRow(
                stringResource(R.string.a11y_flash), iconRes = R.drawable.ic_compass,
                subtitle = stringResource(R.string.a11y_flash_desc),
                trailing = { QolariSwitch(a.screenFlashForRequests) { prefs.store.setScreenFlash(it) } },
            )
            SettingsRow(
                stringResource(R.string.a11y_comm), iconRes = R.drawable.ic_phone,
                subtitle = stringResource(R.string.a11y_comm_desc),
            ) { nav.navigate(R.id.communicationFragment) }
        }
    }
}

class HearingFragment : ComposeFragment() {
    private val prefs: PreferencesViewModel by activityViewModels()

    @Composable
    override fun Content() {
        val nav = findNavController()
        val a by prefs.store.accessibility.collectAsState()
        val options = listOf(
            HearingOption.DEAF to R.string.hearing_deaf,
            HearingOption.HARD_OF_HEARING to R.string.hearing_hard,
            HearingOption.BOTH to R.string.hearing_both,
        )
        Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState())) {
            // Topo com ilustracao (captura 049): botao de voltar redondo e branco sobre a imagem.
            Box(Modifier.fillMaxWidth().height(244.dp)) {
                Image(
                    painterResource(R.drawable.illus_hearing), contentDescription = null,
                    contentScale = ContentScale.Crop, modifier = Modifier.fillMaxSize(),
                )
                Box(
                    Modifier.padding(start = 6.dp, top = 6.dp).size(48.dp).clip(CircleShape)
                        .background(Color.White).clickable { nav.popBackStack() },
                    contentAlignment = Alignment.Center,
                ) {
                    androidx.compose.material3.Icon(
                        painterResource(R.drawable.ic_back), contentDescription = stringResource(R.string.back),
                        tint = colorResource(R.color.qd_ink), modifier = Modifier.size(24.dp),
                    )
                }
            }
            ScreenHeading(stringResource(R.string.a11y_hearing))
            BodyText(stringResource(R.string.hearing_intro))
            Gap(24)
            options.forEach { (option, label) ->
                SettingsRow(
                    stringResource(label), startPadding = 64, titleSize = 16,
                    onClick = { prefs.store.setHearing(if (a.hearing == option) HearingOption.NONE else option) },
                    leading = { RadioDot(a.hearing == option) },
                    trailing = null,
                )
            }
        }
    }
}

/** Botao de opcao como na original (captura 049): aro cinzento; selecionado, aro e ponto pretos. */
@Composable
private fun RadioDot(selected: Boolean) {
    val ink = colorResource(R.color.qd_ink)
    val idle = colorResource(R.color.qd_core_gray600)
    Canvas(Modifier.size(24.dp)) {
        drawCircle(if (selected) ink else idle, radius = 11.dp.toPx(), style = Stroke(width = 2.dp.toPx()))
        if (selected) drawCircle(ink, radius = 6.dp.toPx())
    }
}

class SoundsFragment : ComposeFragment() {
    private val prefs: PreferencesViewModel by activityViewModels()

    @OptIn(ExperimentalMaterial3Api::class)
    @Composable
    override fun Content() {
        val nav = findNavController()
        val s by prefs.store.sounds.collectAsState()
        Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState())) {
            TopBar(stringResource(R.string.sounds_title)) { nav.popBackStack() }
            Gap(8)
            Text(stringResource(R.string.sounds_general), color = colorResource(R.color.qd_ink), fontSize = 18.sp, fontWeight = FontWeight.Bold, modifier = Modifier.padding(start = 16.dp))
            BodyText(stringResource(R.string.sounds_general_desc))
            Slider(
                value = s.volume, onValueChange = { prefs.store.setVolume(it) },
                modifier = Modifier.fillMaxWidth().padding(horizontal = 12.dp),
                colors = SliderDefaults.colors(
                    thumbColor = colorResource(R.color.qd_core_gray100), activeTrackColor = colorResource(R.color.qd_ink),
                    inactiveTrackColor = colorResource(R.color.qd_core_gray200),
                ),
                // Fio fino como na original (captura 047): a pista por omissao do Material 3 tem 16dp.
                track = { st ->
                    SliderDefaults.Track(
                        st, modifier = Modifier.height(2.dp),
                        colors = SliderDefaults.colors(activeTrackColor = colorResource(R.color.qd_ink), inactiveTrackColor = colorResource(R.color.qd_core_gray200)),
                        drawStopIndicator = null, thumbTrackGapSize = 0.dp,
                    )
                },
            )
            Gap(16)
            Text(stringResource(R.string.sounds_alerts), color = colorResource(R.color.qd_ink), fontSize = 18.sp, fontWeight = FontWeight.Bold, modifier = Modifier.padding(start = 16.dp))
            BodyText(stringResource(R.string.sounds_alerts_desc))
            Gap(12)
            TestRow(stringResource(R.string.sounds_test_alert_volume))
            SettingsRow(
                stringResource(R.string.sounds_seatbelt), startPadding = 16,
                trailing = { QolariSwitch(s.seatbeltReminder) { prefs.store.setSeatbeltReminder(it) } },
            )
            Gap(16)
            Text(stringResource(R.string.sounds_voice), color = colorResource(R.color.qd_ink), fontSize = 18.sp, fontWeight = FontWeight.Bold, modifier = Modifier.padding(start = 16.dp))
            BodyText(stringResource(R.string.sounds_voice_desc))
            Gap(12)
            TestRow(stringResource(R.string.sounds_test_voice_volume))
            SettingsRow(
                stringResource(R.string.sounds_soft_voice), startPadding = 16,
                trailing = { QolariSwitch(s.softerVoice) { prefs.store.setSofterVoice(it) } },
            )
            SettingsRow(
                stringResource(R.string.sounds_voice_nav), startPadding = 16,
                trailing = { QolariSwitch(s.voiceNavigation) { prefs.store.setVoiceNavigation(it) } },
            )
        }
    }

    @Composable
    private fun TestRow(label: String) {
        Row(
            Modifier.fillMaxWidth().padding(horizontal = 16.dp).padding(bottom = 8.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text(label, color = colorResource(R.color.qd_ink), fontSize = 14.sp, modifier = Modifier.weight(1f))
            TestPillButton(stringResource(R.string.sounds_test)) { /* som de teste: lote de áudio */ }
        }
    }
}

class AboutFragment : ComposeFragment() {
    @Composable
    override fun Content() {
        val nav = findNavController()
        Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState())) {
            TopBar(stringResource(R.string.about_title)) { nav.popBackStack() }
            Gap(16)
            SettingsRow(stringResource(R.string.about_version, BuildConfig.VERSION_NAME), startPadding = 16, trailing = null)
            SettingsRow(stringResource(R.string.about_acknowledgements), startPadding = 16, trailing = null)
        }
    }
}
