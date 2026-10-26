package com.qolari.drivereplica.ui.map

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.LinearLayout
import android.widget.TextView
import androidx.core.widget.doAfterTextChanged
import androidx.fragment.app.FragmentManager
import androidx.lifecycle.lifecycleScope
import com.google.android.material.bottomsheet.BottomSheetDialogFragment
import com.qolari.drivereplica.R
import com.qolari.drivereplica.data.AppGraph
import com.qolari.drivereplica.databinding.SheetPlaceSearchBinding
import com.qolari.drivereplica.net.PlaceResult
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

/**
 * Pesquisa de locais do mapa (ícone da lupa).
 *
 * A lista local é o fallback imediato; o backend pesquisa no Google Geocoding e
 * devolve moradas reais. Escolher um ponto fecha a folha e move o mapa.
 */
class PlaceSearchSheet : BottomSheetDialogFragment() {

    private var _binding: SheetPlaceSearchBinding? = null
    private val binding get() = _binding!!

    private var onPick: ((name: String, lat: Double, lng: Double) -> Unit)? = null
    private var searchJob: Job? = null

    private data class Place(val name: String, val detail: String, val lat: Double, val lng: Double)

    private fun localPlaces(): List<Place> = listOf(
        Place(getString(R.string.place_casa), getString(R.string.place_casa_detail), 38.753, -9.145),
        Place(getString(R.string.place_airport), getString(R.string.place_airport_detail), 38.7742, -9.1342),
        Place(getString(R.string.place_pombal), getString(R.string.place_pombal_detail), 38.72553, -9.14997),
        Place(getString(R.string.place_rossio), getString(R.string.place_rossio_detail), 38.7139, -9.1394),
        Place(getString(R.string.place_cordoaria), getString(R.string.place_cordoaria_detail), 38.6979, -9.2032),
        Place(getString(R.string.place_oriente), getString(R.string.place_oriente_detail), 38.7679, -9.0993),
        Place(getString(R.string.place_luz), getString(R.string.place_luz_detail), 38.7527, -9.1848),
        Place(getString(R.string.place_alfama), getString(R.string.place_alfama_detail), 38.7116, -9.1300),
    )

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = SheetPlaceSearchBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        binding.placeClose.setOnClickListener { dismiss() }
        binding.placeQuery.doAfterTextChanged { query ->
            val text = query?.toString().orEmpty()
            render(text, localPlaces())
            searchRemote(text)
        }
        render("", localPlaces())
    }

    private fun searchRemote(raw: String) {
        searchJob?.cancel()
        val query = raw.trim()
        if (query.length < 2) return
        searchJob = viewLifecycleOwner.lifecycleScope.launch {
            delay(350)
            val fix = if (AppGraph.location.hasPermission) AppGraph.location.lastKnown() else null
            AppGraph.repository.searchPlaces(query, fix?.first, fix?.second)
                .onSuccess { results ->
                    if (results.isNotEmpty()) render(query, results.map { it.toPlace() }, filter = false)
                }
        }
    }

    private fun render(query: String, source: List<Place>, filter: Boolean = true) {
        val b = _binding ?: return
        val q = query.trim().lowercase()
        b.placeResults.removeAllViews()
        val matches = if (!filter) source else source.filter { p ->
            q.isEmpty() || p.name.lowercase().contains(q) || p.detail.lowercase().contains(q)
        }
        if (matches.isEmpty()) {
            b.placeResults.addView(
                TextView(requireContext()).apply {
                    setText(R.string.map_search_empty)
                    setTextColor(requireContext().getColor(R.color.qd_core_gray600))
                    textSize = 16f
                    setPadding(dp(20), dp(20), dp(20), dp(20))
                },
            )
            return
        }
        matches.forEach { p ->
            val row = LinearLayout(requireContext()).apply {
                orientation = LinearLayout.VERTICAL
                setPadding(dp(20), dp(14), dp(20), dp(14))
                setBackgroundResource(android.R.drawable.list_selector_background)
                isClickable = true
                setOnClickListener {
                    onPick?.invoke(p.name, p.lat, p.lng)
                    dismiss()
                }
            }
            row.addView(TextView(requireContext()).apply {
                text = p.name
                setTextColor(requireContext().getColor(R.color.qd_ink))
                textSize = 16f
            })
            row.addView(TextView(requireContext()).apply {
                text = p.detail
                setTextColor(requireContext().getColor(R.color.qd_core_gray600))
                textSize = 13f
                setPadding(0, dp(2), 0, 0)
            })
            b.placeResults.addView(row)
        }
    }

    private fun PlaceResult.toPlace(): Place {
        val detail = listOf(line1, line2).filter { it.isNotBlank() }.joinToString(", ")
        return Place(name.ifBlank { full }, detail.ifBlank { full }, lat, lng)
    }

    private fun dp(value: Int) = (value * resources.displayMetrics.density).toInt()

    override fun onDestroyView() {
        searchJob?.cancel()
        super.onDestroyView()
        _binding = null
    }

    companion object {
        fun show(manager: FragmentManager, onPick: (name: String, lat: Double, lng: Double) -> Unit) {
            PlaceSearchSheet().apply { this.onPick = onPick }.show(manager, "place_search")
        }
    }
}
