package com.qolari.drivereplica.ui.earnings

import android.content.Intent
import android.os.Bundle
import android.text.InputType
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.TextView
import androidx.core.view.isVisible
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import androidx.navigation.fragment.findNavController
import com.google.android.material.button.MaterialButton
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import com.qolari.drivereplica.R
import com.qolari.drivereplica.data.AppGraph
import com.qolari.drivereplica.databinding.FragmentIncentivesBinding
import com.qolari.drivereplica.net.IncentivesResponse
import com.qolari.drivereplica.net.QuestDto
import kotlinx.coroutines.launch

/** Missoes, pontos/Pro e referral. */
class IncentivesFragment : Fragment() {

    private var _binding: FragmentIncentivesBinding? = null
    private val binding get() = _binding!!

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentIncentivesBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        binding.incentivesBack.setOnClickListener { findNavController().popBackStack() }
        binding.incentivesShare.setOnClickListener { shareCode() }
        binding.incentivesInvite.setOnClickListener { invite() }
        load()
    }

    private fun load() {
        lifecycleScope.launch {
            AppGraph.repository.incentives()
                .onSuccess { render(it) }
                .onFailure { error() }
        }
    }

    private fun render(x: IncentivesResponse) {
        binding.incentivesError.isVisible = false
        binding.incentivesPoints.text = getString(R.string.incentives_points, x.points)
        binding.incentivesTier.text = if (x.nextTierPoints != null) {
            getString(R.string.incentives_tier_next, x.tier, x.nextTierPoints)
        } else {
            getString(R.string.incentives_tier_max, x.tier)
        }
        binding.incentivesQuests.removeAllViews()
        if (x.quests.isEmpty()) {
            binding.incentivesQuests.addView(text(getString(R.string.incentives_no_quests)))
        }
        x.quests.forEach { q -> binding.incentivesQuests.addView(questRow(q)) }
        binding.incentivesCode.text = x.referral.code
        binding.incentivesReferralDetail.text =
            getString(R.string.incentives_referral_detail, x.referral.invited, x.referral.pending, x.referral.reward)
    }

    private fun questRow(q: QuestDto): View {
        val box = LinearLayout(requireContext()).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(0, dp(10), 0, dp(10))
        }
        box.addView(text(q.title).apply { textSize = 16f; setTypeface(typeface, android.graphics.Typeface.BOLD) })
        box.addView(text(q.description).apply { textSize = 14f })
        box.addView(text(getString(R.string.incentives_progress, q.progress, q.target, q.reward)).apply { textSize = 14f })
        if (q.claimed) {
            box.addView(text(getString(R.string.incentives_claimed)).apply {
                setTextColor(requireContext().getColor(R.color.qd_core_green600))
                textSize = 14f
            })
        } else if (q.canClaim) {
            box.addView(MaterialButton(requireContext()).apply {
                setText(R.string.incentives_claim)
                setOnClickListener { claim(q.uuid) }
            })
        }
        return box
    }

    private fun claim(uuid: String) {
        lifecycleScope.launch {
            AppGraph.repository.claimQuest(uuid)
                .onSuccess { render(it) }
                .onFailure { error() }
        }
    }

    private fun shareCode() {
        val code = binding.incentivesCode.text.toString()
        val intent = Intent(Intent.ACTION_SEND).apply {
            type = "text/plain"
            putExtra(Intent.EXTRA_TEXT, getString(R.string.incentives_share_text, code))
        }
        startActivity(Intent.createChooser(intent, getString(R.string.incentives_share)))
    }

    private fun invite() {
        val input = EditText(requireContext()).apply {
            hint = getString(R.string.incentives_phone)
            inputType = InputType.TYPE_CLASS_PHONE
            setPadding(dp(20), dp(8), dp(20), dp(8))
        }
        MaterialAlertDialogBuilder(requireContext())
            .setTitle(R.string.incentives_invite)
            .setView(input)
            .setPositiveButton(R.string.incentives_send) { _, _ ->
                val phone = input.text.toString().trim()
                if (phone.length >= 6) {
                    lifecycleScope.launch {
                        AppGraph.repository.inviteDriver(phone)
                            .onSuccess { render(it) }
                            .onFailure { error() }
                    }
                }
            }
            .setNegativeButton(R.string.safety_cancel, null)
            .show()
    }

    private fun text(value: String) = TextView(requireContext()).apply {
        text = value
        setTextColor(requireContext().getColor(R.color.qd_core_gray600))
        textSize = 14f
    }

    private fun error() {
        binding.incentivesError.isVisible = true
        binding.incentivesError.setText(R.string.incentives_error)
    }

    private fun dp(value: Int) = (value * resources.displayMetrics.density).toInt()

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
