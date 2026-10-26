package com.qolari.drivereplica

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.content.res.Configuration
import android.os.Build
import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.isVisible
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
import com.qolari.drivereplica.push.PushRegistrar
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

    override fun attachBaseContext(newBase: Context) {
        val prefs = newBase.getSharedPreferences("qolari_ui", Context.MODE_PRIVATE)
        if (prefs.getBoolean("simple", false)) {
            val config = Configuration(newBase.resources.configuration)
            config.fontScale = 1.15f
            super.attachBaseContext(newBase.createConfigurationContext(config))
        } else {
            super.attachBaseContext(newBase)
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)
        if (Build.VERSION.SDK_INT >= 33 &&
            checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED
        ) {
            requestPermissions(arrayOf(Manifest.permission.POST_NOTIFICATIONS), 101)
        }

        val navHost = supportFragmentManager.findFragmentById(R.id.navHost) as NavHostFragment
        val nav = navHost.navController
        // O destino inicial depende da sessão (sem token: boas-vindas), por isso o grafo é montado aqui.
        lifecycleScope.launch {
            val graph = nav.navInflater.inflate(R.navigation.nav_main)
            graph.setStartDestination(if (AppGraph.repository.hasSession()) R.id.homeFragment else R.id.welcomeFragment)
            nav.graph = graph
        }
        binding.bottomNav.setupWithNavController(nav)
        // O grafo do Menu é aninhado; em alguns estados o NavigationUI resolvia o separador
        // "Página inicial" para o Menu. O listener explícito garante que cada separador navega
        // para o seu destino de topo.
        binding.bottomNav.setOnItemSelectedListener { item ->
            runCatching { nav.navigate(item.itemId) }
            true
        }
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
        binding.bottomNav.getOrCreateBadge(R.id.menuTab).backgroundColor = getColor(R.color.qd_core_blue600)
        nav.addOnDestinationChangedListener { _, destination, _ ->
            val tabs = destination.id !in fullScreenDestinations
            binding.bottomNav.isVisible = tabs
            binding.bottomNavDivider.isVisible = tabs
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

    override fun onResume() {
        super.onResume()
        lifecycleScope.launch {
            if (AppGraph.repository.hasSession()) PushRegistrar.register()
        }
    }
}
