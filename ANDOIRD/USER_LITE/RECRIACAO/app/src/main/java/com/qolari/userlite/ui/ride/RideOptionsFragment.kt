package com.qolari.userlite.ui.ride

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
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
import com.qolari.userlite.ui.map.DirectionsClient
import kotlinx.coroutines.launch

/** Escolha da viagem (captura 032): mapa com rota, categorias com preço, pagamento e pedido. */
class RideOptionsFragment : Fragment() {

    private var _binding: FragmentRideOptionsBinding? = null
    private val binding get() = _binding!!
    private val ride: RideViewModel by activityViewModels()
    private val viewModel: RideOptionsViewModel by viewModels()
    private lateinit var adapter: RideProductAdapter

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
        DirectionsClient.fetch(requireContext(), pickup.lat, pickup.lng, dropoff.lat, dropoff.lng) { pts ->
            if (_binding != null && pts.size > 1) binding.map.route = pts
        }
        binding.map.showUser = false
        binding.map.dropoff = dropoff.lat to dropoff.lng
        binding.routeLabel.text = getString(R.string.ride_to, dropoff.address)
        binding.pickupLabel.text = getString(R.string.ride_from, pickup.address)
        binding.backButton.setOnClickListener { findNavController().navigateUp() }
        binding.zoomIn.setOnClickListener { binding.map.zoomIn() }
        binding.zoomOut.setOnClickListener { binding.map.zoomOut() }
        binding.paymentRow.setOnClickListener { choosePayment() }
        binding.requestButton.setOnClickListener {
            // Sem rede não há pedido: evita orçamentos antigos e o erro feio do socket.
            if (!AppGraph.network.connected.value) {
                Snackbar.make(binding.root, R.string.ride_offline, Snackbar.LENGTH_LONG).show()
                return@setOnClickListener
            }
            viewModel.request(pickup, dropoff, ride.promoCode)
        }
        binding.error.setOnClickListener { load(pickup, dropoff) }
        binding.whenChip.setOnClickListener { chooseWhen() }
        binding.forChip.setOnClickListener { chooseForWhom() }

        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                viewModel.state.collect { state ->
                    binding.loading.isVisible = state.loading
                    binding.products.isVisible = !state.loading && state.error == null
                    binding.error.isVisible = state.error != null
                    binding.error.text = state.error
                    binding.paymentLabel.text = getString(R.string.ride_payment, state.payment.label)
                    // Folha "A pedir a sua viagem" com o conteúdo por trás esbatido (original).
                    binding.requestingScrim.isVisible = state.requesting
                    binding.requestingOverlay.isVisible = state.requesting
                    state.quote?.let { quote ->
                        adapter.submit(quote.products, state.selected)
                        binding.requestButton.isVisible = quote.products.isNotEmpty()
                    }
                    state.selected?.let { product ->
                        binding.requestButton.text = getString(R.string.ride_request, product.name)
                        // O ETA do mapa é o do produto escolhido, não um "3 min." fixo.
                        binding.pickupEta.text = getString(R.string.ride_eta, product.etaMin)
                        binding.pickupEta.isVisible = product.etaMin > 0
                    }
                    binding.requestButton.isEnabled = !state.requesting && state.selected != null
                    if (state.requesting) binding.requestButton.text = getString(R.string.loading)
                    if (state.requestError != null) {
                        Snackbar.make(binding.root, state.requestError, Snackbar.LENGTH_LONG).show()
                    }
                    if (state.trip != null) {
                        ride.select(state.selected!!)
                        ride.promoCode = null
                        ride.reopenTrip()
                        findNavController().navigate(R.id.action_ride_to_active)
                    }
                }
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

    private fun chooseWhen() {
        val labels = arrayOf(getString(R.string.ride_when_now), getString(R.string.ride_when_later))
        MaterialAlertDialogBuilder(requireContext())
            .setTitle(R.string.search_when)
            .setItems(labels) { _, which ->
                if (which == 1) {
                    Snackbar.make(binding.root, R.string.ride_schedule_soon, Snackbar.LENGTH_SHORT).show()
                }
            }
            .show()
    }

    private fun chooseForWhom() {
        val labels = arrayOf(getString(R.string.ride_for_me), getString(R.string.ride_for_other))
        MaterialAlertDialogBuilder(requireContext())
            .setTitle(R.string.search_for)
            .setItems(labels) { _, which ->
                if (which == 1) {
                    Snackbar.make(binding.root, R.string.ride_for_other_soon, Snackbar.LENGTH_SHORT).show()
                }
            }
            .show()
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

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
