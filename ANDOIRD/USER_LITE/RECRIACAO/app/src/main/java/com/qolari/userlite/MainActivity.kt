package com.qolari.userlite

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
import com.qolari.userlite.data.AppGraph
import com.qolari.userlite.databinding.ActivityMainBinding
import com.qolari.userlite.push.PushRegistrar
import kotlinx.coroutines.launch

/** Atividade única: hospeda a navegação e o banner "Sem conexão de rede". */
class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding

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

    override fun onResume() {
        super.onResume()
        lifecycleScope.launch {
            if (AppGraph.repository.hasSession()) PushRegistrar.register()
        }
    }
}
