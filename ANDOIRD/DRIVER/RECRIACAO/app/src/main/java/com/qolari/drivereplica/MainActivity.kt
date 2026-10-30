package com.qolari.drivereplica

import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.isVisible
import androidx.core.view.doOnLayout
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import androidx.navigation.fragment.NavHostFragment
import androidx.navigation.ui.setupWithNavController
import com.qolari.drivereplica.data.AppGraph
import androidx.activity.viewModels
import com.qolari.drivereplica.databinding.ActivityMainBinding
import com.qolari.drivereplica.drive.DriveStage
import com.qolari.drivereplica.drive.DriveViewModel
import com.qolari.drivereplica.ui.home.HomeViewModel
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.distinctUntilChanged
import kotlinx.coroutines.launch

/** Atividade única (STACK_DECISAO.md): hospeda a navegação, o banner sem rede e a barra de 5 separadores. */
class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding
    private val home: HomeViewModel by viewModels { HomeViewModel.Factory }
    private val drive: DriveViewModel by viewModels { DriveViewModel.Factory }

    /** Destinos de ecrã inteiro, sem a barra de separadores (modo mapa, captura 110; boas-vindas e login, 031-033). */
    private val fullScreenDestinations = setOf(R.id.mapFragment, R.id.welcomeFragment, R.id.loginPhoneFragment, R.id.loginCodeFragment)

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        val navHost = supportFragmentManager.findFragmentById(R.id.navHost) as NavHostFragment
        val nav = navHost.navController
        // O destino inicial depende da sessão (sem token: boas-vindas), por isso o grafo é montado aqui.
        lifecycleScope.launch {
            val graph = nav.navInflater.inflate(R.navigation.nav_main)
            graph.setStartDestination(if (AppGraph.repository.hasSession()) R.id.homeFragment else R.id.welcomeFragment)
            nav.graph = graph
        }
        binding.bottomNav.setupWithNavController(nav)
        // Contador na Caixa de entrada e ponto no Menu (capturas 000/060). O ponto do Menu continua de exemplo.
        val inboxBadge = binding.bottomNav.getOrCreateBadge(R.id.inboxFragment).apply {
            backgroundColor = getColor(R.color.qd_core_blue600)
            badgeTextColor = getColor(R.color.qd_core_white)
            isVisible = false
        }
        // Contador real: vem das notificações do servidor (atualiza ao arrancar e ao abrir a Caixa de entrada).
        lifecycleScope.launch { AppGraph.repository.notifications() }
        lifecycleScope.launch {
            AppGraph.repository.unread.collect { n ->
                inboxBadge.isVisible = n > 0
                if (n > 0) inboxBadge.number = n
            }
        }
        // Os rótulos têm de caber em 1/5 da largura e acabar em "…" (captura 064: "Página inici…", "Caixa de en…").
        // A original limita cada etiqueta a ~60dp; sem isto "Página inicial" e "Rendimentos" cabiam inteiros.
        binding.bottomNav.doOnLayout {
            val limit = (60 * resources.displayMetrics.density).toInt()
            for (i in 0 until binding.bottomNav.menu.size()) {
                val item = binding.bottomNav.menu.getItem(i)
                binding.bottomNav.findViewById<android.view.View>(item.itemId)?.let { clampLabels(it, limit) }
            }
        }
        nav.addOnDestinationChangedListener { _, destination, _ ->
            val tabs = destination.id !in fullScreenDestinations
            binding.bottomNav.isVisible = tabs
            binding.bottomNavDivider.isVisible = tabs
            // A original não mostra ponto no separador Menu (capturas 061-064): só o contador da Caixa de entrada.
        }

        // Estar online liga a sondagem de propostas e viagens; uma proposta ou viagem leva sempre ao modo mapa.
        lifecycleScope.launch {
            home.state.map { it.online }.distinctUntilChanged().collect { drive.setOnline(it) }
        }
        lifecycleScope.launch {
            drive.state.map { it.stage }.distinctUntilChanged().collect { stage ->
                if (stage != DriveStage.IDLE && nav.currentDestination?.id != R.id.mapFragment && nav.currentDestination?.id != null) {
                    nav.navigate(R.id.mapFragment)
                }
            }
        }
        lifecycleScope.launch {
            repeatOnLifecycle(Lifecycle.State.STARTED) {
                AppGraph.network.connected.collect { connected -> binding.offlineBanner.isVisible = !connected }
            }
        }
    }

    /** Põe as etiquetas da barra em 1 linha, 12sp e com "…" dentro da largura de cada separador. */
    private fun clampLabels(view: android.view.View, maxWidth: Int) {
        if (view is android.widget.TextView) {
            view.maxLines = 1
            view.ellipsize = android.text.TextUtils.TruncateAt.END
            view.maxWidth = maxWidth
        } else if (view is android.view.ViewGroup) {
            for (i in 0 until view.childCount) clampLabels(view.getChildAt(i), maxWidth)
        }
    }
}
