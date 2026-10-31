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
        // Botões da navegação (prints de 2026-10-30): A+ relata um obstáculo aos próximos
        // condutores, o atalho mostra o percurso completo e o escudo abre o Conjunto de
        // Ferramentas de Segurança. Os filtros escolhem os serviços com que se trabalha.
        b.navReport.setOnClickListener { MapReportSheet.show(this) }
        b.navRoute.setOnClickListener { toggleNavigationMode(b) }
        b.navShield.setOnClickListener {
            com.qolari.drivereplica.ui.manage.SafetySheet.show(this)
        }
        b.navFilters.setOnClickListener { findNavController().navigate(R.id.preferencesServicesFragment) }
        // Atalhos do mapa em repouso (ids do original em ub__map_controls.xml):
        //   escudo        -> safety_toolkit_container
        //   A+ (pin+)     -> ugc_container  (relatório de mapa)
        //   gráfico       -> earnings_trends_container
        //   localizar     -> bottom_right_center_me ("Center map")
        // O raio saiu: no original só existe em banners de Boost e não temos ecrã de zonas.
        b.mapShield.setOnClickListener {
            com.qolari.drivereplica.ui.manage.SafetySheet.show(this)
        }
        b.mapReportShortcut.setOnClickListener { MapReportSheet.show(this) }
        b.mapTrendsShortcut.setOnClickListener {
            // "Earnings Trends" no original é um ecrã próprio; aqui o mais perto que existe é o
            // separador Rendimentos (que tem o gráfico da semana). Muda de separador em vez de
            // inventar um ecrã novo.
            requireActivity()
                .findViewById<com.google.android.material.bottomnavigation.BottomNavigationView>(R.id.bottomNav)
                ?.selectedItemId = R.id.earningsFragment
        }
        b.mapLocateShortcut.setOnClickListener {
            // "Center map": volta a câmara ao motorista (o mapa já segue o GPS).
            b.mapFull.deviceLocation = AppGraph.location.lastKnown()
        }
        // Botão de lista do canto inferior direito: abre o Planeador de viagem (print 01:57).
        b.pickupNavBar.pickupNavOptions.setOnClickListener {
            findNavController().navigate(R.id.tripPlannerFragment)
        }
        // Filtros da barra de estado: mesmo destino do filtro solto da esquerda. Antes era um
        // ImageView decorativo e o ecrã tinha dois ícones de filtros, só um a funcionar.
        b.pickupNavBar.pickupNavIcon.setOnClickListener {
            findNavController().navigate(R.id.preferencesServicesFragment)
        }

        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                launch {
                    // Espera na recolha: contagem decrescente do tempo grátis, como no vídeo.
                    while (true) {
                        val t = drive.state.value.trip
                        val start = t?.waitStartSec
                        val free = t?.waitFreeSec
                        if (t != null && t.phase == TripPhase.AT_PICKUP && start != null) {
                            val text = formatWait(start, free)
                            // Cartão antigo (só o PIN) e cartão novo da espera partilham o texto.
                            b.tripCard.tripWait.text = getString(R.string.drive_wait, text)
                            b.waitCard.waitTimer.text = text
                            b.waitCard.waitProgress.progress = waitPercent(start, free)
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
        // O botão "Navegar"/"Vista geral" só aparece na VISTA GERAL (vídeo 2026-10-30): em modo
        // navegação o original esconde-o e deixa só o mapa.
        b.navButton.isVisible = navigating && !navMode
        // Botões da fase de recolha/viagem (prints de 2026-10-30): A+ e atalho do percurso à
        // direita, escudo e filtros à esquerda. Só existem nos ecrãs de navegação.
        b.navActions.isVisible = navigating
        b.navShield.isVisible = navigating
        b.navFilters.isVisible = navigating
        // Na vista geral o botão "Navegar" aparece em baixo a direita: a coluna do A+ tem de
        // subir para não ficar por cima dele.
        applyNavLayout(b, navigating)
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
                            // Sem a rota do servidor, pede-se a perna cliente -> destino aqui,
                            // para as DUAS pernas ficarem sempre visíveis até aceitar/recusar.
                            DirectionsClient.fetch(requireContext(), pickup.first, pickup.second, dropoff.first, dropoff.second) { trip ->
                                if (binding == null) return@fetch
                                // Mesmo com falha no Google, desenha-se a ligação direta:
                                // um cartão sem traço nenhum não mostra o percurso.
                                val tripLeg = if (trip.size > 1) trip else listOf(pickup, dropoff)
                                val pickLeg = if (toPickup.size > 1) toPickup else listOf(from, pickup)
                                b.mapFull.setOfferRoutes(pickLeg, tripLeg, cardH())
                            }
                        }
                    }
                } else {
                    // Sem GPS: liga o motorista à recolha e a recolha ao destino na mesma.
                    val tripLeg = if (tripRoute.size > 2) tripRoute else listOf(pickup, dropoff)
                    b.mapFull.setOfferRoutes(emptyList(), tripLeg, cardH())
                }

                card.post {
                    if (binding == null) return@post
                    // Plano amplo: as duas pernas + motorista, sempre visíveis.
                    b.mapFull.reframe()
                }
                // Repete depois do layout: a altura real do cartão só é conhecida então.
                b.mapFull.postDelayed({
                    if (binding != null) b.mapFull.reframe()
                }, 400)
                b.mapFull.postDelayed({
                    if (binding != null) b.mapFull.reframe()
                }, 900)
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
            // o original mostra primeiro a VISTA GERAL com o botão "Navegar" e só depois entra
            // no modo navegação (vídeo 2026-10-30, 0:00→0:02). Sem esta paragem inicial o botão
            // nunca chegava a aparecer, porque em modo navegação ele está escondido.
            if (d.stage != lastNavStage) {
                lastNavStage = d.stage
                val auto = prefs.store.navigation.value.autoStart
                navMode = !auto
                b.mapFull.navigating = navMode
                b.navButton.isVisible = !navMode
                b.navButton.setText(if (navMode) R.string.nav_wide else R.string.nav_navigate)
                if (auto) {
                    // "Navegação automática": a vista geral fica ~2 s e depois cola a câmara.
                    b.mapFull.postDelayed({
                        if (binding != null && lastNavStage == d.stage && !navMode) {
                            navMode = true
                            b.mapFull.navigating = true
                            b.navButton.isVisible = false
                            b.navButton.setText(R.string.nav_wide)
                        }
                    }, NAV_AUTO_START_MS)
                }
            }
            // O mapa em navegação usa o estilo do Google Maps (ruas e nomes), não o mapa limpo
            // do ecrã inicial — sem isto "não se percebe nada" (feedback de 2026-10-30).
            b.mapFull.thickNavigation = true
            if (d.route.size > 1 && d.route != b.mapFull.route) b.mapFull.route = d.route
            // Pino da paragem da fase (vídeo 2026-10-30): verde na recolha, vermelho no destino.
            // Só um pino por fase — o mapa de navegação não mostra o outro extremo.
            val stopPoint = d.navigation?.stop?.let { stop ->
                when (stop.kind) {
                    "dropoff" -> d.trip?.let { t ->
                        if (t.latitude != null && t.longitude != null) t.latitude to t.longitude else null
                    }
                    else -> d.trip?.let { t -> t.pickupLat?.let { la -> t.pickupLng?.let { lo -> la to lo } } }
                }
            }
            b.mapFull.setNavStop(stopPoint, d.navigation?.stop?.kind)
            bindNavigation(b, d)
            return
        }
        lastNavStage = null
        b.mapFull.thickNavigation = false
        b.mapFull.setStreetLabel(null)
        b.mapFull.setNavStop(null, null)
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
            // Vídeo 2026-10-30: a barra sobe para o TOPO do cartão de espera em vez de ficar por
            // baixo dele (no original o cartão entra pela base e empurra a barra para cima).
            bar.root.post {
                if (binding == null) return@post
                val cardH = b.waitCard.root.takeIf { it.isVisible }?.height ?: 0
                bar.root.translationY = -cardH.toFloat()
            }
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
        // A bordo, o mesmo cartão mostra "Concluir <produto>": é o único caminho para terminar a
        // viagem pela UI (o cartão antigo com o deslize só existe quando há PIN).
        val onTrip = trip != null && d.stage == DriveStage.ON_TRIP
        b.waitCard.root.isVisible = waiting || onTrip
        // O cartão antigo só serve agora para o PIN (quando o passageiro o pediu).
        val pinNeeded = waiting && trip?.pin != null && !d.pinVerified
        b.tripCard.root.isVisible = pinNeeded
        if (trip != null && pinNeeded) bindTrip(b, trip, d)
        if (trip != null && (waiting || onTrip)) bindWaitCard(b, trip, d, onTrip)

        updateAudioNotice(b, d)

        val sheet = childFragmentManager.findFragmentByTag("rating")
        if (d.stage == DriveStage.RATING && d.summary != null) {
            if (sheet == null) RatingSheet().show(childFragmentManager, "rating")
        } else if (sheet is androidx.fragment.app.DialogFragment) {
            sheet.dismissAllowingStateLoss()
        }
    }

    private var timerKey: String? = null

    /**
     * Cartão de espera / de viagem (vídeo 2026-10-30): nome, contacto, contador "À espera do
     * utilizador" com barra azul, e o botão "Começar <produto>" — ou "Concluir <produto>" quando
     * o passageiro já está a bordo.
     */
    private fun bindWaitCard(b: FragmentMapBinding, t: ActiveTrip, d: DriveUiState, onTrip: Boolean) {
        val c = b.waitCard
        val product = t.product?.takeIf { it.isNotBlank() } ?: getString(R.string.drive_product_fallback)
        c.waitName.text = t.riderName
        c.waitStartLabel.text = getString(
            if (onTrip) R.string.trip_finish else R.string.wait_start,
            product,
        )
        // A bordo já não há espera: esconde o contador e mostra só o contacto + "Concluir".
        c.waitPanel.isVisible = !onTrip
        if (onTrip) {
            c.waitStart.setOnClickListener { drive.finishTrip() }
            c.waitStart.isEnabled = !d.busy
            return
        }
        // O contador conta desde a chegada (waitTimeTaskData.startTimeSec do servidor).
        c.waitTimer.text = formatWait(t.waitStartSec, t.waitFreeSec)
        val pct = waitPercent(t.waitStartSec, t.waitFreeSec)
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

    /**
     * Contagem decrescente da espera grátis (`waitFreeSec`, 2 min por omissão) — como no vídeo de
     * 2026-10-30, onde o contador desce de 1:44 até 0:00. Antes subia desde a chegada.
     * A chegar a 0 mostra "0:00": o tempo grátis acabou.
     */
    private fun formatWait(startSec: Long?, freeSec: Long? = null): String {
        if (startSec == null) return "0:00"
        val free = freeSec ?: DEFAULT_WAIT_FREE_S
        val elapsed = (System.currentTimeMillis() / 1000 - startSec).coerceAtLeast(0)
        val left = (free - elapsed).coerceAtLeast(0)
        return "%d:%02d".format(left / 60, left % 60)
    }

    /**
     * Barra da espera. Decisão do cliente (2026-10-31): com progresso, ao contrário do original
     * (onde é fixa). Enche à medida que o tempo grátis é consumido.
     */
    private fun waitPercent(startSec: Long?, freeSec: Long? = null): Int {
        if (startSec == null) return 0
        val free = (freeSec ?: DEFAULT_WAIT_FREE_S).coerceAtLeast(1)
        val elapsed = (System.currentTimeMillis() / 1000 - startSec).coerceAtLeast(0)
        return ((elapsed * 100) / free).coerceIn(0, 100).toInt()
    }

    /**
     * Aviso de gravacao de audio (video 2026-10-30): mostra-se nos primeiros segundos de cada
     * viagem aceite e desaparece sozinho. Guarda a viagem para nao voltar a aparecer.
     */
    private var audioNoticeTrip: String? = null

    /** Modo da câmara: true = navegação (câmara colada), false = vista ampla do percurso. */
    private var navMode = false
    /** Última fase em que se entrou em navegação, para a transição automática só acontecer uma vez. */
    private var lastNavStage: DriveStage? = null

    /**
     * Botões em baixo, à direita, na vista geral: o "Navegar" fica mais perto da barra e a coluna
     * do A+ sobe acima dele. Os dois partilham a mesma margem (`112dp`) e, sem separação, o círculo
     * do atalho ficava por cima do texto "Navegar" e só se lia "Nav" (visto no Mi a 2026-10-31).
     *
     * A altura do "Navegar" é 44dp e a coluna do A+ tem dois botões de 52dp com 12dp entre eles
     * (116dp); o deslocamento tem de ser a altura do botão + a folga, não um valor redondo.
     */
    private fun applyNavLayout(b: FragmentMapBinding, navigating: Boolean) {
        val d = resources.displayMetrics.density
        val wide = navigating && !navMode
        // +14dp de folga entre o topo do "Navegar" e a base do atalho.
        val lift = if (wide) (44 + 14) * d else 0f
        b.navActions.translationY = -lift
    }

    /**
     * Botão "Navegar" (vídeo 2026-10-30): na vista geral mostra "Navegar" e leva à navegação.
     * Em modo navegação o botão desaparece, como no original - o mapa fica limpo.
     */
    private fun toggleNavigationMode(b: FragmentMapBinding) {
        navMode = !navMode
        b.mapFull.navigating = navMode
        // Escondido a navegar; visível na vista geral, onde diz "Navegar" para voltar.
        b.navButton.isVisible = !navMode
        b.navButton.setText(if (navMode) R.string.nav_wide else R.string.nav_navigate)
        // A coluna do A+ acompanha o modo: ao voltar à vista geral tem de subir para não tapar
        // o "Navegar", e ao entrar em navegação tem de descer outra vez.
        applyNavLayout(b, navigating = true)
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
            val step = nav.current
            // Distância separada: "140" grande e "m" pequeno (vídeo 2026-10-30).
            panel.maneuverDistance.text = step.distanceValue.ifBlank { step.distance }
            panel.maneuverDistanceUnit.text = step.distanceUnit
            panel.maneuverDistanceUnit.isVisible = step.distanceUnit.isNotBlank()
            // Texto rico da 1.ª secção: via a branco + "em direção a" cinza + destino a branco.
            panel.maneuverRoad.text = maneuverText(step)
            // Chegou ao destino final: a 1.ª secção passa a bandeira (vídeo 2026-10-30, 10:04).
            panel.maneuverIcon.setImageResource(
                if (nav.atDestination) R.drawable.ic_flag_finish else maneuverIcon(step.maneuver)
            )
        }
        // 2.ª secção: o vídeo alterna entre a PRÓXIMA manobra (enquanto houver outra à frente)
        // e a PARAGEM (quando a manobra actual já é a última). Nunca as duas ao mesmo tempo.
        val stop = nav?.stop
        val showStop = nav != null && nav.secondaryIsStop
        panel.stopSection.isVisible = showStop
        panel.nextSection.isVisible = hasPanel && !showStop && nav?.next != null
        panel.maneuverDivider.isVisible = hasPanel
        if (hasPanel && !showStop) {
            val nxt = nav?.next
            if (nxt != null) {
                panel.nextIcon.setImageResource(maneuverIcon(nxt.maneuver))
                panel.nextRoad.text = nxt.road.ifBlank { nxt.distance }
            }
        }
        if (showStop && stop != null) {
            panel.stopAddress.text = stop.address
            panel.stopCity.text = stop.city
            panel.stopCity.isVisible = stop.city.isNotBlank()
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
        b.mapFull.setStreetLabel(nav?.current?.street?.ifBlank { nav?.current?.via?.ifBlank { null } })
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
        // O símbolo da barra acompanha a fase: disco verde com pessoa na recolha,
        // quadrado vermelho na entrega (vídeo 2026-10-30).
        // No disco NAO se aplica tint: o drawable já traz o círculo verde e a pessoa branca,
        // e um tint verde pintava também a pessoa (via-se só a silhueta).
        val dropoffPhase = trip?.phase == TripPhase.ON_TRIP
        bar.pickupNavDot.setImageResource(
            if (dropoffPhase) R.drawable.ic_stop_dot_square else R.drawable.ic_person_disc
        )
        bar.pickupNavDot.imageTintList = if (dropoffPhase) {
            android.content.res.ColorStateList.valueOf(requireContext().getColor(R.color.qd_stop_dropoff))
        } else {
            null
        }
        // O traço fino não deve ficar por baixo da barra inferior.
        bar.root.post {
            if (binding != null) b.mapFull.setBottomPadding(bar.root.height)
        }
    }

    /**
     * Texto da 1.ª secção do painel, como no vídeo de 2026-10-30:
     *   "Avenida Duque de Loulé **em** direção a Praça do Marquês de Pombal"
     * A via e o destino ficam a branco (tamanho normal) e o "em direção a" em cinza e mais
     * pequeno. Sem destino conhecido fica só o nome da via.
     */
    private fun maneuverText(step: com.qolari.drivereplica.drive.NavigationStep): CharSequence {
        val via = step.via.ifBlank { step.street }.ifBlank { step.road }
        val toward = step.toward.ifBlank { step.road }
        if (via.isBlank()) return step.road
        // Sem destino distinto da via não há frase a compor: mostra só a via.
        if (toward.isBlank() || toward.equals(via, ignoreCase = true)) return via
        val join = android.text.SpannableStringBuilder()
        join.append(via)
        join.append(" em direção a ")
        join.setSpan(
            android.text.style.ForegroundColorSpan(requireContext().getColor(R.color.qd_maneuver_secondary)),
            via.length, join.length,
            android.text.Spanned.SPAN_EXCLUSIVE_EXCLUSIVE,
        )
        join.setSpan(
            android.text.style.RelativeSizeSpan(0.74f),
            via.length, join.length,
            android.text.Spanned.SPAN_EXCLUSIVE_EXCLUSIVE,
        )
        join.append(toward)
        // O texto é branco por defeito (TextView); só o conector é pintado por cima.
        return join
    }

    private fun hideNavigation(b: FragmentMapBinding) {
        b.maneuverPanel.root.isVisible = false
        b.pickupNavBar.root.isVisible = false
        b.speedBadge.isVisible = false
        b.navButton.isVisible = false
        // A barra sobe por cima do cartão de espera (translationY negativo). Ao sair da espera
        // tem de voltar ao fundo, senão fica a flutuar a meio do mapa — visto no Mi a 2026-10-31.
        b.pickupNavBar.root.translationY = 0f
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

    /** Moradas separadas em rua + cidade, como no cartão do vídeo (cidade em linha própria). */
    private fun splitCity(raw: String): Pair<String, String> {
        val clean = raw.trim()
        val comma = clean.lastIndexOf(',')
        if (comma <= 0) return clean to ""
        val tail = clean.substring(comma + 1).trim()
        // Só separa quando a cauda parece uma localidade (curta e sem números).
        if (tail.length !in 2..28 || tail.any { it.isDigit() }) return clean to ""
        return clean.substring(0, comma).trim() to tail
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
        // Rua em bold + cidade em linha própria, cinza (vídeo 2026-10-29):
        //   "Avenida Doutor José Pontes 5"
        //   "Amadora"
        val (pickupStreet, pickupCity) = splitCity(o.pickupAddress)
        c.offerPickupAddress.text = pickupStreet
        c.offerPickupCity.text = pickupCity
        c.offerPickupCity.isVisible = pickupCity.isNotBlank()
        c.offerTripLine.text = o.tripLine
        c.offerTripLine.isVisible = o.tripLine != null
        val (dropStreet, dropCity) = splitCity(o.dropoffAddress.orEmpty())
        c.offerDropoffAddress.text = dropStreet
        c.offerDropoffAddress.isVisible = o.dropoffAddress != null
        c.offerDropoffCity.text = dropCity
        c.offerDropoffCity.isVisible = dropCity.isNotBlank()
        // O rail acompanha o bloco de textos: círculo na 1.ª linha, quadrado na última.
        c.offerRail.post {
            val d = resources.displayMetrics.density
            val containerTop = c.offerRail.top.toFloat()
            c.offerRail.pickupCenterDp =
                (c.offerPickupLine.top + c.offerPickupLine.height / 2f - containerTop) / d
            val last = if (c.offerDropoffCity.isVisible) c.offerDropoffCity
                       else if (c.offerDropoffAddress.isVisible) c.offerDropoffAddress
                       else c.offerTripLine
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

    /**
     * Aviso "O passageiro pode gravar audio nesta viagem" (video 2026-10-30, 0:00-0:07).
     * Aparece uma vez por viagem, por cima da barra, e sai ao fim de [AUDIO_NOTICE_MS].
     */
    private fun updateAudioNotice(b: FragmentMapBinding, d: DriveUiState) {
        val trip = d.trip
        val navigating = d.stage == DriveStage.TO_PICKUP || d.stage == DriveStage.ON_TRIP
        if (trip == null || !navigating) {
            if (audioNoticeTrip != null && trip == null) {
                audioNoticeTrip = null
                b.audioNotice.root.isVisible = false
            }
            return
        }
        if (audioNoticeTrip == trip.uuid) return
        audioNoticeTrip = trip.uuid
        // O cartao vive no fundo do FrameLayout, por cima da barra de estado e da coluna de
        // botoes (A+, atalho, escudo, filtros). Subia so pela altura da barra e continuava a tapar
        // os botoes durante os 7 s (reportado a 2026-10-31). Sobe pela barra + a margem dos botoes.
        val bar = b.pickupNavBar.root
        val dpm = resources.displayMetrics.density
        b.audioNotice.root.post {
            if (binding == null) return@post
            val barH = if (bar.isVisible && bar.height > 0) bar.height else 0
            val buttonsH = (NAV_BUTTONS_BOTTOM_DP * dpm).toInt()
            b.audioNotice.root.translationY = -(barH + buttonsH).toFloat()
        }
        b.audioNotice.root.isVisible = true
        b.audioNotice.root.postDelayed({
            if (binding != null) b.audioNotice.root.isVisible = false
        }, AUDIO_NOTICE_MS)
    }

    override fun onDestroyView() {
        audioNoticeTrip = null
        timerKey = null
        alertOfferUuid = null
        alerts?.stop()
        alerts = null
        binding = null
        super.onDestroyView()
    }

    private companion object {
        /**
         * Tempo da vista geral antes de a navegação automática arrancar (vídeo 2026-10-30:
         * o botão "Navegar" e o percurso inteiro ficam ~2 s à vista antes de a câmara colar).
         */
        const val NAV_AUTO_START_MS = 2200L

        /** Tempo do aviso de gravacao de audio no ecra (video: ~7 s). */
        const val AUDIO_NOTICE_MS = 7000L

        /**
         * Altura reservada pelos botoes de navegacao acima da barra (`navShield`/`navFilters`
         * usam `marginBottom=112dp`). O aviso sobe pela barra + este valor para nao os tapar.
         */
        const val NAV_BUTTONS_BOTTOM_DP = 112

        /** Espera grátis na recolha, quando o servidor não manda `freeWaitSec` (2 min). */
        const val DEFAULT_WAIT_FREE_S = 120L
    }
}
