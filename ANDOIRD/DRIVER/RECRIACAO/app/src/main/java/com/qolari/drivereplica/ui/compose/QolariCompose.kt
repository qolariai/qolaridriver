package com.qolari.drivereplica.ui.compose

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Switch
import androidx.compose.material3.SwitchDefaults
import androidx.compose.material3.Text
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.colorResource
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.material3.Icon
import com.qolari.drivereplica.R

/**
 * Componentes Compose partilhados pelos ecrãs que a original faz em Compose (lote 1). Medidas tiradas das capturas
 * (densidade 560: 3,5 px por dp): linha de 64dp, texto a 64dp da borda, margem de 16dp, divisor desde os 64dp.
 */
@Composable
fun QolariTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = lightColorScheme(
            primary = colorResource(R.color.qd_ink),
            onPrimary = Color.White,
            background = Color.White,
            surface = Color.White,
            onSurface = colorResource(R.color.qd_ink),
        ),
        content = content,
    )
}

@Composable
private fun ink() = colorResource(R.color.qd_ink)

@Composable
private fun secondary() = colorResource(R.color.qd_core_gray600)

/** Barra de topo: seta de voltar e, opcionalmente, o título ao lado (captura 043); sem título nas páginas com cabeçalho grande. */
@Composable
fun TopBar(title: String?, onBack: () -> Unit) {
    Column(Modifier.fillMaxWidth()) {
        Spacer(Modifier.height(4.dp))
        Row(Modifier.fillMaxWidth().height(48.dp), verticalAlignment = Alignment.CenterVertically) {
            Box(
                Modifier.padding(start = 6.dp).size(48.dp).clickable(onClick = onBack),
                contentAlignment = Alignment.Center,
            ) {
                Icon(painterResource(R.drawable.ic_back), contentDescription = "Voltar", tint = ink(), modifier = Modifier.size(24.dp))
            }
            if (title != null) {
                Text(title, color = ink(), fontSize = 17.sp, modifier = Modifier.padding(start = 12.dp))
            }
        }
        Spacer(Modifier.height(4.dp))
    }
}

@Composable
fun ScreenHeading(text: String) {
    Text(text, color = ink(), fontSize = 30.sp, fontWeight = FontWeight.Bold, modifier = Modifier.padding(start = 16.dp, end = 16.dp, bottom = 8.dp))
}

/** Título de secção (ex.: "Conta", "Geral"): bloco de 48dp, texto a negrito. */
@Composable
fun SectionTitle(text: String) {
    Box(Modifier.fillMaxWidth().height(48.dp).padding(start = 16.dp, top = 12.dp)) {
        Text(text, color = ink(), fontSize = 18.sp, fontWeight = FontWeight.Bold)
    }
}

@Composable
fun Chevron() {
    Icon(painterResource(R.drawable.ic_chevron), contentDescription = null, tint = colorResource(R.color.qd_chevron), modifier = Modifier.size(20.dp))
}

@Composable
fun RowDivider(startPadding: Int = 64) {
    Box(Modifier.fillMaxWidth().padding(start = startPadding.dp).height(1.dp).background(colorResource(R.color.qd_line)))
}

/** Linha de lista: ícone opcional (24dp aos 16dp), título 16sp, subtítulo 14sp cinzento, componente à direita. */
@Composable
fun SettingsRow(
    title: String,
    modifier: Modifier = Modifier,
    iconRes: Int? = null,
    subtitle: String? = null,
    startPadding: Int = 64,
    trailing: (@Composable () -> Unit)? = { Chevron() },
    leading: (@Composable () -> Unit)? = null,
    titleSize: Int = 15,
    // Ultimo parametro de proposito: `SettingsRow(..) { ... }` e o clique, nao o componente `trailing`.
    onClick: (() -> Unit)? = null,
) {
    Column(modifier) {
        Row(
            Modifier.fillMaxWidth()
                .then(if (onClick != null) Modifier.clickable(onClick = onClick) else Modifier)
                .heightIn(min = 64.dp)
                .padding(start = 16.dp, end = 16.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            if (leading != null) {
                leading()
                Spacer(Modifier.width((startPadding - 16 - 24).dp))
            } else if (iconRes != null) {
                Icon(painterResource(iconRes), contentDescription = null, tint = ink(), modifier = Modifier.size(24.dp))
                Spacer(Modifier.width((startPadding - 16 - 24).dp))
            } else if (startPadding > 16) {
                Spacer(Modifier.width((startPadding - 16).dp))
            }
            Column(Modifier.weight(1f).padding(vertical = 12.dp)) {
                Text(title, color = ink(), fontSize = titleSize.sp)
                if (subtitle != null) {
                    Text(subtitle, color = secondary(), fontSize = 12.sp, lineHeight = 16.sp, modifier = Modifier.padding(top = 2.dp))
                }
            }
            if (trailing != null) {
                Spacer(Modifier.width(12.dp))
                trailing()
            }
        }
        RowDivider(startPadding)
    }
}

@Composable
fun QolariSwitch(checked: Boolean, onCheckedChange: (Boolean) -> Unit) {
    Switch(
        checked = checked,
        onCheckedChange = onCheckedChange,
        colors = SwitchDefaults.colors(
            checkedThumbColor = Color.White,
            checkedTrackColor = colorResource(R.color.qd_ink),
            checkedBorderColor = colorResource(R.color.qd_ink),
            uncheckedThumbColor = colorResource(R.color.qd_core_gray600),
            uncheckedTrackColor = colorResource(R.color.qd_core_gray50),
            uncheckedBorderColor = colorResource(R.color.qd_core_gray600),
        ),
    )
}

/** Botão preto arredondado com ícone de altifalante ("Teste", captura 047). */
@Composable
fun TestPillButton(label: String, onClick: () -> Unit) {
    Button(
        onClick = onClick,
        shape = CircleShape,
        colors = ButtonDefaults.buttonColors(containerColor = colorResource(R.color.qd_ink), contentColor = Color.White),
        modifier = Modifier.height(44.dp),
    ) {
        Icon(painterResource(R.drawable.ic_speaker), contentDescription = null, tint = Color.White, modifier = Modifier.size(18.dp))
        Spacer(Modifier.width(6.dp))
        Text(label, fontSize = 14.sp, fontWeight = FontWeight.Medium)
    }
}

@Composable
fun BodyText(text: String, modifier: Modifier = Modifier) {
    Text(text, color = ink(), fontSize = 14.sp, lineHeight = 20.sp, modifier = modifier.padding(start = 16.dp, end = 16.dp))
}

@Composable
fun SecondaryText(text: String, modifier: Modifier = Modifier) {
    Text(text, color = secondary(), fontSize = 14.sp, lineHeight = 20.sp, modifier = modifier.padding(start = 16.dp, end = 16.dp))
}

@Composable
fun Gap(h: Int) = Spacer(Modifier.height(h.dp))

@Composable
fun SpaceBetween(content: @Composable () -> Unit) {
    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) { content() }
}
