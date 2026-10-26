package com.qolari.userlite.ui.ride

import android.app.DatePickerDialog
import android.app.TimePickerDialog
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.TextView
import androidx.core.view.isVisible
import androidx.fragment.app.Fragment
import androidx.fragment.app.activityViewModels
import androidx.fragment.app.viewModels
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import androidx.navigation.fragment.findNavController
import androidx.recyclerview.widget.LinearLayoutManager
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import com.google.android.material.snackbar.Snackbar
import com.qolari.userlite.R
import com.qolari.userlite.data.AppGraph
import com.qolari.userlite.databinding.FragmentRideOptionsBinding
import com.qolari.userlite.net.QuoteProduct
import com.qolari.userlite.net.RoutePoint
import kotlinx.coroutines.launch
import java.text.DateFormat
import java.util.Calendar
import java.util.Date

/** Escolha da viagem (captura 032): mapa com rota, categorias com preço, pagamento e pedido. */
class RideOptionsFragment : Fragment() {

    private var _binding: FragmentRideOptionsBinding? = null
    private val binding get() = _binding!!
    private val ride: RideViewModel by activityViewModels()
    private val viewModel: RideOptionsViewModel by viewModels()
    private lateinit var adapter: RideProductAdapter
    private var scheduledAt: Long? = null

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentRideOptionsBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        val pickup = ride.pickup.value
        val dropoff = ride.dropoff.value
        if (dropoff == null) {
            findNavController().navigateUp()
            return
        }

        adapter = RideProductAdapter { product -> choose(product) }
        binding.products.layoutManager = LinearLayoutManager(requireContext())
        binding.products.adapter = adapter
        binding.map.route = listOf(pickup.lat to pickup.lng, dropoff.lat to dropoff.lng)
        binding.map.showUser = false
        viewLifecycleOwner.lifecycleScope.launch {
            AppGraph.repository.route(pickup, dropoff).onSuccess { points ->
                if (points.size >= 2) _binding?.map?.route = points
            }
        }
        binding.routeLabel.text = getString(R.string.trip_dropoff) + ": " + dropoff.address
        binding.backButton.setOnClickListener { findNavController().navigateUp() }
        binding.paymentRow.setOnClickListener { choosePayment() }
        binding.scheduleRow.setOnClickListener { chooseSchedule() }
        binding.addStopRow.setOnClickListener { addStop() }
        binding.requestButton.setOnClickListener {
            viewModel.request(pickup, dropoff, ride.promoCode, scheduledAt, ride.stops.value)
        }
        binding.error.setOnClickListener { load(pickup, dropoff) }

        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                viewModel.state.collect { state ->
                    binding.loading.isVisible = state.loading
                    binding.products.isVisible = !state.loading && state.error == null
                    binding.error.isVisible = state.error != null
                    binding.error.text = state.error
                    binding.paymentLabel.text = getString(R.string.ride_payment, state.payment.label)
                    state.quote?.let { quote ->
                        adapter.submit(quote.products, state.selected)
                        binding.requestButton.isVisible = quote.products.isNotEmpty()
                    }
                    state.selected?.let { product ->
                        binding.requestButton.text = getString(R.string.ride_request, product.name)
                    }
                    binding.requestButton.isEnabled = !state.requesting && state.selected != null
                    if (state.requesting) binding.requestButton.text = getString(R.string.loading)
                    if (state.requestError != null) {
                        Snackbar.make(binding.root, state.requestError, Snackbar.LENGTH_LONG).show()
                    }
                    if (state.trip != null) {
                        ride.select(state.selected!!)
                        ride.promoCode = null
                        findNavController().navigate(R.id.action_ride_to_active)
                    }
                }
            }
        }

        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                ride.stops.collect { renderStops(it) }
            }
        }

        load(pickup, dropoff)
    }

    private fun load(pickup: RoutePoint, dropoff: RoutePoint) {
        viewModel.load(pickup, dropoff)
    }

    private fun choose(product: QuoteProduct) {
        viewModel.select(product)
        ride.select(product)
    }

    private fun choosePayment() {
        val labels = arrayOf("Dinheiro", "Cartão •••• 4242")
        val ids = arrayOf("cash", "card")
        val current = viewModel.state.value.payment.id
        val checked = ids.indexOf(current).coerceAtLeast(0)
        MaterialAlertDialogBuilder(requireContext())
            .setTitle(R.string.ride_payment_add)
            .setSingleChoiceItems(labels, checked) { dialog, which ->
                viewModel.selectPayment(ids[which])
                dialog.dismiss()
            }
            .setNegativeButton(R.string.error_cancel, null)
            .show()
    }

    private fun chooseSchedule() {
        val base = Calendar.getInstance()
        scheduledAt?.let { base.timeInMillis = it } ?: run {
            base.add(Calendar.HOUR_OF_DAY, 1)
            base.set(Calendar.MINUTE, 0)
        }
        DatePickerDialog(requireContext(), { _, year, month, day ->
            val chosen = Calendar.getInstance().apply {
                set(Calendar.YEAR, year)
                set(Calendar.MONTH, month)
                set(Calendar.DAY_OF_MONTH, day)
                set(Calendar.HOUR_OF_DAY, base.get(Calendar.HOUR_OF_DAY))
                set(Calendar.MINUTE, base.get(Calendar.MINUTE))
                set(Calendar.SECOND, 0)
                set(Calendar.MILLISECOND, 0)
            }
            TimePickerDialog(requireContext(), { _, hour, minute ->
                chosen.set(Calendar.HOUR_OF_DAY, hour)
                chosen.set(Calendar.MINUTE, minute)
                if (chosen.timeInMillis < System.currentTimeMillis() + 5 * 60 * 1000) {
                    Snackbar.make(binding.root, R.string.ride_schedule_too_soon, Snackbar.LENGTH_LONG).show()
                } else {
                    scheduledAt = chosen.timeInMillis
                    val label = DateFormat.getDateTimeInstance(DateFormat.SHORT, DateFormat.SHORT)
                        .format(Date(chosen.timeInMillis))
                    binding.scheduleLabel.text = getString(R.string.ride_schedule_for, label)
                }
            }, base.get(Calendar.HOUR_OF_DAY), base.get(Calendar.MINUTE), true).show()
        }, base.get(Calendar.YEAR), base.get(Calendar.MONTH), base.get(Calendar.DAY_OF_MONTH)).apply {
            datePicker.minDate = System.currentTimeMillis()
        }.show()
    }

    private fun addStop() {
        if (ride.stops.value.size >= 3) {
            Snackbar.make(binding.root, R.string.ride_stops_limit, Snackbar.LENGTH_SHORT).show()
            return
        }
        val input = EditText(requireContext()).apply {
            hint = getString(R.string.ride_stop_hint)
            setPadding(dp(20), dp(8), dp(20), dp(8))
        }
        MaterialAlertDialogBuilder(requireContext())
            .setTitle(R.string.ride_add_stop)
            .setView(input)
            .setPositiveButton(R.string.ride_stop_add) { _, _ ->
                val query = input.text.toString().trim()
                if (query.isEmpty()) return@setPositiveButton
                lifecycleScope.launch {
                    AppGraph.repository.places(query)
                        .onSuccess { places ->
                            val p = places.firstOrNull()
                            if (p == null) {
                                Snackbar.make(binding.root, R.string.ride_stop_not_found, Snackbar.LENGTH_SHORT).show()
                            } else {
                                ride.addStop(RoutePoint(p.lat, p.lng, p.address.ifBlank { p.name }))
                            }
                        }
                        .onFailure {
                            Snackbar.make(binding.root, R.string.ride_stop_not_found, Snackbar.LENGTH_SHORT).show()
                        }
                }
            }
            .setNegativeButton(R.string.error_cancel, null)
            .show()
    }

    private fun renderStops(stops: List<RoutePoint>) {
        binding.stopsList.removeAllViews()
        stops.forEachIndexed { index, stop ->
            val row = LinearLayout(requireContext()).apply {
                orientation = LinearLayout.HORIZONTAL
                gravity = android.view.Gravity.CENTER_VERTICAL
                setPadding(0, dp(6), 0, dp(6))
            }
            row.addView(TextView(requireContext()).apply {
                text = getString(R.string.ride_stop_row, index + 1, stop.address)
                setTextColor(requireContext().getColor(R.color.ql_black))
                textSize = 14f
                layoutParams = LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f)
            })
            row.addView(TextView(requireContext()).apply {
                setText(R.string.saved_remove)
                setTextColor(requireContext().getColor(R.color.ql_red))
                textSize = 14f
                setPadding(dp(8), dp(4), 0, dp(4))
                setOnClickListener { ride.removeStop(index) }
            })
            binding.stopsList.addView(row)
        }
    }

    private fun dp(value: Int) = (value * resources.displayMetrics.density).toInt()

    override fun onResume() {
        super.onResume()
        _binding?.map?.onResume()
    }

    override fun onPause() {
        _binding?.map?.onPause()
        super.onPause()
    }

    override fun onDestroyView() {
        _binding?.map?.onDestroy()
        super.onDestroyView()
        _binding = null
    }
}
