package com.qolari.drivereplica.ui.settings

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import androidx.fragment.app.activityViewModels
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import androidx.navigation.fragment.findNavController
import com.qolari.drivereplica.R
import com.qolari.drivereplica.databinding.FragmentNavigationSettingsBinding
import com.qolari.drivereplica.databinding.ItemChoiceRowBinding
import com.qolari.drivereplica.state.NavApp
import com.qolari.drivereplica.state.PreferencesViewModel
import kotlinx.coroutines.launch

/** Navegação (Views; captura 046): escolha da aplicação de navegação com visto azul e interruptor de navegação automática. */
class NavigationSettingsFragment : Fragment() {

    private val prefs: PreferencesViewModel by activityViewModels()
    private var _binding: FragmentNavigationSettingsBinding? = null
    private val binding get() = _binding!!
    private val rows = mutableMapOf<NavApp, ItemChoiceRowBinding>()

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentNavigationSettingsBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        binding.navBack.setOnClickListener { findNavController().popBackStack() }
        val inflater = LayoutInflater.from(requireContext())
        val apps = listOf(
            Triple(NavApp.OWN, R.string.nav_own, R.string.nav_own_desc),
            Triple(NavApp.GOOGLE_MAPS, R.string.nav_gmaps, R.string.nav_separate_app),
            Triple(NavApp.WAZE, R.string.nav_waze, R.string.nav_separate_app),
        )
        apps.forEach { (app, title, subtitle) ->
            val row = ItemChoiceRowBinding.inflate(inflater, binding.navApps, false)
            row.choiceTitle.setText(title)
            row.choiceTitle.textSize = 18f
            row.choiceSubtitle.setText(subtitle)
            row.choiceSubtitle.textSize = 14f
            row.choiceSubtitle.visibility = View.VISIBLE
            row.choiceDivider.visibility = View.GONE
            row.choiceContent.setOnClickListener { prefs.store.setNavApp(app) }
            binding.navApps.addView(row.root)
            rows[app] = row
        }
        binding.navAutoSwitch.setOnCheckedChangeListener { _, checked -> prefs.store.setAutoStart(checked) }

        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                prefs.store.navigation.collect { n ->
                    rows.forEach { (app, row) -> row.choiceCheck.visibility = if (app == n.app) View.VISIBLE else View.INVISIBLE }
                    if (binding.navAutoSwitch.isChecked != n.autoStart) binding.navAutoSwitch.isChecked = n.autoStart
                }
            }
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        rows.clear()
        _binding = null
    }
}
