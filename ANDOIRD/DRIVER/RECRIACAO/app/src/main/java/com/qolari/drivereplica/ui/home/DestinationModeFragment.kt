package com.qolari.drivereplica.ui.home

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.LinearLayout
import android.widget.TextView
import androidx.core.view.isVisible
import androidx.fragment.app.Fragment
import androidx.fragment.app.activityViewModels
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import androidx.navigation.fragment.findNavController
import com.qolari.drivereplica.R
import com.qolari.drivereplica.databinding.FragmentDestinationModeBinding
import com.qolari.drivereplica.drive.DestinationMode
import com.qolari.drivereplica.drive.DriveViewModel
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

/**
 * "Modo Destino" (print do utilizador, 2026-10-31 16:24), aberto pela lupa do mapa.
 *
 * O motorista marca para onde quer ir e só lhe são propostas viagens cujo DESTINO fica
 * dentro de `destination_mode_radius_km` (7 km) desse ponto. Tem
 * `destination_mode_daily_filters` (2) filtros por dia, contados no servidor.
 *
 * A pesquisa usa o Places Autocomplete; a escolha de uma sugestão grava as coordenadas no
 * servidor. Nada é inventado: se o Places não responder, a lista fica vazia e diz-se porquê.
 */
class DestinationModeFragment : Fragment(R.layout.fragment_destination_mode) {

    private val drive: DriveViewModel by activityViewModels { DriveViewModel.Factory }
    private var binding: FragmentDestinationModeBinding? = null
    private var searchJob: Job? = null

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        val b = FragmentDestinationModeBinding.bind(view)
        binding = b
        b.destBack.setOnClickListener { findNavController().popBackStack() }

        b.destSearch.addTextChangedListener(object : android.text.TextWatcher {
            override fun afterTextChanged(s: android.text.Editable?) {
                val q = s?.toString()?.trim().orEmpty()
                searchJob?.cancel()
                if (q.length < 3) {
                    b.destSuggestions.removeAllViews()
                    return
                }
                // Debounce: o Places cobra por pedido e o utilizador escreve depressa.
                // O pedido é I/O bloqueante: tem de correr fora do main thread.
                searchJob = viewLifecycleOwner.lifecycleScope.launch {
                    delay(350)
                    val places = withContext(kotlinx.coroutines.Dispatchers.IO) {
                        PlacesClient.search(requireContext(), q)
                    }
                    if (binding != null) showSuggestions(b, places)
                }
            }
            override fun beforeTextChanged(s: CharSequence?, a: Int, bb: Int, c: Int) = Unit
            override fun onTextChanged(s: CharSequence?, a: Int, bb: Int, c: Int) = Unit
        })

        b.destSwitch.setOnClickListener {
            val st = drive.state.value.destination
            if (st.enabled) {
                // Desligar não gasta filtro.
                drive.setDestination(null, null, "")
            } else {
                val lat = st.latitude
                val lng = st.longitude
                if (lat != null && lng != null) {
                    drive.setDestination(lat, lng, st.label)
                } else {
                    // Sem destino marcado ainda: o interruptor não pode ligar sozinho.
                    b.destSearch.requestFocus()
                    b.destSwitch.isChecked = false
                }
            }
        }

        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                drive.state.collect { s -> bind(b, s.destination) }
            }
        }
    }

    private fun bind(b: FragmentDestinationModeBinding, m: DestinationMode) {
        b.destSwitch.isChecked = m.enabled
        b.destFiltersLeft.text = if (m.filtersLeft > 0) {
            getString(R.string.dest_filters_left, m.filtersLeft, m.filtersTotal)
        } else {
            getString(R.string.dest_no_filters)
        }
        if (m.enabled && m.label.isNotBlank()) {
            b.destSearch.setText(m.label)
        }
    }

    private fun showSuggestions(b: FragmentDestinationModeBinding, places: List<Place>) {
        b.destSuggestions.removeAllViews()
        places.forEach { p ->
            val row = TextView(requireContext()).apply {
                text = p.description
                textSize = 17f
                setTextColor(requireContext().getColor(R.color.qd_ink))
                setPadding(dp(16), dp(16), dp(16), dp(16))
                setBackgroundResource(android.R.drawable.list_selector_background)
                setOnClickListener {
                    // Marcar o destino: liga o modo e consome um filtro.
                    drive.setDestination(p.latitude, p.longitude, p.description)
                    b.destSearch.setText(p.description)
                    findNavController().popBackStack()
                }
            }
            b.destSuggestions.addView(row)
            b.destSuggestions.addView(View(requireContext()).apply {
                layoutParams = LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, dp(1))
                setBackgroundResource(R.color.qd_line)
            })
        }
        b.destSuggestions.isVisible = places.isNotEmpty()
    }

    private fun dp(v: Int) = (v * resources.displayMetrics.density).toInt()

    override fun onDestroyView() {
        searchJob?.cancel()
        binding = null
        super.onDestroyView()
    }
}
