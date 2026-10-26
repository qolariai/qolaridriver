package com.qolari.drivereplica.ui.help

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.annotation.DrawableRes
import androidx.annotation.StringRes
import androidx.core.os.bundleOf
import androidx.fragment.app.Fragment
import androidx.navigation.fragment.findNavController
import androidx.recyclerview.widget.GridLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.qolari.drivereplica.R
import com.qolari.drivereplica.databinding.FragmentHelpBinding
import com.qolari.drivereplica.databinding.ItemHelpCategoryBinding
import com.qolari.drivereplica.ui.manage.InfoFragment

/**
 * Ajuda (Views; capturas 042 e 090): cabeçalho com título grande e grelha de 3 colunas com as categorias.
 * Cada categoria abre uma página de conteúdo próprio (D7: não é o conteúdo web do original).
 */
class HelpFragment : Fragment() {

    private var _binding: FragmentHelpBinding? = null
    private val binding get() = _binding!!

    private data class Category(
        @DrawableRes val icon: Int,
        @StringRes val label: Int,
        @StringRes val body: Int,
    )

    private val categories = listOf(
        Category(R.drawable.ic_route, R.string.help_cat_trip, R.string.help_body_trip),
        Category(R.drawable.ic_person, R.string.help_cat_account, R.string.help_body_account),
        Category(R.drawable.ic_wallet, R.string.help_cat_earnings, R.string.help_body_earnings),
        Category(R.drawable.ic_car, R.string.help_cat_evs, R.string.help_body_evs),
        Category(R.drawable.ic_fleet, R.string.help_cat_fleet, R.string.help_body_fleet),
        Category(R.drawable.ic_book, R.string.help_cat_guides, R.string.help_body_guides),
        Category(R.drawable.ic_box, R.string.help_cat_delivery, R.string.help_body_delivery),
        Category(R.drawable.ic_shield, R.string.help_cat_safety, R.string.help_body_safety),
        Category(R.drawable.ic_calendar, R.string.help_cat_appointment, R.string.help_body_appointment),
        Category(R.drawable.ic_accessibility, R.string.help_cat_accessibility, R.string.help_body_accessibility),
        Category(R.drawable.ic_document, R.string.help_cat_legal, R.string.help_body_legal),
        Category(R.drawable.ic_lock, R.string.help_cat_privacy, R.string.help_body_privacy),
        Category(R.drawable.ic_folder, R.string.help_cat_diagnostics, R.string.help_body_diagnostics),
        Category(R.drawable.ic_pin_plus, R.string.help_cat_map, R.string.help_body_map),
    )

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentHelpBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        val nav = findNavController()
        binding.helpBack.setOnClickListener { nav.popBackStack() }
        // "Caixa de entrada" salta para o separador respetivo (a pílula da captura 042).
        binding.helpInboxPill.setOnClickListener { nav.navigate(R.id.inboxFragment) }

        val layout = GridLayoutManager(requireContext(), SPANS)
        layout.spanSizeLookup = object : GridLayoutManager.SpanSizeLookup() {
            override fun getSpanSize(position: Int) = if (position < HEADERS) SPANS else 1
        }
        binding.helpGrid.layoutManager = layout
        binding.helpGrid.adapter = Adapter()
    }

    private inner class Adapter : RecyclerView.Adapter<RecyclerView.ViewHolder>() {
        override fun getItemCount() = HEADERS + categories.size
        override fun getItemViewType(position: Int) = if (position < HEADERS) 0 else 1

        override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): RecyclerView.ViewHolder {
            val inflater = LayoutInflater.from(parent.context)
            return if (viewType == 0) {
                object : RecyclerView.ViewHolder(inflater.inflate(R.layout.item_section_title, parent, false)) {}
            } else {
                CategoryHolder(ItemHelpCategoryBinding.inflate(inflater, parent, false))
            }
        }

        override fun onBindViewHolder(holder: RecyclerView.ViewHolder, position: Int) {
            if (holder is CategoryHolder) {
                val c = categories[position - HEADERS]
                holder.b.catIcon.setImageResource(c.icon)
                holder.b.catLabel.setText(c.label)
                holder.b.root.setOnClickListener {
                    findNavController().navigate(
                        R.id.infoFragment,
                        bundleOf(
                            InfoFragment.ARG_TITLE to getString(c.label),
                            InfoFragment.ARG_BODY to getString(c.body),
                        ),
                    )
                }
            } else {
                val tv = holder.itemView as TextView
                if (position == 0) {
                    tv.setText(R.string.help_title); tv.textSize = 40f
                } else {
                    tv.setText(R.string.help_all_categories); tv.textSize = 24f
                }
            }
        }
    }

    private class CategoryHolder(val b: ItemHelpCategoryBinding) : RecyclerView.ViewHolder(b.root)

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }

    private companion object {
        const val SPANS = 3
        const val HEADERS = 2
    }
}
