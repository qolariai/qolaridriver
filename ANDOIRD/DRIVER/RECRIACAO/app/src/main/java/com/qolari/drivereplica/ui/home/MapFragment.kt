package com.qolari.drivereplica.ui.home

import android.Manifest
import android.os.Bundle
import android.os.SystemClock
import android.view.View
import androidx.activity.result.contract.ActivityResultContracts
import androidx.core.view.isVisible
import androidx.fragment.app.Fragment
import androidx.fragment.app.activityViewModels
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import androidx.navigation.fragment.findNavController
import com.qolari.drivereplica.R
import com.qolari.drivereplica.data.AppGraph
import com.qolari.drivereplica.databinding.FragmentMapBinding
import com.qolari.drivereplica.drive.ActiveTrip
import com.qolari.drivereplica.drive.DriveStage
import com.qolari.drivereplica.drive.DriveUiState
import com.qolari.drivereplica.drive.DriveViewModel
import com.qolari.drivereplica.drive.OfferAlerts
import com.qolari.drivereplica.drive.OfferCard
import com.qolari.drivereplica.drive.PinSheet
import com.qolari.drivereplica.drive.RatingSheet
import com.qolari.drivereplica.drive.TripPhase
import com.qolari.drivereplica.state.PreferencesViewModel
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.launch

/**
 * Modo mapa da Página inicial (captura 110) e, com o motorista online, o ecrã da proposta e da viagem
 * (capturas 100_online_*): "Radar de viagens", cartão da proposta, recolher, PIN, deixar e avaliação.
 * O ícone da casa volta ao painel (ux_behavior.md §1.2). Partilha o estado com o painel.
 */
class MapFragment : Fragment(R.layout.fragment_map) {

    private val viewModel: HomeViewModel by activityViewModels { HomeViewModel.Factory }
    private val drive: DriveViewModel by activityViewModels { DriveViewModel.Factory }
    private val prefs: PreferencesViewModel by activityViewModels()
    private var binding: FragmentMapBinding? = null

    /** Vibração, tom e flash do pedido, com as preferências de Acessibilidade. */
    private var alerts: OfferAlerts? = null
    private var alertOfferUuid: String? = null

    /** Última rota pedida, para não repetir o Directions a cada atualização de estado. */
    private var lastRouteKey: String? = null

    private val locationPermission = registerForActivityResult(ActivityResultContracts.RequestPermission()) {
        viewModel.toggleOnline()
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        val b = FragmentMapBinding.bind(view)
        binding = b
        alerts = OfferAlerts(requireContext())
        b.mapHome.setOnClickListener { findNavController().popBackStack() }
        b.mapStart.setOnClickListener {
            if (AppGraph.location.hasPermission) viewModel.toggleOnline()
            else locationPermission.launch(Manifest.permission.ACCESS_FINE_LOCATION)
        }
        b.offerCard.offerAccept.setOnClickListener { drive.accept() }
        b.offerCard.offerClose.setOnClickListener { drive.decline() }
        b.tripCard.tripPinButton.setOnClickListener { PinSheet().show(childFragmentManager, "pin") }
        // "Navegar" alterna entre navegação (câmara colada) e vista ampla do percurso, como na
        // Uber (vídeo 2026-10-30). Guarda-se no fragment para sobreviver aos re-renders.
        b.navButton.setOnClickListener { toggleNavigationMode(b) }

        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                launch {
                    // Tempo de espera na recolha: relógio que avança por segundos (WaitTimeTaskData.startTimeSec).
                    while (true) {
                        val t = drive.state.value.trip
                        val start = t?.waitStartSec
                        if (t != null && t.phase == TripPhase.AT_PICKUP && start != null) {
                            val secs = (System.currentTimeMillis() / 1000 - start).coerceAtLeast(0)
                            b.tripCard.tripWait.text = getString(R.string.drive_wait, "%d:%02d".format(secs / 60, secs % 60))
                            // Cartão novo da espera (vídeo 2026-10-30): contador + barra azul.
                            b.waitCard.waitTimer.text = "%d:%02d".format(secs / 60, secs % 60)
                            b.waitCard.waitProgress.progress = (secs.coerceIn(0, 300) * 100 / 300).toInt()
                        }
                        delay(1000)
                    }
                }
                launch {
                    combine(viewModel.state, AppGraph.network.connected, drive.state) { s, c, d -> Triple(s, c, d) }.collect { (s, connected, d) ->
                        renderStatus(b, s.online, connected, d.stage)
                        render(b, d)
                    }
                }
                launch {
                    viewModel.events.collect {
                        ErrorSheet.show(childFragmentManager, viewLifecycleOwner) { viewModel.refresh() }
                    }
                }
                launch { drive.events.collect { ErrorSheet.show(childFragmentManager, viewLifecycleOwner) { drive.setOnline(true) } } }
            }
        }
    }

    private fun renderStatus(b: FragmentMapBinding, online: Boolean, connected: Boolean, stage: DriveStage) {
        val idle = stage == DriveStage.IDLE || stage == DriveStage.RATING
        // Ecrã de recolha/viagem (vídeo 2026-10-30): painel de manobras em cima, barra "A recolher/
        // A deixar X" em baixo e selo de limite. O cromo do mapa sai, como no pedido.
        val navigating = stage == DriveStage.TO_PICKUP || stage == DriveStage.ON_TRIP
        val chrome = stage != DriveStage.OFFER && !navigating
        b.mapStart.isVisible = !online
        b.mapStatus.setText(if (online) R.string.home_online else R.string.home_offline)
        b.mapStatusHint.setText(if (online) R.string.map_online_hint else R.string.map_offline_no_network)
        b.mapStatusHint.isVisible = (!connected || online) && chrome
        b.mapStatusHint.setTextColor(requireContext().getColor(if (online) R.color.qd_core_green600 else R.color.qd_core_red600))
        b.statusPanel.isVisible = idle && chrome
        b.mapShortcuts.isVisible = idle && chrome
        b.mapShield.isVisible = idle && chrome
        b.radarPill.isVisible = online && (idle || stage == DriveStage.OFFER) && chrome
        b.mapHome.isVisible = chrome
        b.mapSearch.isVisible = chrome
        b.mapPro.isVisible = chrome
        b.mapFull.showDemand = chrome
        // O selo depende de haver limite real: quem decide é bindNavigation (não o modo do ecrã).
        b.navButton.isVisible = navigating
        // O painel de manobras tapa o topo: o padding do mapa passa a ser a altura real do painel
        // (ver bindNavigation). Fora da navegação limpa-se.
        if (!navigating) b.mapFull.setTopPadding(0)
    }

    /**
     * Rota real (estradas) da posição atual do motorista até à recolha/destino. O mapa deixa de
     * mostrar a linha reta e passa a acompanhar a localização verdadeira do telemóvel.
     * Na proposta o traço é recolha -> destino, grosso e desenhado progressivamente (vídeo 2026-10-29).
     */
    private fun updateRoute(b: FragmentMapBinding, d: DriveUiState) {
        val device = AppGraph.location.lastKnown()
        b.mapFull.deviceLocation = device
        // A rota da proposta vem do Google Directions (segue as ruas). O back-end só tem a reta
        // quando não há chave e o projeto proíbe traços retos, por isso aqui pede-se sempre ao Google.
        // Vídeo 2026-10-29: dois troços na mesma linha — motorista -> recolha e recolha -> destino.
        if (d.stage == DriveStage.OFFER) {
            val offer = d.offer ?: return
            val pickup = offer.pickup
            val dropoff = offer.dropoff
            val key = "offer-${offer.uuid}"
            if (key != lastRouteKey && pickup != null && dropoff != null) {
                lastRouteKey = key
                b.mapFull.offerEndpoints = pickup to dropoff
                val card = b.offerCard.root
                val dp = resources.displayMetrics.density
                val cardH = { if (card.height > 0) card.height else (430 * dp).toInt() }
                // Troço cliente -> destino: vem do servidor (Google Directions).
                val tripRoute = d.route

                // Troço motorista -> cliente: do GPS atual até à recolha.
                val from = device
                if (from != null) {
                    DirectionsClient.fetch(requireContext(), from.first, from.second, pickup.first, pickup.second) { toPickup ->
                        if (binding == null) return@fetch
                        if (tripRoute.size > 2) {
                            b.mapFull.setOfferRoutes(toPickup, tripRoute, cardH())
                        } else {
                            DirectionsClient.fetch(requireContext(), pickup.first, pickup.second, dropoff.first, dropoff.second) { trip ->
                                if (binding != null && trip.size > 1) b.mapFull.setOfferRoutes(toPickup, trip, cardH())
                            }
                        }
                    }
                } else {
                    b.mapFull.setOfferRoutes(emptyList(), tripRoute, cardH())
                }

                card.post {
                    if (binding == null) return@post
                    // Só reenquadra a câmara: não mexe nos traços nem pára o varrimento.
                    b.mapFull.reframe()
                }
            }
            b.mapFull.showOfferMarkers = true
            return
        }
        b.mapFull.showOfferMarkers = false
        b.mapFull.offerEndpoints = null
        b.mapFull.setBottomPadding(0)
        b.mapFull.clearOfferRoutes()
        // Navegação (vídeo 2026-10-30): as duas fases usam o mesmo painel, com o traço da sua perna.
        //   TO_PICKUP -> rota até à recolha (ponto verde na 2.ª secção);
        //   ON_TRIP   -> rota até ao destino (quadrado vermelho na 2.ª secção).
        if (d.stage == DriveStage.TO_PICKUP || d.stage == DriveStage.ON_TRIP) {
            // Ao entrar em navegação (aceitar a viagem ou iniciar a viagem com o cliente a bordo)
            // a câmara passa logo a modo navegação, como no vídeo de 2026-10-30.
            if (d.stage != lastNavStage) {
                lastNavStage = d.stage
                navMode = true
                b.mapFull.navigating = true
                b.navButton.setText(R.string.nav_wide)
            }
            // O mapa em navegação usa o estilo do Google Maps (ruas e nomes), não o mapa limpo
            // do ecrã inicial — sem isto "não se percebe nada" (feedback de 2026-10-30).
            b.mapFull.thickNavigation = true
            if (d.route.size > 1 && d.route != b.mapFull.route) b.mapFull.route = d.route
            bindNavigation(b, d)
            return
        }
        lastNavStage = null
        b.mapFull.thickNavigation = false
        b.mapFull.setStreetLabel(null)
        // Espera na recolha (print 2026-10-30 11:34): a barra "À espera do passageiro" fica
        // visível por baixo do painel, com filtros à esquerda e lista à direita. O cartão
        // completo (contador + contacto + Começar) vive por baixo dela.
        if (d.stage == DriveStage.AT_PICKUP) {
            hideNavigation(b)
            val bar = b.pickupNavBar
            bar.root.isVisible = true
            bar.pickupNavTitle.text = getString(R.string.nav_waiting)
            bar.pickupNavEta.text = ""
            bar.pickupNavDistance.text = ""
            bar.pickupNavDot.isVisible = false
            bar.root.post {
                if (binding != null) b.mapFull.setBottomPadding(bar.root.height)
            }
            return
        }
        hideNavigation(b)
        val target: Pair<Double, Double>? = when (d.stage) {
            // Em AT_PICKUP já não há navegação (está à espera do passageiro): não se desenha
            // traço nenhum. Antes pedia-se aqui a rota e o resultado assíncrono voltava a
            // desenhar o traço depois de cancelar (bug de 2026-10-30).
            DriveStage.TO_PICKUP, DriveStage.ON_TRIP ->
                d.trip?.let { t -> if (t.latitude != null && t.longitude != null) t.latitude to t.longitude else null }
            else -> null
        }
        if (device == null || target == null) {
            // Sem viagem não há traço: limpa sempre (antes, um "none" anterior deixava a rota
            // da viagem cancelada no mapa — visto a 2026-10-30).
            lastRouteKey = "none"
            if (b.mapFull.route.isNotEmpty()) b.mapFull.route = emptyList()
            b.mapFull.setStreetLabel(null)
            return
        }
        val key = "${device.first},${device.second}-${target.first},${target.second}"
        if (key == lastRouteKey && b.mapFull.route.isNotEmpty()) return
        lastRouteKey = key
        DirectionsClient.fetch(requireContext(), device.first, device.second, target.first, target.second) { pts ->
            // Só desenha se a viagem ainda existir: uma resposta atrasada do Directions voltava a
            // pintar o traço depois de a viagem ter sido cancelada (bug de 2026-10-30).
            val stillOnTrip = drive.state.value.trip != null &&
                drive.state.value.stage in listOf(DriveStage.TO_PICKUP, DriveStage.ON_TRIP)
            if (binding != null && pts.size > 1 && stillOnTrip) binding?.mapFull?.route = pts
        }
    }

    private fun render(b: FragmentMapBinding, d: DriveUiState) {
        // Sem viagem nem proposta não há traço nenhum no mapa (a rota da viagem cancelada
        // ficava desenhada — reportado a 2026-10-30). Limpa antes de tudo o resto.
        val noTrip = d.trip == null
        if (noTrip && d.stage != DriveStage.OFFER) {
            b.mapFull.thickNavigation = false
            b.mapFull.setStreetLabel(null)
            b.mapFull.clearOfferRoutes()
        }
        updateRoute(b, d)
        val offer = d.offer
        val offerVisible = d.stage == DriveStage.OFFER && offer != null
        b.offerCard.root.isVisible = offerVisible
        b.radarCount.text = if (offer != null) "1" else "0"
        if (offer != null && offerVisible) bindOffer(b, offer)
        // Radar: depois do toque o cartão apaga-se e o botão passa a "A verificar…" até o
        // servidor fechar a janela de emparelhamento (vídeo 2026-10-29, 0:07).
        // O fundo do cartão mantém-se opaco: só o conteúdo é que esbate.
        val c = b.offerCard
        listOf(c.offerProduct, c.offerKind, c.offerPrice, c.offerTotals,
               c.offerPickupLine, c.offerPickupAddress, c.offerTripLine, c.offerDropoffAddress)
            .forEach { it.alpha = if (d.radarPending) 0.45f else 1f }
        c.offerAccept.isEnabled = !d.radarPending
        c.offerAccept.text = getString(
            if (d.radarPending) R.string.drive_radar_checking else R.string.drive_accept
        )
        updateAlerts(b, if (offerVisible) offer?.uuid else null)

        val trip = d.trip
        // Espera na recolha: o cartão novo do vídeo de 2026-10-30 (contador + contacto +
        // "Começar <produto>") substitui o cartão antigo com "Deslize: recolher".
        val waiting = trip != null && d.stage == DriveStage.AT_PICKUP
        b.waitCard.root.isVisible = waiting
        // O cartão antigo só serve agora para o PIN (quando o passageiro o pediu).
        val pinNeeded = waiting && trip?.pin != null && !d.pinVerified
        b.tripCard.root.isVisible = pinNeeded
        if (trip != null && pinNeeded) bindTrip(b, trip, d)
        if (trip != null && waiting) bindWaitCard(b, trip, d)

        val sheet = childFragmentManager.findFragmentByTag("rating")
        if (d.stage == DriveStage.RATING && d.summary != null) {
            if (sheet == null) RatingSheet().show(childFragmentManager, "rating")
        } else if (sheet is androidx.fragment.app.DialogFragment) {
            sheet.dismissAllowingStateLoss()
        }
    }

    private var timerKey: String? = null

    /**
     * Cartão de espera na recolha (vídeo 2026-10-30): nome, contacto, contador "À espera do
     * utilizador" com barra azul, e o botão "Começar <produto>".
     */
    private fun bindWaitCard(b: FragmentMapBinding, t: ActiveTrip, d: DriveUiState) {
        val c = b.waitCard
        c.waitName.text = t.riderName
        c.waitStartLabel.text = getString(
            R.string.wait_start,
            t.product?.takeIf { it.isNotBlank() } ?: getString(R.string.drive_product_fallback),
        )
        // O contador conta desde a chegada (waitTimeTaskData.startTimeSec do servidor).
        c.waitTimer.text = formatWait(t.waitStartSec)
        val pct = waitPercent(t.waitStartSec)
        c.waitProgress.progress = pct
        // Vídeo 2026-10-30: o telefone abre o CHAT (mensagem ou ligação); o ícone de pessoa
        // abre a lista de motivos de cancelamento. São coisas diferentes.
        c.waitCall.setOnClickListener {
            findNavController().navigate(R.id.chatFragment)
        }
        c.waitProfile.setOnClickListener {
            findNavController().navigate(R.id.cancelReasonsFragment)
        }
        // "Começar <produto>": inicia a viagem (com PIN já verificado, quando o passageiro o pediu).
        c.waitStart.setOnClickListener { drive.startTrip() }
        c.waitStart.isEnabled = !d.busy && (t.pin == null || d.pinVerified)
    }

    /**
     * "A+" (aceitação automática): liga/desliga o aceitar automático de pedidos. Guardado no
     * fragment para o estado sobreviver aos re-renders. O ícone fica a cheio quando ligado.
     */
    /**
     * Itinerário da viagem em curso (botão de rota do ecrã de espera): recolha e entrega.
     * Mostra o que o motorista precisa de saber antes de arrancar — nada é inventado,
     * as moradas vêm da viagem que o servidor devolveu.
     */
    private fun showTripItinerary(t: ActiveTrip) {
        val pickup = t.pickupAddress?.takeIf { it.isNotBlank() } ?: t.address
        val msg = getString(R.string.itinerary_body, pickup, t.address, t.riderName)
        androidx.appcompat.app.AlertDialog.Builder(requireContext())
            .setTitle(R.string.itinerary_title)
            .setMessage(msg)
            .setPositiveButton(android.R.string.ok, null)
            .show()
    }

    /** "1:35" a partir do instante de chegada; "0:00" se não houver carimbo. */    private fun formatWait(startSec: Long?): String {
        if (startSec == null) return "0:00"
        val secs = (System.currentTimeMillis() / 1000 - startSec).coerceAtLeast(0)
        return "%d:%02d".format(secs / 60, secs % 60)
    }

    /** Progresso da barra: enche ao longo da espera (5 min = 100%, o máximo da Uber). */
    private fun waitPercent(startSec: Long?): Int {
        if (startSec == null) return 0
        val secs = (System.currentTimeMillis() / 1000 - startSec).coerceIn(0, 300)
        return (secs * 100 / 300).toInt()
    }

    /** Modo da câmara: true = navegação (câmara colada), false = vista ampla do percurso. */
    private var navMode = false
    /** Última fase em que se entrou em navegação, para a transição automática só acontecer uma vez. */
    private var lastNavStage: DriveStage? = null

    /**
     * Botão "Navegar" (vídeo 2026-10-30): alterna entre a navegação e a vista ampla.
     * O rótulo acompanha o modo: em vista ampla diz "Navegar" (volta à navegação).
     */
    private fun toggleNavigationMode(b: FragmentMapBinding) {
        navMode = !navMode
        b.mapFull.navigating = navMode
        b.navButton.setText(if (navMode) R.string.nav_wide else R.string.nav_navigate)
    }

    /** Painel de manobras + barra "A recolher X" + selo de limite (vídeo 2026-10-29). */
    private fun bindNavigation(b: FragmentMapBinding, d: DriveUiState) {
        val trip = d.trip
        val nav = d.navigation
        val panel = b.maneuverPanel
        // Só aparece quando há manobras do Google; sem elas fica só a barra inferior.
        val hasPanel = nav?.current != null
        panel.root.isVisible = hasPanel
        val bar = b.pickupNavBar
        bar.root.isVisible = trip != null
        if (nav?.current != null) {
            panel.maneuverDistance.text = nav.current.distance
            panel.maneuverRoad.text = nav.current.road
            // Chegou ao destino final: a 1.ª secção passa a bandeira (vídeo 2026-10-30, 10:04).
            panel.maneuverIcon.setImageResource(
                if (nav.atDestination) R.drawable.ic_flag_finish else maneuverIcon(nav.current.maneuver)
            )
        }
        // 2.ª secção: a paragem (verde = recolha, vermelho = entrega) com a cidade.
        val stop = nav?.stop
        panel.stopSection.isVisible = stop != null
        panel.maneuverDivider.isVisible = hasPanel && stop != null
        if (stop != null) {
            panel.stopAddress.text = stop.address
            panel.stopCity.text = stop.city
            panel.stopDot.setBackgroundResource(
                if (stop.kind == "dropoff") R.drawable.bg_stop_dot_dropoff
                else R.drawable.bg_stop_dot_pickup
            )
        }
        // Selo "LIMITE": só com o limite real da via (OSM). Sem dado, não se mostra um número
        // inventado — o condutor não deve confiar num limite estimado.
        val limit = nav?.speedLimitKmh
        b.speedBadge.isVisible = limit != null
        if (limit != null) b.speedLimit.text = limit.toString()
        // Balão com o nome da rua atual junto à seta (vídeo 2026-10-30 15:16).
        b.mapFull.setStreetLabel(nav?.current?.street?.ifBlank { null })
        // O map padding do topo tem de ser a altura REAL do painel (estava fixo em 176dp e
        // esmagava a área do mapa, deixando a seta fora do sítio).
        panel.root.post {
            if (binding != null) b.mapFull.setTopPadding(panel.root.height)
        }
        bar.pickupNavEta.text = nav?.remainingTime.orEmpty()
        bar.pickupNavDistance.text = nav?.remainingDistance.orEmpty()
        bar.pickupNavTitle.text = when {
            trip == null -> ""
            trip.phase == TripPhase.ON_TRIP -> getString(R.string.nav_dropoff_title, trip.riderName)
            else -> getString(R.string.nav_pickup_title, trip.riderName)
        }
        // O símbolo da barra acompanha a fase: verde na recolha, vermelho na entrega (vídeo 2026-10-30).
        val dropoffPhase = trip?.phase == TripPhase.ON_TRIP
        bar.pickupNavDot.setImageResource(
            if (dropoffPhase) R.drawable.ic_stop_dot_square else R.drawable.ic_person_filled
        )
        bar.pickupNavDot.imageTintList = android.content.res.ColorStateList.valueOf(
            requireContext().getColor(if (dropoffPhase) R.color.qd_stop_dropoff else R.color.qd_core_green600)
        )
        // O traço fino não deve ficar por baixo da barra inferior.
        bar.root.post {
            if (binding != null) b.mapFull.setBottomPadding(bar.root.height)
        }
    }

    private fun hideNavigation(b: FragmentMapBinding) {
        b.maneuverPanel.root.isVisible = false
        b.pickupNavBar.root.isVisible = false
        b.speedBadge.isVisible = false
        b.navButton.isVisible = false
        // Fora da navegação volta o mapa limpo do ecrã inicial.
        if (navMode) {
            navMode = false
            b.mapFull.navigating = false
        }
    }

    private fun maneuverIcon(maneuver: String): Int = when {
        maneuver.startsWith("turn-left") || maneuver.contains("left") -> R.drawable.ic_maneuver_left
        maneuver.startsWith("turn-right") || maneuver.contains("right") -> R.drawable.ic_maneuver_right
        maneuver.startsWith("roundabout") || maneuver.startsWith("rotary") -> R.drawable.ic_maneuver_roundabout
        else -> R.drawable.ic_maneuver_straight
    }

    /**
     * Alerta do pedido: vibra/toca/pisca só enquanto o cartão está no ecrã e só uma vez por proposta.
     * As opções vêm de Definições > Acessibilidade e o volume de Definições > Sons e voz.
     */
    private fun updateAlerts(b: FragmentMapBinding, offerUuid: String?) {
        if (offerUuid == alertOfferUuid) return
        alertOfferUuid = offerUuid
        val a = prefs.store.accessibility.value
        val s = prefs.store.sounds.value
        if (offerUuid == null) {
            alerts?.stop()
        } else {
            alerts?.start(
                viewLifecycleOwner.lifecycleScope,
                b.offerFlash,
                // O pedido alerta sempre (vibração + tom); o flash depende de Acessibilidade > Iluminação.
                vibrate = true,
                flash = a.screenFlashForRequests,
                volume = s.volume,
            )
        }
    }

    private fun bindOffer(b: FragmentMapBinding, o: OfferCard) {
        val c = b.offerCard
        c.offerProduct.text = o.product
        // Tipo de pedido, como no vídeo: "Exclusivo" a azul ou "Radar".
        c.offerKind.text = getString(
            if (o.kind == com.qolari.drivereplica.drive.OfferKind.RADAR) R.string.drive_kind_radar
            else R.string.drive_kind_exclusive
        )
        c.offerPrice.text = o.price
        c.offerTotals.text = o.totals.orEmpty()
        c.offerTotals.isVisible = !o.totals.isNullOrBlank()
        c.offerPickupLine.text = o.pickupLine
        c.offerPickupAddress.text = o.pickupAddress
        c.offerTripLine.text = o.tripLine
        c.offerTripLine.isVisible = o.tripLine != null
        c.offerDropoffAddress.text = o.dropoffAddress
        c.offerDropoffAddress.isVisible = o.dropoffAddress != null
        // O rail acompanha o bloco de textos: círculo na 1.ª linha, quadrado na última.
        c.offerRail.post {
            val d = resources.displayMetrics.density
            val containerTop = c.offerRail.top.toFloat()
            c.offerRail.pickupCenterDp =
                (c.offerPickupLine.top + c.offerPickupLine.height / 2f - containerTop) / d
            val last = if (c.offerDropoffAddress.isVisible) c.offerDropoffAddress else c.offerTripLine
            c.offerRail.dropoffCenterDp = (last.top + last.height / 2f - containerTop) / d
        }
        // Sem barra de contagem: a original não mostra o tempo e o pedido expira em silêncio.
        if (timerKey == o.uuid) return
        timerKey = o.uuid
        // O relógio segue `expiresAt` (hora do servidor), não `acceptWindow`: no Radar o servidor
        // pode já ter substituído a proposta e o cartão não pode ficar pendurado a pedir "expire"
        // de uma oferta que já não existe.
        val total = if (o.expiresAtMs > 0) {
            (o.expiresAtMs - System.currentTimeMillis()).coerceAtLeast(1000L)
        } else {
            (o.acceptWindowS * 1000L).coerceAtLeast(1000L)
        }
        val start = SystemClock.elapsedRealtime()
        viewLifecycleOwner.lifecycleScope.launch {
            while (timerKey == o.uuid) {
                val left = total - (SystemClock.elapsedRealtime() - start)
                if (left <= 0) {
                    timerKey = null
                    drive.expire()
                    return@launch
                }
                delay(250)
            }
        }
    }

    private fun bindTrip(b: FragmentMapBinding, t: ActiveTrip, d: DriveUiState) {
        val c = b.tripCard
        val pinNeeded = t.phase == TripPhase.AT_PICKUP && t.pin != null && !d.pinVerified
        c.tripTitle.text = getString(if (t.phase == TripPhase.ON_TRIP) R.string.drive_dropoff_title else R.string.drive_pickup_title, t.riderName)
        c.tripRider.text = t.riderRating?.let { getString(R.string.drive_rider_rating, "%.2f".format(java.util.Locale("pt", "PT"), it)) }.orEmpty()
        c.tripAddress.text = t.address
        c.tripFare.text = t.fare?.let { getString(R.string.drive_fare, it) }.orEmpty()
        c.tripFare.isVisible = t.fare != null
        c.tripWait.isVisible = t.phase == TripPhase.AT_PICKUP && t.waitStartSec != null
        t.waitStartSec?.let { start ->
            val secs = (System.currentTimeMillis() / 1000 - start).coerceAtLeast(0)
            c.tripWait.text = getString(R.string.drive_wait, "%d:%02d".format(secs / 60, secs % 60))
        }
        c.tripPinButton.isVisible = pinNeeded
        c.tripSlide.isVisible = !pinNeeded
        c.tripSlide.label = getString(
            when (t.phase) {
                TripPhase.TO_PICKUP -> R.string.drive_slide_arrived
                TripPhase.AT_PICKUP -> R.string.drive_slide_pickup
                TripPhase.ON_TRIP -> R.string.drive_slide_end
            }
        )
        c.tripSlide.reset()
        c.tripSlide.onConfirmed = {
            when (t.phase) {
                TripPhase.TO_PICKUP -> drive.arrive()
                TripPhase.AT_PICKUP -> drive.startTrip()
                TripPhase.ON_TRIP -> drive.finishTrip()
            }
        }
    }

    override fun onDestroyView() {
        timerKey = null
        alertOfferUuid = null
        alerts?.stop()
        alerts = null
        binding = null
        super.onDestroyView()
    }
}
