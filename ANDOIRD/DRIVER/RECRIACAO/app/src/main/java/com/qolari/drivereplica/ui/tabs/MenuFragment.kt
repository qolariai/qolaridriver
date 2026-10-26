package com.qolari.drivereplica.ui.tabs

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.annotation.DrawableRes
import androidx.annotation.StringRes
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import androidx.navigation.NavOptions
import com.qolari.drivereplica.data.AppGraph
import kotlinx.coroutines.launch
import androidx.navigation.fragment.findNavController
import com.qolari.drivereplica.R
import com.qolari.drivereplica.data.Fixtures
import com.qolari.drivereplica.databinding.FragmentMenuBinding
import com.qolari.drivereplica.databinding.ItemMenuRowBinding
import com.qolari.drivereplica.databinding.ItemMenuTileBinding

/**
 * Separador Menu (Views; capturas 013, 041, 064). As linhas só navegam onde o destino já existe neste lote:
 * Definições, Ajuda e Sobre. "Mudar de conta" e "Terminar sessão" terminam a sessão e voltam às boas-vindas.
 */
class MenuFragment : Fragment() {

    private var vehicleSubtitleView: android.widget.TextView? = null
    private var _binding: FragmentMenuBinding? = null
    private val binding get() = _binding!!

    private sealed interface Entry {
        data class Section(@StringRes val title: Int) : Entry
        data class Row(
            @DrawableRes val icon: Int?, @StringRes val title: Int, val subtitle: String? = null,
            val destination: Int? = null, val chevron: Boolean = true, @StringRes val info: Int? = null,
        ) : Entry
    }

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentMenuBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        val nav = findNavController()
        binding.profileName.text = Fixtures.DRIVER_NAME
        binding.profileRating.text = Fixtures.DRIVER_RATING
        binding.profileAcceptance.text = Fixtures.DRIVER_ACCEPTANCE
        // Perfil real do backend (`get-profile-hub`); sem rede ficam os valores de exemplo.
        viewLifecycleOwner.lifecycleScope.launch {
            AppGraph.repository.profile().getOrNull()?.let { p ->
                _binding?.let {
                    it.profileName.text = p.name.ifBlank { Fixtures.DRIVER_NAME }
                    it.profileRating.text = p.rating
                    it.profileAcceptance.text = p.acceptance
                }
                p.vehicle?.let { v -> vehicleSubtitleView?.text = v }
            }
        }

        bindTile(ItemMenuTileBinding.bind(binding.tileHelp.root), R.drawable.ic_help, R.string.menu_help) { nav.navigate(R.id.helpFragment) }
        bindTile(ItemMenuTileBinding.bind(binding.tileSafety.root), R.drawable.ic_shield, R.string.menu_safety) { com.qolari.drivereplica.ui.manage.SafetySheet.show(this) }
        bindTile(ItemMenuTileBinding.bind(binding.tileSettings.root), R.drawable.ic_gear, R.string.menu_settings) { nav.navigate(R.id.settingsFragment) }

        val entries = listOf(
            Entry.Section(R.string.menu_section_earn_more),
            Entry.Row(R.drawable.ic_compass, R.string.menu_discover_opportunities, destination = R.id.discoverFragment),
            Entry.Row(R.drawable.ic_half_circle, R.string.menu_pro, subtitle = getString(R.string.menu_tier_gold), destination = R.id.incentivesFragment),
            Entry.Row(R.drawable.ic_briefcase, R.string.menu_work_hub, info = R.string.info_work_body),
            Entry.Row(R.drawable.ic_gift, R.string.menu_referrals, destination = R.id.incentivesFragment),
            Entry.Section(R.string.menu_section_manage),
            Entry.Row(R.drawable.ic_car, R.string.menu_vehicles, subtitle = Fixtures.VEHICLE_SUMMARY, destination = R.id.vehiclesFragment),
            Entry.Row(R.drawable.ic_document, R.string.menu_documents, destination = R.id.documentsFragment),
            Entry.Row(R.drawable.ic_compass, R.string.menu_driving_prefs, destination = R.id.drivingPrefsFragment),
            Entry.Row(R.drawable.ic_compass, R.string.queue_title, destination = R.id.airportQueueFragment),
            Entry.Row(R.drawable.ic_briefcase, R.string.business_title, destination = R.id.businessProfileFragment),
            Entry.Row(R.drawable.ic_gear, R.string.appearance_title, destination = R.id.appearanceFragment),
            Entry.Row(R.drawable.ic_umbrella, R.string.menu_insurance, info = R.string.info_insurance_body),
            Entry.Section(R.string.menu_section_money),
            Entry.Row(R.drawable.ic_calculator, R.string.menu_tax_info, info = R.string.info_tax_body),
            Entry.Row(R.drawable.ic_wallet, R.string.menu_payment_methods, info = R.string.info_payments_body),
            Entry.Row(R.drawable.ic_help, R.string.support_title, destination = R.id.supportFragment),
            Entry.Section(R.string.menu_section_resources),
            Entry.Row(R.drawable.ic_info, R.string.menu_about, destination = R.id.aboutFragment),
        )
        val inflater = LayoutInflater.from(requireContext())
        val container = binding.menuContainer
        for (entry in entries) {
            when (entry) {
                is Entry.Section -> {
                    val tv = inflater.inflate(R.layout.item_section_title, container, false) as android.widget.TextView
                    tv.setText(entry.title)
                    container.addView(tv)
                }
                is Entry.Row -> {
                    val row = ItemMenuRowBinding.inflate(inflater, container, false)
                    entry.icon?.let { row.rowIcon.setImageResource(it) }
                    row.rowTitle.setText(entry.title)
                    if (entry.title == R.string.menu_vehicles) vehicleSubtitleView = row.rowSubtitle
                    if (entry.subtitle != null) {
                        row.rowSubtitle.text = entry.subtitle
                        row.rowSubtitle.visibility = View.VISIBLE
                    }
                    row.rowChevron.visibility = if (entry.chevron) View.VISIBLE else View.INVISIBLE
                    entry.destination?.let { dest -> row.rowContent.setOnClickListener { nav.navigate(dest) } }
                    entry.info?.let { body ->
                        row.rowContent.setOnClickListener {
                            nav.navigate(R.id.infoFragment, androidx.core.os.bundleOf(
                                com.qolari.drivereplica.ui.manage.InfoFragment.ARG_TITLE to getString(entry.title),
                                com.qolari.drivereplica.ui.manage.InfoFragment.ARG_BODY to getString(body)))
                        }
                    }
                    container.addView(row.root)
                }
            }
        }
        // Rodapé com a conta: sem ícones nem setas (captura 064_s2). Sem ação neste lote.
        container.addView(View(requireContext()).apply {
            layoutParams = ViewGroup.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, (8 * resources.displayMetrics.density).toInt())
            setBackgroundResource(R.color.qd_line)
        })
        listOf(R.string.menu_switch_account to null, R.string.menu_sign_out to Fixtures.ACCOUNT_EMAIL).forEach { (title, sub) ->
            val row = ItemMenuRowBinding.inflate(inflater, container, false)
            row.rowIcon.visibility = View.GONE
            (row.rowTitle.parent as ViewGroup).let { (it.layoutParams as ViewGroup.MarginLayoutParams).marginStart = 0 }
            row.rowTitle.setText(title)
            if (sub != null) { row.rowSubtitle.text = sub; row.rowSubtitle.visibility = View.VISIBLE }
            row.rowChevron.visibility = View.GONE
            // As duas linhas terminam a sessão local e voltam às boas-vindas (a original abre o seletor de contas).
            row.rowContent.setOnClickListener {
                viewLifecycleOwner.lifecycleScope.launch {
                    AppGraph.repository.signOut()
                    findNavController().navigate(R.id.welcomeFragment, null, NavOptions.Builder().setPopUpTo(R.id.nav_main, true).build())
                }
            }
            (row.rowDivider.layoutParams as ViewGroup.MarginLayoutParams).marginStart = (16 * resources.displayMetrics.density).toInt()
            container.addView(row.root)
        }
    }

    private fun bindTile(tile: ItemMenuTileBinding, @DrawableRes icon: Int, @StringRes label: Int, onClick: (() -> Unit)?) {
        tile.tileIcon.setImageResource(icon)
        tile.tileLabel.setText(label)
        if (onClick != null) tile.root.setOnClickListener { onClick() }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
