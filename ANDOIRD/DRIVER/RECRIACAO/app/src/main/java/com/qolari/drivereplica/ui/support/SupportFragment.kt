package com.qolari.drivereplica.ui.support

import android.app.Activity
import android.content.Intent
import android.media.projection.MediaProjectionManager
import android.net.Uri
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.LinearLayout
import android.widget.TextView
import androidx.activity.result.contract.ActivityResultContracts
import androidx.core.view.isVisible
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import androidx.navigation.fragment.findNavController
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import com.qolari.drivereplica.R
import com.qolari.drivereplica.capture.ScreenShareService
import com.qolari.drivereplica.data.AppGraph
import com.qolari.drivereplica.databinding.FragmentSupportBinding
import com.qolari.drivereplica.net.SupportMessageDto
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

/** Chat de apoio: conversa, anexos, chamada e partilha do ecrã completo. */
class SupportFragment : Fragment() {

    private var _binding: FragmentSupportBinding? = null
    private val binding get() = _binding!!
    private var threadUuid: String? = null
    private var category = "outro"
    private var pendingFileName: String? = null
    private var pendingBase64: String? = null
    private var shareUuid: String? = null
    private var pendingThread: String? = null
    private var pendingShare: String? = null

    private val pickFile = registerForActivityResult(ActivityResultContracts.GetContent()) { uri ->
        if (uri == null) return@registerForActivityResult
        val bytes = runCatching {
            requireContext().contentResolver.openInputStream(uri)?.use { it.readBytes() }
        }.getOrNull()
        if (bytes == null || bytes.size > 8 * 1024 * 1024) {
            _binding?.let {
                it.supportError.isVisible = true
                it.supportError.setText(R.string.support_attach_error)
            }
            return@registerForActivityResult
        }
        pendingFileName = uri.lastPathSegment ?: "anexo"
        pendingBase64 = android.util.Base64.encodeToString(bytes, android.util.Base64.NO_WRAP)
        binding.supportAttachLabel.isVisible = true
        binding.supportAttachLabel.text = getString(R.string.support_attached, pendingFileName)
    }

    private val captureScreen = registerForActivityResult(ActivityResultContracts.StartActivityForResult()) { result ->
        val thread = pendingThread
        val share = pendingShare
        if (result.resultCode == Activity.RESULT_OK && result.data != null && thread != null && share != null) {
            shareUuid = share
            ScreenShareService.start(requireContext(), result.resultCode, result.data!!, thread, share)
            binding.supportShare.setText(R.string.support_share_stop)
            binding.supportShareLabel.isVisible = true
        } else {
            pendingThread = null
            pendingShare = null
            _binding?.let {
                it.supportError.isVisible = true
                it.supportError.setText(R.string.support_share_denied)
            }
        }
    }

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentSupportBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        binding.supportBack.setOnClickListener { findNavController().popBackStack() }
        binding.supportSend.setOnClickListener { send() }
        binding.supportAttach.setOnClickListener { pickFile.launch("*/*") }
        binding.supportCall.setOnClickListener {
            startActivity(Intent(Intent.ACTION_DIAL, Uri.parse("tel:" + getString(R.string.support_phone))))
        }
        binding.supportCategory.setOnClickListener { chooseCategory() }
        binding.supportShare.setOnClickListener { toggleShare() }
        lifecycleScope.launch {
            AppGraph.repository.supportThreads()
                .onSuccess { threads ->
                    threadUuid = threads.firstOrNull()?.uuid
                    threadUuid?.let { load(it) } ?: render(emptyList())
                    binding.supportCategory.isVisible = threadUuid == null
                }
                .onFailure { showError() }
        }
    }

    private fun chooseCategory() {
        val ids = arrayOf("viagem", "conta", "pagamento", "seguranca", "bug", "outro")
        val labels = arrayOf(
            getString(R.string.support_cat_trip), getString(R.string.support_cat_account),
            getString(R.string.support_cat_payment), getString(R.string.support_cat_safety),
            getString(R.string.support_cat_bug), getString(R.string.support_cat_other),
        )
        MaterialAlertDialogBuilder(requireContext())
            .setTitle(R.string.support_category)
            .setSingleChoiceItems(labels, ids.indexOf(category).coerceAtLeast(0)) { dialog, which ->
                category = ids[which]
                binding.supportCategory.text = labels[which]
                dialog.dismiss()
            }
            .setNegativeButton(R.string.safety_cancel, null)
            .show()
    }

    private fun send() {
        val text = binding.supportInput.text?.toString()?.trim().orEmpty()
        if (text.isEmpty() && pendingBase64 == null) return
        binding.supportSend.isEnabled = false
        lifecycleScope.launch {
            val current = threadUuid
            val result: Result<String?> = if (current != null) {
                AppGraph.repository.sendSupportMessage(current, text, pendingFileName, pendingBase64).map { current }
            } else {
                AppGraph.repository.createSupportThread(text, category, pendingFileName, pendingBase64)
                    .map { it.thread?.uuid }
            }
            result.onSuccess { uuid ->
                if (uuid != null) threadUuid = uuid
                binding.supportInput.setText("")
                pendingFileName = null
                binding.supportAttachLabel.isVisible = false
                binding.supportCategory.isVisible = false
                threadUuid?.let { load(it) } ?: render(emptyList())
            }.onFailure { showError() }
            binding.supportSend.isEnabled = true
        }
    }

    private fun load(uuid: String) {
        lifecycleScope.launch {
            AppGraph.repository.supportThread(uuid)
                .onSuccess { render(it.messages) }
                .onFailure { showError() }
        }
    }

    private fun toggleShare() {
        if (shareUuid != null) {
            stopShare()
            return
        }
        val current = threadUuid
        if (current != null) {
            requestProjection(current)
        } else {
            lifecycleScope.launch {
                AppGraph.repository.createSupportThread("Quero partilhar o ecrã com o apoio.", "outro")
                    .onSuccess { r ->
                        threadUuid = r.thread?.uuid
                        threadUuid?.let { requestProjection(it) }
                    }
                    .onFailure { showError() }
            }
        }
    }

    private fun requestProjection(thread: String) {
        lifecycleScope.launch {
            AppGraph.repository.startScreenShare(thread)
                .onSuccess { share ->
                    if (share == null) {
                        showError()
                        return@onSuccess
                    }
                    pendingThread = thread
                    pendingShare = share.uuid
                    val manager = requireContext().getSystemService(MediaProjectionManager::class.java)
                    captureScreen.launch(manager.createScreenCaptureIntent())
                }
                .onFailure { showError() }
        }
    }

    private fun stopShare() {
        val thread = threadUuid
        val share = shareUuid
        shareUuid = null
        pendingThread = null
        pendingShare = null
        ScreenShareService.stop(requireContext())
        binding.supportShare.setText(R.string.support_share)
        binding.supportShareLabel.isVisible = false
        if (thread != null && share != null) {
            lifecycleScope.launch { AppGraph.repository.stopScreenShare(thread, share) }
        }
    }

    private fun showError() {
        binding.supportError.isVisible = true
        binding.supportError.setText(R.string.support_error)
    }

    private fun render(messages: List<SupportMessageDto>) {
        binding.supportError.isVisible = false
        binding.supportMessages.removeAllViews()
        if (messages.isEmpty()) {
            binding.supportMessages.addView(TextView(requireContext()).apply {
                setText(R.string.support_empty)
                setTextColor(requireContext().getColor(R.color.qd_core_gray600))
                textSize = 15f
                setPadding(dp(8), dp(8), dp(8), dp(8))
            })
            return
        }
        messages.forEach { m ->
            binding.supportMessages.addView(TextView(requireContext()).apply {
                text = if (m.hasFile) "${m.body}\n📎 ${m.fileName}" else m.body
                textSize = 15f
                setTextColor(requireContext().getColor(R.color.qd_ink))
                setPadding(dp(12), dp(10), dp(12), dp(10))
                setBackgroundColor(
                    if (m.sender == "support") 0xFFE8F0FE.toInt() else 0xFFF0F1F4.toInt(),
                )
                val lp = LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.WRAP_CONTENT,
                    LinearLayout.LayoutParams.WRAP_CONTENT,
                )
                lp.topMargin = dp(6)
                layoutParams = lp
            })
        }
    }

    private fun dp(value: Int) = (value * resources.displayMetrics.density).toInt()

    override fun onDestroyView() {
        val thread = threadUuid
        val share = shareUuid
        if (share != null) {
            ScreenShareService.stop(requireContext())
            if (thread != null) {
                CoroutineScope(Dispatchers.IO).launch {
                    AppGraph.repository.stopScreenShare(thread, share)
                }
            }
        }
        super.onDestroyView()
        _binding = null
    }
}
