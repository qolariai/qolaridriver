package com.qolari.drivereplica.ui.manage

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.core.os.bundleOf
import androidx.core.view.isVisible
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import androidx.lifecycle.viewModelScope
import androidx.navigation.fragment.NavHostFragment
import androidx.navigation.fragment.findNavController
import com.google.android.material.bottomsheet.BottomSheetDialogFragment
import com.qolari.drivereplica.R
import com.qolari.drivereplica.data.AppGraph
import com.qolari.drivereplica.databinding.FragmentSimpleListBinding
import com.qolari.drivereplica.databinding.ItemSimpleRowBinding
import com.qolari.drivereplica.databinding.ItemSimpleSectionBinding
import com.qolari.drivereplica.databinding.SheetSafetyBinding
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

/** Carrega uma lista do servidor: A carregar -> dados, ou falha ("Sem ligação de rede", como em Rendimentos, captura 122). */
sealed interface LoadState<out T> {
    data object Loading : LoadState<Nothing>
    data class Data<T>(val value: T) : LoadState<T>
    data object Failed : LoadState<Nothing>
}

class LoadViewModel<T>(private val loader: suspend () -> Result<T>) : ViewModel() {
    private val _state = MutableStateFlow<LoadState<T>>(LoadState.Loading)
    val state: StateFlow<LoadState<T>> = _state.asStateFlow()

    init { reload() }

    fun reload() {
        viewModelScope.launch {
            loader().onSuccess { _state.value = LoadState.Data(it) }.onFailure {
                // Com dados já mostrados mantém-nos (como Rendimentos); sem dados mostra a falha.
                if (_state.value !is LoadState.Data) _state.value = LoadState.Failed
            }
        }
    }
}

fun <T> loadFactory(loader: suspend () -> Result<T>) = object : ViewModelProvider.Factory {
    @Suppress("UNCHECKED_CAST")
    override fun <V : ViewModel> create(modelClass: Class<V>): V = LoadViewModel(loader) as V
}

/** Base dos ecrãs de lista simples: seta, título, texto e linhas. */
abstract class SimpleListFragment : Fragment() {
    private var _b: FragmentSimpleListBinding? = null
    protected val b get() = _b!!

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _b = FragmentSimpleListBinding.inflate(inflater, container, false)
        b.listBack.setOnClickListener { findNavController().popBackStack() }
        return b.root
    }

    protected fun row(title: String, subtitle: String? = null, status: String? = null, statusColor: Int? = null, onClick: (() -> Unit)? = null): View {
        val r = ItemSimpleRowBinding.inflate(layoutInflater, b.listRows, false)
        r.simpleRowTitle.text = title
        r.simpleRowSubtitle.text = subtitle
        r.simpleRowSubtitle.isVisible = !subtitle.isNullOrBlank()
        r.simpleRowStatus.text = status
        r.simpleRowStatus.isVisible = !status.isNullOrBlank()
        statusColor?.let { r.simpleRowStatus.setTextColor(requireContext().getColor(it)) }
        r.simpleRowChevron.isVisible = onClick != null
        onClick?.let { r.simpleRowContent.setOnClickListener { _ -> it() } }
        return r.root
    }

    protected fun section(text: String): View =
        ItemSimpleSectionBinding.inflate(layoutInflater, b.listRows, false).also { (it.root as TextView).text = text }.root

    protected fun openInfo(title: String, body: String) =
        findNavController().navigate(R.id.infoFragment, bundleOf(InfoFragment.ARG_TITLE to title, InfoFragment.ARG_BODY to body))

    override fun onDestroyView() {
        _b = null
        super.onDestroyView()
    }
}

/** Página informativa de texto (Seguro, Pagamentos, Informações fiscais, detalhe de segurança). Conteúdo próprio (D7). */
class InfoFragment : SimpleListFragment() {
    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        b.listHeading.text = requireArguments().getString(ARG_TITLE)
        b.listIntro.text = requireArguments().getString(ARG_BODY)
        b.listIntro.isVisible = true
    }

    companion object {
        const val ARG_TITLE = "title"
        const val ARG_BODY = "body"
    }
}

/** Veículo (captura 080) e "Os seus veículos" (captura 082), com dados do backend (`/rt/drivers/v2/vehicles`). */
class VehiclesFragment : SimpleListFragment() {
    private val vm: LoadViewModel<List<VehicleItem>> by viewModels { loadFactory { AppGraph.repository.vehicles() } }
    private val manage get() = arguments?.getBoolean(ARG_MANAGE) == true

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        b.listBarTitle.text = if (manage) "" else getString(R.string.vehicles_title)
        b.listHeading.text = if (manage) getString(R.string.vehicles_yours) else ""
        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) { vm.state.collect(::render) }
        }
    }

    private fun render(s: LoadState<List<VehicleItem>>) {
        b.listRows.removeAllViews()
        b.listState.isVisible = s !is LoadState.Data
        b.listState.setText(if (s is LoadState.Failed) R.string.earnings_no_network else R.string.loading)
        b.listButton.isVisible = false
        val list = (s as? LoadState.Data)?.value ?: return
        if (list.isEmpty()) {
            b.listState.isVisible = true
            b.listState.setText(R.string.vehicles_none)
            return
        }
        if (manage) {
            list.forEach { v -> b.listRows.addView(row(v.title, v.plate)) }
        } else {
            val v = list.firstOrNull { it.isDefault } ?: list.first()
            b.listHeading.text = v.title
            b.listIntro.text = v.plate
            b.listIntro.isVisible = true
            b.listButton.setText(R.string.vehicles_manage)
            b.listButton.isVisible = true
            b.listButton.setOnClickListener { findNavController().navigate(R.id.vehiclesManageFragment, bundleOf(ARG_MANAGE to true)) }
        }
    }

    companion object { const val ARG_MANAGE = "manage" }
}

/** Documentos do motorista (captura 083): estado de cada um; o backend só indica os pendentes. */
class DocumentsFragment : SimpleListFragment() {
    private val vm: LoadViewModel<List<DocumentItem>> by viewModels { loadFactory { AppGraph.repository.documents() } }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        b.listBarTitle.text = getString(R.string.menu_documents)
        b.listHeading.setText(R.string.docs_requirements)
        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) { vm.state.collect(::render) }
        }
    }

    private fun render(s: LoadState<List<DocumentItem>>) {
        b.listRows.removeAllViews()
        b.listState.isVisible = s !is LoadState.Data
        b.listState.setText(if (s is LoadState.Failed) R.string.earnings_no_network else R.string.loading)
        val items = (s as? LoadState.Data)?.value ?: return
        items.forEach { d ->
            val (label, color) = when (d.status) {
                DocStatus.APPROVED -> R.string.docs_done to R.color.qd_core_green600
                DocStatus.PENDING -> R.string.docs_pending to R.color.qd_core_gray600
                DocStatus.REJECTED -> R.string.docs_rejected to R.color.qd_core_red600
            }
            val expiry = ManageMapper.expiry(d.expiresOn)?.let { getString(R.string.docs_expires, it) }
            val status = listOfNotNull(getString(label), expiry).joinToString(" · ")
            val detail = when (d.status) {
                DocStatus.APPROVED -> getString(R.string.docs_detail_done)
                DocStatus.PENDING -> getString(R.string.docs_detail_pending)
                DocStatus.REJECTED -> listOf(getString(R.string.docs_detail_rejected), d.note).filter { it.isNotBlank() }.joinToString("\n\n")
            }
            b.listRows.addView(row(d.title, status = status, statusColor = color) { openInfo(d.title, detail) })
        }
    }
}

/** Centro de segurança (capturas 017, 018, 024): secções com texto e linhas. Conteúdo próprio (D7). */
class SafetyCenterFragment : SimpleListFragment() {
    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        b.listHeading.setText(R.string.safety_center_title)
        SafetyContent.sections.forEach { (title, rows) ->
            b.listRows.addView(section(title))
            rows.forEach { r -> b.listRows.addView(row(r.title, r.subtitle) { openInfo(r.title, r.subtitle) }) }
        }
    }
}

/** Conjunto de Ferramentas de Segurança em folha inferior (captura 014), aberto pelo escudo e pelo Menu. */
class SafetySheet : BottomSheetDialogFragment() {
    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        val b = SheetSafetyBinding.inflate(inflater, container, false)
        b.safetyClose.setOnClickListener { dismiss() }
        val nav = NavHostFragment.findNavController(requireParentFragment())
        SafetyContent.tools.forEach { t ->
            val r = ItemSimpleRowBinding.inflate(inflater, b.safetyRows, false)
            r.simpleRowTitle.text = t.title
            r.simpleRowSubtitle.text = t.subtitle
            r.simpleRowSubtitle.isVisible = true
            r.simpleRowContent.setOnClickListener {
                dismiss()
                if (t.title == "Centro de segurança") nav.navigate(R.id.safetyCenterFragment)
                else nav.navigate(R.id.infoFragment, bundleOf(InfoFragment.ARG_TITLE to t.title, InfoFragment.ARG_BODY to t.subtitle))
            }
            b.safetyRows.addView(r.root)
        }
        return b.root
    }

    companion object {
        fun show(fragment: Fragment) = SafetySheet().show(fragment.childFragmentManager, "safety")
    }
}
