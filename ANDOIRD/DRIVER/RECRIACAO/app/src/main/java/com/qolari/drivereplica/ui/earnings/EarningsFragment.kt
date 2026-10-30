package com.qolari.drivereplica.ui.earnings

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.LinearLayout
import android.widget.TextView
import androidx.core.view.isVisible
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import com.qolari.drivereplica.R
import com.qolari.drivereplica.databinding.FragmentEarningsBinding
import com.qolari.drivereplica.databinding.ItemMenuRowBinding
import com.qolari.drivereplica.databinding.ItemRecentTripBinding
import com.qolari.drivereplica.databinding.ItemStatRowBinding
import kotlinx.coroutines.launch

/**
 * Separador Rendimentos (Views; capturas 011, 062, 122, 126). Resumo da semana, saldo e viagens recentes vêm do
 * backend; as secções de baixo (desafio, nível, mais formas de ganhar) são conteúdo de exemplo.
 */
class EarningsFragment : Fragment() {

    private var _binding: FragmentEarningsBinding? = null
    private val binding get() = _binding!!
    private val viewModel: EarningsViewModel by viewModels { EarningsViewModel.Factory }

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentEarningsBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        binding.swipe.setOnRefreshListener { viewModel.refresh() }
        // "Ver detalhes" abre o seletor "Abrir com" na original; aqui leva à lista de viagens da semana.
        binding.btnDetails.setOnClickListener { binding.scroll.smoothScrollTo(0, binding.recentTitle.top) }
        buildDayLabels()
        buildSections()
        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                viewModel.state.collect(::render)
            }
        }
    }

    private fun render(s: EarningsUiState) {
        binding.swipe.isRefreshing = s.refreshing && s.week != null
        val w = s.week
        binding.earningsError.isVisible = s.failed
        binding.earningsBody.isVisible = w != null
        if (w == null) return
        binding.weekPeriod.text = w.periodLabel
        binding.weekTotal.text = w.formattedTotal
        binding.weekChart.values = w.dayTotals
        // Gráfico da semana igual à captura 062: barras largas (~20dp) encostadas à direita, altura máxima 48dp.
        binding.weekChart.barWidthDp = 20f
        binding.weekChart.gapDp = 5f
        binding.weekChart.maxBarHeightDp = 48f
        binding.weekChart.highlight = w.todayIndex
        binding.weekChart.barColor = requireContext().getColor(R.color.qd_core_blue600)
        binding.weekChart.highlightColor = requireContext().getColor(R.color.qd_core_blue600)

        binding.statRows.removeAllViews()
        w.onlineLabel?.let { addStat(getString(R.string.menu_online_hours), it) }
        addStat(getString(R.string.earnings_trips), w.tripCount.toString())
        // "Pontos" existe na original (captura 062); derivamos 2 pontos por viagem concluída, como no programa Uber Pro.
        addStat(getString(R.string.earnings_points), (w.tripCount * 2).toString())
        binding.balanceRow.isVisible = w.balance != null
        binding.balanceValue.text = w.balance.orEmpty()

        binding.recentList.removeAllViews()
        w.recent.forEach { t ->
            val row = ItemRecentTripBinding.inflate(layoutInflater, binding.recentList, false)
            row.tripRoute.text = t.route
            row.tripTotal.text = t.total
            row.tripWhen.text = t.whenLabel
            binding.recentList.addView(row.root)
        }
        binding.recentEmpty.isVisible = w.recent.isEmpty()
    }

    private fun addStat(label: String, value: String) {
        if (binding.statRows.childCount > 0) {
            binding.statRows.addView(
                View(requireContext()).apply {
                    layoutParams = LinearLayout.LayoutParams(
                        ViewGroup.LayoutParams.MATCH_PARENT,
                        (2 * resources.displayMetrics.density).toInt(),
                    )
                    setBackgroundResource(R.drawable.qd_dashed_divider)
                },
            )
        }
        val row = ItemStatRowBinding.inflate(layoutInflater, binding.statRows, false)
        row.statLabel.text = label
        row.statValue.text = value
        binding.statRows.addView(row.root)
    }

    private fun buildDayLabels() {
        EarningsMapper.DAY_LABELS.forEach { d ->
            binding.weekDayLabels.addView(
                TextView(requireContext()).apply {
                    text = d.take(3)
                    textSize = 11f
                    maxLines = 1
                    setSingleLine(true)
                    includeFontPadding = false
                    gravity = android.view.Gravity.CENTER
                    setTextColor(requireContext().getColor(R.color.qd_core_gray600))
                    layoutParams = LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f)
                }
            )
        }
    }

    private fun buildSections() {
        val c = binding.earningsSections
        fun title(@androidx.annotation.StringRes t: Int, size: Float = 20f) = TextView(requireContext()).apply {
            setText(t); textSize = size
            setTypeface(typeface, android.graphics.Typeface.BOLD)
            setTextColor(requireContext().getColor(R.color.qd_ink))
            setPadding(dp(16), dp(24), dp(16), dp(4))
        }
        fun body(@androidx.annotation.StringRes t: Int) = TextView(requireContext()).apply {
            setText(t); textSize = 14f
            setTextColor(requireContext().getColor(R.color.qd_core_gray600))
            setPadding(dp(16), 0, dp(16), dp(8))
        }
        c.addView(title(R.string.earnings_challenge))
        c.addView(body(R.string.earnings_challenge_sub))
        c.addView(title(R.string.earnings_tier))
        c.addView(body(R.string.earnings_tier_sub))
        c.addView(TextView(requireContext()).apply {
            setText(R.string.earnings_tier_goal); textSize = 16f
            setTextColor(requireContext().getColor(R.color.qd_ink))
            setPadding(dp(16), dp(12), dp(16), dp(8))
        })
        // Barra de progresso: 45% do caminho até ao nível seguinte (valor de exemplo).
        c.addView(LinearLayout(requireContext()).apply {
            orientation = LinearLayout.HORIZONTAL
            setPadding(dp(16), 0, dp(16), dp(8))
            addView(View(requireContext()).apply {
                setBackgroundColor(requireContext().getColor(R.color.qd_core_yellow300))
                layoutParams = LinearLayout.LayoutParams(0, dp(24), 45f)
            })
            addView(View(requireContext()).apply {
                setBackgroundColor(requireContext().getColor(R.color.qd_core_gray200))
                layoutParams = LinearLayout.LayoutParams(0, dp(24), 55f)
            })
        })
        c.addView(title(R.string.menu_section_earn_more))
        listOf(
            Triple(R.drawable.ic_navigate_ne, R.string.menu_discover_opportunities, R.string.earnings_row_discover_sub),
            Triple(R.drawable.ic_gift, R.string.earnings_row_refer, R.string.earnings_row_refer_sub),
        ).forEach { (icon, t, sub) ->
            val row = ItemMenuRowBinding.inflate(layoutInflater, c, false)
            row.rowIcon.setImageResource(icon)
            row.rowTitle.setText(t)
            row.rowSubtitle.setText(sub)
            row.rowSubtitle.visibility = View.VISIBLE
            c.addView(row.root)
        }
    }

    private fun dp(v: Int) = (v * resources.displayMetrics.density).toInt()

    override fun onDestroyView() {
        _binding = null
        super.onDestroyView()
    }
}
