package com.qolari.drivereplica.ui.earnings

import com.qolari.drivereplica.net.BalanceSummary
import com.qolari.drivereplica.net.EarningsView
import java.time.Instant
import java.time.LocalDate
import java.time.ZoneId
import java.time.format.DateTimeFormatter

/** Viagem recente para a lista "As suas sessões recentes" (captura 062). */
data class RecentTrip(val route: String, val total: String, val whenLabel: String)

/**
 * Resumo semanal do separador Rendimentos (capturas 011/062). O servidor devolve o total e as viagens da semana;
 * as barras por dia calculam-se aqui a partir das viagens. "Online" e "Pontos" da original não existem no nosso
 * backend e por isso não são mostrados (D7: sem inventar valores).
 */
data class WeeklyEarnings(
    val periodLabel: String,
    val formattedTotal: String,
    val tripCount: Int,
    /** Valor por dia, de segunda a domingo (euros). */
    val dayTotals: List<Float>,
    /** Índice do dia de hoje dentro da semana, ou -1 se a semana já passou. */
    val todayIndex: Int,
    val balance: String?,
    val recent: List<RecentTrip>,
    /** "22 h 54 m"; nulo se o servidor não devolve as horas online. */
    val onlineLabel: String? = null,
)

object EarningsMapper {

    val DAY_LABELS = listOf("Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom")

    /** "1 234,56 €" -> 1234.56; texto sem número -> 0. */
    fun parseMoney(text: String?): Float {
        val cleaned = text.orEmpty().filter { it.isDigit() || it == ',' || it == '-' }.replace(',', '.')
        return cleaned.toFloatOrNull() ?: 0f
    }

    fun map(view: EarningsView, balance: BalanceSummary?, zone: ZoneId = ZoneId.systemDefault(), today: LocalDate = LocalDate.now(zone)): WeeklyEarnings {
        val start = Instant.ofEpochMilli((view.startAt ?: 0.0).toLong()).atZone(zone).toLocalDate()
        // Último instante da semana (fim exclusivo menos 1 ms): o fim do servidor soma 7x86400 s e, na semana da mudança de hora, cairia no dia seguinte.
        val lastDay = Instant.ofEpochMilli((view.endAt ?: 0.0).toLong() - 1).atZone(zone).toLocalDate()
        val fmt = DateTimeFormatter.ofPattern("dd/MM")
        val perDay = FloatArray(7)
        val whenFmt = DateTimeFormatter.ofPattern("dd/MM HH:mm")
        val recent = view.trips.orEmpty().map { t ->
            val at = Instant.ofEpochMilli((t.processedAt ?: 0.0).toLong()).atZone(zone)
            val idx = java.time.temporal.ChronoUnit.DAYS.between(start, at.toLocalDate()).toInt()
            if (idx in 0..6) perDay[idx] += parseMoney(t.formattedTotal)
            RecentTrip(
                route = listOfNotNull(t.pickupAddress, t.dropoffAddress).joinToString(" → "),
                total = t.formattedTotal.orEmpty(),
                whenLabel = at.format(whenFmt),
            )
        }
        val todayIdx = java.time.temporal.ChronoUnit.DAYS.between(start, today).toInt().takeIf { it in 0..6 } ?: -1
        return WeeklyEarnings(
            periodLabel = "${start.format(fmt)} - ${lastDay.format(fmt)}",
            formattedTotal = view.formattedTotal.orEmpty(),
            tripCount = view.tripCount ?: recent.size,
            dayTotals = perDay.toList(),
            todayIndex = todayIdx,
            balance = balance?.balance,
            recent = recent,
            onlineLabel = view.onlineSeconds?.let { hours(it) },
        )
    }

    /** 82440 s -> "22 h 54 m". */
    fun hours(seconds: Long): String = "${seconds / 3600} h ${(seconds % 3600) / 60} m"
}
