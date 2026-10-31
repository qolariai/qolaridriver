package com.qolari.drivereplica.ui.home

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.widget.GridLayout
import androidx.fragment.app.Fragment
import androidx.fragment.app.activityViewModels
import androidx.navigation.fragment.findNavController
import com.qolari.drivereplica.R
import com.qolari.drivereplica.databinding.FragmentPreferencesServicesBinding
import com.qolari.drivereplica.databinding.ItemPrefsTileBinding
import com.qolari.drivereplica.state.PreferencesViewModel
import com.qolari.drivereplica.state.ServiceOption
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.launch
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle

/**
 * "Preferências" de serviços (print 2026-10-30, 02:10).
 *
 * O motorista escolhe com que categorias quer trabalhar. Disponível em todas as fases pelo
 * botão de filtros do canto inferior esquerdo do mapa. Os três primeiros vêm marcados no print.
 */
class PreferencesServicesFragment : Fragment(R.layout.fragment_preferences_services) {

    private val prefs: PreferencesViewModel by activityViewModels()
    private var binding: FragmentPreferencesServicesBinding? = null

    /** Serviços na ordem do print (2 colunas: Conforto/Package, Electric/Uber Pet, UberX/Priority). */
    private val services = listOf(
        ServiceOption("comfort", R.string.prefs_comfort, R.drawable.ic_cat_comfort),
        ServiceOption("package", R.string.prefs_package, R.drawable.ic_cat_package),
        ServiceOption("electric", R.string.prefs_electric, R.drawable.ic_cat_electric),
        ServiceOption("pet", R.string.prefs_pet, R.drawable.ic_cat_pet),
        ServiceOption("uberx", R.string.prefs_uberx, R.drawable.ic_person_filled),
        ServiceOption("priority", R.string.prefs_priority, R.drawable.ic_person_filled),
    )

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        val b = FragmentPreferencesServicesBinding.bind(view)
        binding = b
        b.prefsBack.setOnClickListener { findNavController().popBackStack() }
        // "Ver mais": a grelha já mostra os 6 serviços do print e não há referência do original
        // para o que este botão devia revelar. Fica sem ação até o cliente decidir — inventar um
        // ecrã (ou escondê-lo, contra o print) seria pior do que o botão inerte que está reportado.
        b.prefsSeeMore.setOnClickListener { }
        buildGrid(b.prefsGrid)
        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                prefs.store.services.collectLatest { s ->
                    for (i in 0 until b.prefsGrid.childCount) {
                        val tile = b.prefsGrid.getChildAt(i)
                        val id = tile.tag as? String ?: continue
                        tile.isSelected = id in s.selected
                        tile.findViewById<android.widget.ImageView>(R.id.prefsTileCheck).setImageResource(
                            if (id in s.selected) R.drawable.ic_check_box else R.drawable.ic_check_box_empty
                        )
                    }
                }
            }
        }
    }

    private fun buildGrid(grid: GridLayout) {
        grid.removeAllViews()
        val d = resources.displayMetrics.density
        val available = (resources.displayMetrics.widthPixels - (16 + 16) * d).toInt()
        services.forEach { s ->
            val tile = ItemPrefsTileBinding.inflate(layoutInflater, grid, false)
            tile.root.tag = s.id
            tile.prefsTileIcon.setImageResource(s.iconRes)
            tile.prefsTileLabel.setText(s.labelRes)
            tile.root.setOnClickListener { prefs.store.toggleService(s.id) }
            val params = GridLayout.LayoutParams().apply {
                width = available / 2
                height = (118 * d).toInt()
            }
            grid.addView(tile.root, params)
        }
    }

    override fun onDestroyView() {
        binding = null
        super.onDestroyView()
    }
}
