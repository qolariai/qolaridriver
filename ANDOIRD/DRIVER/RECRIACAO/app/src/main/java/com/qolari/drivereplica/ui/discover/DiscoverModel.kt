package com.qolari.drivereplica.ui.discover

import java.time.LocalDate

/** Datas em português europeu, sem depender do idioma do aparelho (a original usa "Sexta-feira, 16/Out"). */
object PtDates {
    private val weekdayShort = listOf("Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom")
    private val weekdayLong = listOf("Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo")
    private val monthShort = listOf("Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez")

    fun short(d: LocalDate): String = weekdayShort[d.dayOfWeek.value - 1]

    fun header(d: LocalDate): String = "${weekdayLong[d.dayOfWeek.value - 1]}, ${d.dayOfMonth}/${monthShort[d.monthValue - 1]}"
}

enum class DiscoverKind { EVENT, AIRPORT }

enum class DiscoverFilter { REMINDERS, PROMOS, AIRPORTS }

/** Um evento ou pico de procura. Conteúdo de exemplo: a original recebe-o de um serviço de recomendações que o nosso backend não tem. */
data class DiscoverItem(
    val id: String,
    val date: LocalDate,
    val time: String,
    val title: String,
    val place: String?,
    val tag: String,
    val kind: DiscoverKind,
)

data class Promo(val title: String, val subtitle: String)

/** Linhas da lista (a ordem é a do ecrã). */
sealed interface DiscoverRow {
    data object Chips : DiscoverRow
    data class Promos(val promos: List<Promo>) : DiscoverRow
    data class DayHeader(val date: LocalDate) : DiscoverRow
    data class Item(val item: DiscoverItem, val saved: Boolean) : DiscoverRow
}

object DiscoverFixtures {
    val promos = listOf(
        Promo("Receba mais 15 € ao concluir 14 viagens", "Começa sexta-feira, às 21:30"),
        Promo("Receba mais 16 € ao concluir 14 viagens", "Começa sábado, às 2:00"),
        Promo("Receba mais 12 € ao concluir 14 viagens", "Começa sábado, às 16:00"),
        Promo("Receba mais 10 € ao concluir 8 viagens", "Começa domingo, às 9:00"),
        Promo("Receba mais 20 € ao concluir 20 viagens", "Começa segunda-feira, às 7:00"),
    )

    /** Duas semanas a partir de [today], com valores determinísticos. */
    fun items(today: LocalDate): List<DiscoverItem> = buildList {
        val venues = listOf("Estádio da Cidade", "Arena Central", "Pavilhão Atlântico Sul", "Estádio do Rio")
        val teams = listOf("Clube Alfa", "Clube Beta", "Atlético Norte", "Real Sul", "União Oeste", "Académico Leste")
        for (k in 0 until 14) {
            val day = today.plusDays(k.toLong())
            if (k % 3 == 0) {
                add(DiscoverItem("air-$k", day, "22:00 - 01:00", "Pico de rendimentos no aeroporto", "9,1 km de distância", "Rendimentos muito elevados", DiscoverKind.AIRPORT))
            }
            add(DiscoverItem("ev-$k-a", day, "18:00 - 19:00", "Taça - ${teams[k % 6]} vs ${teams[(k + 2) % 6]}", venues[k % 4], "Evento desportivo", DiscoverKind.EVENT))
            if (k % 2 == 0) {
                add(DiscoverItem("ev-$k-b", day, "23:00 - 00:00", "Concerto ${('A' + k % 5)}", venues[(k + 1) % 4], "Concerto", DiscoverKind.EVENT))
            }
        }
    }
}
