package com.qolari.drivereplica.ui.inbox

import com.qolari.drivereplica.net.NotificationsResponse

/** Uma notificação da Caixa de entrada (capturas 012, 063). */
data class InboxItem(val title: String, val age: String, val unread: Boolean)

object InboxMapper {

    /** "Há 5 min", "Há 2 h", "Há 3 dias", "Há 2 semanas", "Há 1 mês", como na original. */
    fun age(createdMs: Long, nowMs: Long): String {
        val s = ((nowMs - createdMs) / 1000).coerceAtLeast(0)
        val min = s / 60
        val h = min / 60
        val d = h / 24
        return when {
            s < 60 -> "Agora"
            min < 60 -> "Há $min min"
            h < 24 -> "Há $h h"
            d < 7 -> "Há $d ${if (d == 1L) "dia" else "dias"}"
            d < 30 -> "Há ${d / 7} ${if (d / 7 == 1L) "semana" else "semanas"}"
            d < 365 -> "Há ${d / 30} ${if (d / 30 == 1L) "mês" else "meses"}"
            else -> "Há ${d / 365} ${if (d / 365 == 1L) "ano" else "anos"}"
        }
    }

    fun items(resp: NotificationsResponse?, nowMs: Long = System.currentTimeMillis()): List<InboxItem> =
        resp?.notifications.orEmpty().map { n ->
            InboxItem(
                title = listOfNotNull(n.title, n.body?.takeIf { it.isNotBlank() }).joinToString(": "),
                age = age(n.createdAt?.toLong() ?: nowMs, nowMs),
                unread = n.read != true,
            )
        }
}
