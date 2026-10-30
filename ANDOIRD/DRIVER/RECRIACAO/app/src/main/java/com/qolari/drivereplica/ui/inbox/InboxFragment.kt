package com.qolari.drivereplica.ui.inbox

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.Icon
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.res.colorResource
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.fragment.app.viewModels
import com.qolari.drivereplica.R
import com.qolari.drivereplica.data.AppGraph
import com.qolari.drivereplica.ui.manage.LoadState
import com.qolari.drivereplica.ui.manage.LoadViewModel
import com.qolari.drivereplica.ui.manage.loadFactory
import com.qolari.drivereplica.ui.compose.ComposeFragment

/**
 * Separador Caixa de entrada (Compose, como na original: toolkit_por_ecra.csv; capturas 012, 063). Dois separadores
 * internos, "Notificações" (com contador) e "Apoio". Sem dados nem estado de erro próprio: a lista é local (D7).
 */
class InboxFragment : ComposeFragment() {
    private val vm: LoadViewModel<List<InboxItem>> by viewModels { loadFactory { AppGraph.repository.notifications() } }

    @Composable
    override fun Content() {
        var tab by rememberSaveable { mutableIntStateOf(0) }
        val state by vm.state.collectAsState()
        val items = (state as? LoadState.Data)?.value.orEmpty()
        val unread = items.count { it.unread }
        // Ao abrir, as notificações passam a lidas no servidor (o contador da barra zera); o texto a negrito mantém-se neste ecrã.
        LaunchedEffect(state) { if (state is LoadState.Data && unread > 0) AppGraph.repository.markNotificationsRead() }
        Column(Modifier.fillMaxSize()) {
            Box(Modifier.fillMaxWidth().padding(top = 16.dp, end = 16.dp)) {
                // Caixa de entrada com seta para baixo, como na captura 063 (não é o cubo 3D).
                Icon(
                    painterResource(R.drawable.ic_inbox_tray), contentDescription = null,
                    tint = colorResource(R.color.qd_ink),
                    modifier = Modifier.align(Alignment.CenterEnd).size(30.dp),
                )
            }
            Text(
                stringResource(R.string.tab_inbox), color = colorResource(R.color.qd_ink), fontSize = 32.sp, lineHeight = 38.sp,
                fontWeight = FontWeight.Bold, modifier = Modifier.padding(start = 16.dp, end = 16.dp, top = 18.dp),
            )
            InboxTabs(selected = tab, unread = unread, onSelect = { tab = it })
            if (tab == 0) {
                when (state) {
                    LoadState.Loading -> Text(stringResource(R.string.loading), color = colorResource(R.color.qd_core_gray600), fontSize = 16.sp, textAlign = TextAlign.Center, modifier = Modifier.fillMaxWidth().padding(48.dp))
                    LoadState.Failed -> Text(stringResource(R.string.earnings_no_network), color = colorResource(R.color.qd_core_gray600), fontSize = 16.sp, textAlign = TextAlign.Center, modifier = Modifier.fillMaxWidth().padding(48.dp))
                    is LoadState.Data -> if (items.isEmpty()) {
                        Text(stringResource(R.string.inbox_empty), color = colorResource(R.color.qd_core_gray600), fontSize = 16.sp, textAlign = TextAlign.Center, modifier = Modifier.fillMaxWidth().padding(48.dp))
                    } else LazyColumn(Modifier.fillMaxSize()) { items(items) { NotificationRow(it) } }
                }
            } else {
                Text(
                    stringResource(R.string.inbox_support_empty), color = colorResource(R.color.qd_core_gray600),
                    fontSize = 16.sp, textAlign = TextAlign.Center, modifier = Modifier.fillMaxWidth().padding(48.dp),
                )
            }
        }
    }
}

@Composable
private fun InboxTabs(selected: Int, unread: Int, onSelect: (Int) -> Unit) {
    Row(Modifier.fillMaxWidth().padding(top = 8.dp)) {
        listOf(R.string.inbox_tab_notifications, R.string.inbox_tab_support).forEachIndexed { i, label ->
            Column(
                Modifier.weight(1f).clickable { onSelect(i) },
                horizontalAlignment = Alignment.CenterHorizontally,
            ) {
                Row(Modifier.height(52.dp), verticalAlignment = Alignment.CenterVertically) {
                    Text(
                        stringResource(label), fontSize = 15.sp,
                        color = colorResource(if (i == selected) R.color.qd_ink else R.color.qd_core_gray600),
                        fontWeight = if (i == selected) FontWeight.Medium else FontWeight.Normal,
                    )
                    if (i == 0 && unread > 0) {
                        Box(
                            Modifier.padding(start = 8.dp).size(24.dp).clip(CircleShape).background(colorResource(R.color.qd_core_blue600)),
                            contentAlignment = Alignment.Center,
                        ) { Text(unread.toString(), color = colorResource(R.color.qd_core_white), fontSize = 13.sp) }
                    }
                }
                Box(
                    Modifier.fillMaxWidth().height(3.dp)
                        .background(colorResource(if (i == selected) R.color.qd_ink else R.color.qd_line))
                )
            }
        }
    }
}

@Composable
private fun NotificationRow(item: InboxItem) {
    Column(Modifier.fillMaxWidth()) {
        Row(
            Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 18.dp),
            verticalAlignment = Alignment.Top, horizontalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Text(
                item.title, color = colorResource(R.color.qd_ink), fontSize = 18.sp, maxLines = 2,
                overflow = androidx.compose.ui.text.style.TextOverflow.Ellipsis,
                fontWeight = if (item.unread) FontWeight.Bold else FontWeight.Normal,
                modifier = Modifier.weight(1f),
            )
            Column(horizontalAlignment = Alignment.End) {
                Text(item.age, color = colorResource(R.color.qd_core_gray600), fontSize = 14.sp)
                if (item.unread) {
                    Box(
                        Modifier.padding(top = 8.dp).size(8.dp).clip(CircleShape).background(colorResource(R.color.qd_core_blue600))
                    )
                } else {
                    Box(Modifier.padding(top = 8.dp).width(8.dp).height(8.dp))
                }
            }
        }
        Box(Modifier.fillMaxWidth().padding(start = 16.dp).height(1.dp).background(colorResource(R.color.qd_line)))
    }
}
