package com.qolari.drivereplica.ui.home

import android.Manifest
import android.os.Bundle
import androidx.activity.result.contract.ActivityResultContracts
import com.qolari.drivereplica.data.AppGraph
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.core.view.isVisible
import androidx.core.view.updateLayoutParams
import androidx.fragment.app.Fragment
import androidx.fragment.app.activityViewModels
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import androidx.navigation.fragment.findNavController
import com.qolari.drivereplica.R
import com.qolari.drivereplica.databinding.FragmentHomeBinding
import com.qolari.drivereplica.databinding.ItemBlockerBinding
import com.qolari.drivereplica.databinding.ItemHomeSectionBinding
import com.qolari.drivereplica.databinding.ItemOpportunityBinding
import kotlinx.coroutines.launch

/**
 * Página inicial em modo painel (capturas 000, 060, 117): estado, ações necessárias, mapa, oportunidades e tendências.
 * Puxar para atualizar volta a perguntar ao servidor; sem rede abre a janela "Erro" (ux_behavior.md §4).
 * As secções de baixo são conteúdo de exemplo (Fixtures): a original recebe-as do servidor de recomendações.
 */
class HomeFragment : Fragment() {

    private var _binding: FragmentHomeBinding? = null
    private val binding get() = _binding!!
    private val viewModel: HomeViewModel by activityViewModels { HomeViewModel.Factory }
    private var openMapWhenOnline = false

    private val locationPermission = registerForActivityResult(ActivityResultContracts.RequestPermission()) { toggleAndOpenMap() }

    /** Ficar online leva ao modo mapa, onde chegam as propostas (captura 110); ficar offline fica no painel. */
    private fun toggleAndOpenMap() {
        openMapWhenOnline = !viewModel.state.value.online
        viewModel.toggleOnline()
    }

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentHomeBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        val nav = findNavController()
        binding.btnExpand.setOnClickListener { nav.navigate(R.id.mapFragment) }
        binding.btnPreferences.setOnClickListener {
            // Definições vive no grafo aninhado do Menu: entrar pelo grafo e depois no ecrã.
            nav.navigate(R.id.menuTab)
            nav.navigate(
                R.id.settingsFragment,
                androidx.core.os.bundleOf(
                    com.qolari.drivereplica.ui.settings.SettingsFragment.ARG_BACK_TO to R.id.homeFragment,
                ),
            )
        }
        binding.btnSearch.setOnClickListener {
            com.qolari.drivereplica.ui.map.PlaceSearchSheet.show(childFragmentManager) { name, lat, lng ->
                binding.mapView.focus(lat, lng, name)
            }
        }
        binding.btnGoOnline.setOnClickListener {
            if (viewModel.state.value.online || AppGraph.location.hasPermission) toggleAndOpenMap()
            else locationPermission.launch(Manifest.permission.ACCESS_FINE_LOCATION)
        }
        binding.btnSafety.setOnClickListener { com.qolari.drivereplica.ui.manage.SafetySheet.show(this) }
        binding.btnBannerRetry.setOnClickListener { viewModel.refresh() }
        binding.swipe.setOnRefreshListener { viewModel.refresh() }
        buildSections()

        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                launch { viewModel.state.collect(::render) }
                launch { viewModel.events.collect { ErrorSheet.show(childFragmentManager, viewLifecycleOwner) { viewModel.refresh() } } }
            }
        }
    }

    private fun render(s: HomeUiState) {
        if (s.online && openMapWhenOnline) {
            openMapWhenOnline = false
            findNavController().navigate(R.id.mapFragment)
        } else if (s.blocked || s.failed) {
            openMapWhenOnline = false
        }
        binding.swipe.isRefreshing = s.refreshing && s.loaded
        binding.title.setText(
            when {
                s.blocked -> R.string.home_blocked
                s.online -> R.string.home_online
                else -> R.string.home_offline
            }
        )
        binding.subtitle.isVisible = !s.blocked
        binding.blockersCard.isVisible = s.blocked
        if (s.blocked) {
            binding.blockersTitle.text = getString(R.string.home_actions_title, s.blockers.size)
            binding.blockersList.removeAllViews()
            s.blockers.forEach { b ->
                val row = ItemBlockerBinding.inflate(layoutInflater, binding.blockersList, false)
                row.blockerTitle.text = b.title
                row.blockerMessage.text = b.message
                row.blockerMessage.isVisible = !b.message.isNullOrBlank()
                binding.blockersList.addView(row.root)
            }
        }
        val coldFailure = s.failed && !s.loaded
        binding.errorBanner.isVisible = coldFailure
        // Com a falha no arranque o mapa encolhe para o texto de erro caber acima do botão (captura 117).
        binding.mapCard.updateLayoutParams { height = (resources.displayMetrics.density * if (coldFailure) 180 else 260).toInt() }
        binding.errorState.isVisible = coldFailure
        binding.sections.isVisible = !coldFailure
        binding.btnGoOnline.setText(if (s.online) R.string.home_go_offline else R.string.home_go_online)
        binding.btnGoOnline.backgroundTintList = android.content.res.ColorStateList.valueOf(
            requireContext().getColor(if (s.online) R.color.qd_ink else R.color.qd_core_blue600)
        )
    }

    private fun buildSections() {
        val container = binding.sections
        // Oportunidades
        ItemHomeSectionBinding.inflate(layoutInflater, container, false).also { sec ->
            sec.sectionTitle.setText(R.string.home_section_opportunities)
            listOf(
                R.string.home_opp_1_title to R.string.home_opp_1_sub,
                R.string.home_opp_2_title to R.string.home_opp_2_sub,
                R.string.home_opp_3_title to R.string.home_opp_3_sub,
            ).forEachIndexed { index, (t, st) ->
                val item = ItemOpportunityBinding.inflate(layoutInflater, sec.sectionItems, false)
                item.oppTitle.setText(t)
                item.oppSubtitle.setText(st)
                item.oppThumb.showDemand = false
                item.oppThumb.center = listOf(
                    38.7570 to -9.2233,
                    38.7223 to -9.1393,
                    38.7742 to -9.1342,
                )[index % 3]
                sec.sectionItems.addView(item.root)
            }
            container.addView(sec.root)
        }
        // Tendências: gráfico de barras por hora.
        ItemHomeSectionBinding.inflate(layoutInflater, container, false).also { sec ->
            sec.sectionTitle.setText(R.string.home_trends_title)
            sec.sectionDesc.setText(R.string.home_trends_desc)
            sec.sectionDesc.isVisible = true
            sec.sectionChart.values = listOf(3f, 6f, 9f, 5f, 4f, 10f, 11f, 9f, 11f, 12f, 12f, 10f, 9f, 11f, 8f, 5f, 6f, 4f)
            sec.sectionChart.highlight = 14
            sec.sectionChart.isVisible = true
            container.addView(sec.root)
        }
        // Horas de ponta de voos.
        ItemHomeSectionBinding.inflate(layoutInflater, container, false).also { sec ->
            sec.sectionTitle.setText(R.string.home_airport_title)
            sec.sectionDesc.setText(R.string.home_airport_desc)
            sec.sectionDesc.isVisible = true
            sec.sectionChart.values = listOf(8f, 12f, 4f, 1f, 1f, 1f, 1f, 1f)
            sec.sectionChart.highlight = 1
            sec.sectionChart.accentIndex = 0
            sec.sectionChart.accentColor = requireContext().getColor(R.color.qd_core_blue600)
            sec.sectionChart.isVisible = true
            container.addView(sec.root)
        }
    }

    override fun onResume() {
        super.onResume()
        _binding?.let {
            it.mapView.onResume()
            if (AppGraph.location.hasPermission) it.mapView.userLocation = AppGraph.location.lastKnown()
        }
    }

    override fun onPause() {
        _binding?.mapView?.onPause()
        super.onPause()
    }

    override fun onDestroyView() {
        _binding?.mapView?.onDestroy()
        _binding = null
        super.onDestroyView()
    }
}
