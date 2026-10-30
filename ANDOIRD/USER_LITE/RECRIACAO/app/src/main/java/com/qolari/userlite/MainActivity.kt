package com.qolari.userlite

import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.isVisible
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import androidx.navigation.fragment.NavHostFragment
import com.qolari.userlite.data.AppGraph
import com.qolari.userlite.databinding.ActivityMainBinding
import kotlinx.coroutines.launch

/** Atividade única: hospeda a navegação e o banner "Sem conexão de rede". */
class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        val navHost = supportFragmentManager.findFragmentById(R.id.navHost) as NavHostFragment
        val nav = navHost.navController
        lifecycleScope.launch {
            val graph = nav.navInflater.inflate(R.navigation.nav_main)
            graph.setStartDestination(
                if (AppGraph.repository.hasSession()) R.id.homeFragment else R.id.welcomeFragment
            )
            nav.graph = graph
        }

        lifecycleScope.launch {
            repeatOnLifecycle(Lifecycle.State.STARTED) {
                AppGraph.network.connected.collect { connected ->
                    binding.offlineBanner.isVisible = !connected
                }
            }
        }
    }
}
