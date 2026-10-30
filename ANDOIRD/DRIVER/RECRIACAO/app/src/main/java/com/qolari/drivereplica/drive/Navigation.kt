package com.qolari.drivereplica.drive

import com.qolari.drivereplica.net.RouteStep

/** Manobra pronta a desenhar no painel preto do ecrã de recolha. */
data class NavigationStep(
    /** turn-left | turn-right | straight | roundabout | merge | fork | ramp */
    val maneuver: String,
    /** Linha grande do painel: a instrução ("Faça uma curva ligeira à direita") ou a rua. */
    val road: String,
    /** Distância até à manobra, já formatada ("15 m", "80 m", "1,2 km"). */
    val distance: String,
    val distanceMeters: Int,
    /** Rua da manobra (para a linha secundária / testes). */
    val street: String = "",
)

/** Estado da navegação para a recolha: manobra atual, seguinte e limite da via. */
data class NavigationInfo(
    val current: NavigationStep?,
    val next: NavigationStep?,
    /**
     * Limite da via em km/h, **só quando é dado real** (OSM tem `maxspeed`). Nulo = sem selo.
     * Decisão de 2026-10-29: não mostrar estimativas como se fossem o limite da via.
     */
    val speedLimitKmh: Int?,
    /** Distância total que falta até à recolha, formatada ("1,7 km"). */
    val remainingDistance: String?,
    /** Tempo que falta até à recolha, formatado ("5 min"). */
    val remainingTime: String?,
    /** Índice da manobra atual na lista de passos (debug e testes). */
    val stepIndex: Int = 0,
    /** Paragem da secção de baixo do painel (vídeo 2026-10-30): recolha ou entrega. */
    val stop: NavStop? = null,
    /** Chegou ao destino final: a secção 1 passa a bandeira ("20 m — R. da Mesquita 3"). */
    val atDestination: Boolean = false,
)

/**
 * Paragem mostrada na 2.ª secção do painel preto (vídeo 2026-10-30):
 * verde = recolha do passageiro, vermelho = entrega no destino.
 */
data class NavStop(
    val address: String,
    val city: String,
    /** "pickup" | "dropoff" — decide o símbolo e a cor. */
    val kind: String,
)

/**
 * Escolhe a manobra atual a partir das manobras do Google e da posição do motorista.
 *
 * A regra é a mesma do Google Maps: a manobra atual é a **próxima** cujo fim ainda não foi
 * passado; se o motorista já estiver em cima dela (a menos de [NEAR_M]), mostra-se a seguinte,
 * como o Maps faz ao aproximar-se de um cruzamento.
 */
object Navigation {

    private const val NEAR_M = 25.0

    /** A menos disto do destino, o painel mostra a bandeira de chegada (vídeo 2026-10-30). */
    private const val AT_DESTINATION_M = 30.0

    /** [speedLimitKmh] só deve vir preenchido quando é dado real da via (ver `speedLimitKmh`). */
    fun build(
        steps: List<RouteStep>?,
        lat: Double?,
        lng: Double?,
        speedLimitKmh: Int?,
        totalDistanceM: Double?,
        totalDurationS: Double?,
        /** Paragem da 2.ª secção do painel (recolha ou entrega). */
        stop: NavStop? = null,
    ): NavigationInfo? {
        if (steps.isNullOrEmpty()) return null
        val index = currentIndex(steps, lat, lng)
        val step = steps.getOrNull(index)
        val next = steps.getOrNull(index + 1)

        // A manobra mostrada é a da INSTRUÇÃO (a 1.ª viragem à frente). Se o passo atual for só
        // "siga em frente" e o próximo for uma viragem, a distância soma os dois: é assim que o
        // Maps mostra "80 m — vire à direita", com os 80 m até ao cruzamento.
        val straightNow = step != null && (step.maneuver.isNullOrEmpty() || step.maneuver == "straight")
        val focus = steps.getOrNull(if (straightNow && next != null) index + 1 else index)
        val focusIndex = if (straightNow && next != null) index + 1 else index
        val toFocus = if (focusIndex == index) {
            step?.distanceMeters ?: 0.0
        } else {
            (step?.distanceMeters ?: 0.0) + (focus?.distanceMeters ?: 0.0)
        }
        val afterFocus = steps.getOrNull(focusIndex + 1)

        val remainingM = steps.drop(index).sumOf { it.distanceMeters ?: 0.0 }
        val etaS = steps.drop(index).sumOf { it.durationSeconds ?: 0.0 }

        return NavigationInfo(
            current = focus?.let { toNav(it, toFocus) },
            next = afterFocus?.let { toNav(it, it.distanceMeters ?: 0.0) },
            // Sem valor real != mostrar 50: fica nulo e o selo desaparece.
            speedLimitKmh = speedLimitKmh,
            remainingDistance = fmtKm(totalDistanceM ?: remainingM),
            remainingTime = fmtMin(totalDurationS ?: etaS),
            stepIndex = focusIndex,
            stop = stop,
            atDestination = (totalDistanceM ?: remainingM) < AT_DESTINATION_M,
        )
    }

    /** Índice da manobra atual (a que ainda não terminou). */
    private fun currentIndex(steps: List<RouteStep>, lat: Double?, lng: Double?): Int {
        if (lat == null || lng == null) return 0
        // A 1.ª manobra é a que se faz agora. O Google devolve um passo inicial "siga para X"
        // que já está a ser percorrido: se for esse o caso, mostramos a manobra seguinte (a viragem),
        // como o Maps faz quando o motorista arranca.
        for (i in steps.indices) {
            val s = steps[i]
            val el = s.lat
            val eg = s.lng
            if (el == null || eg == null) continue
            if (dist(lat, lng, el, eg) > NEAR_M) return i
        }
        return steps.lastIndex
    }

    private fun toNav(s: RouteStep, meters: Double): NavigationStep {
        val man = s.maneuver.orEmpty()
        val kind = when {
            man.startsWith("turn-left") || man == "uturn-left" -> "turn-left"
            man.startsWith("turn-right") || man == "uturn-right" -> "turn-right"
            man.startsWith("roundabout") || man.startsWith("rotary") -> "roundabout"
            man.startsWith("merge") -> "merge"
            man.startsWith("fork") -> "fork"
            man.startsWith("ramp") -> "ramp"
            man == "straight" || man.isEmpty() -> "straight"
            else -> man
        }
        // O painel do Maps mostra a INSTRUÇÃO curta ("Vire à direita"), não a frase inteira.
        // No "em frente" (1.º passo) mostra a rua onde se está ("Praceta da Regueira").
        val text = when (kind) {
            "straight" -> s.road.orEmpty().ifBlank { s.instructionShort.orEmpty() }
            else -> s.instructionShort.orEmpty().ifBlank { s.instruction.orEmpty() }.ifBlank { s.road.orEmpty() }
        }
        return NavigationStep(kind, text, fmtDistance(meters), meters.toInt(), s.road.orEmpty())
    }

    fun fmtDistance(m: Double): String = when {
        m < 10 -> "${m.toInt()} m"
        m < 100 -> "${(m / 10).toInt() * 10} m"
        m < 1000 -> "${(m / 50).toInt() * 50} m"
        else -> "%.1f km".format(java.util.Locale("pt", "PT"), m / 1000).replace(".", ",")
    }

    fun fmtKm(m: Double): String =
        "%.1f km".format(java.util.Locale("pt", "PT"), m / 1000).replace(".", ",")

    fun fmtMin(s: Double): String = "${maxOf(1, Math.round(s / 60.0).toInt())} min"

    /** Distância em metros (fórmula de haversine). */
    fun dist(lat1: Double, lng1: Double, lat2: Double, lng2: Double): Double {
        val r = 6371000.0
        val p1 = Math.toRadians(lat1)
        val p2 = Math.toRadians(lat2)
        val dp = p2 - p1
        val dl = Math.toRadians(lng2 - lng1)
        val h = Math.sin(dp / 2) * Math.sin(dp / 2) +
            Math.cos(p1) * Math.cos(p2) * Math.sin(dl / 2) * Math.sin(dl / 2)
        return 2 * r * Math.asin(Math.sqrt(h))
    }
}
