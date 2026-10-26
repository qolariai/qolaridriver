package com.qolari.drivereplica.ui.login

import android.os.Bundle
import android.view.View
import androidx.core.view.isVisible
import androidx.core.widget.doAfterTextChanged
import androidx.fragment.app.Fragment
import androidx.fragment.app.activityViewModels
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import androidx.navigation.fragment.findNavController
import com.qolari.drivereplica.R
import com.qolari.drivereplica.databinding.FragmentLoginCodeBinding
import com.qolari.drivereplica.databinding.FragmentLoginPhoneBinding
import com.qolari.drivereplica.databinding.FragmentWelcomeBinding
import com.qolari.drivereplica.ui.home.HomeViewModel
import kotlinx.coroutines.launch

private fun LoginError.messageRes() = when (this) {
    LoginError.WRONG_CODE -> R.string.login_error_wrong_code
    LoginError.NO_ACCOUNT -> R.string.login_error_no_account
    LoginError.NETWORK -> R.string.login_error_network
    LoginError.OTHER -> R.string.login_error_other
}

/** Boas-vindas (captura 031): fundo escuro, cabeçalho e "Continuar". */
class WelcomeFragment : Fragment(R.layout.fragment_welcome) {
    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        FragmentWelcomeBinding.bind(view).welcomeContinue.setOnClickListener {
            findNavController().navigate(R.id.loginPhoneFragment)
        }
    }
}

/** Telefone (captura 032). Os ecrãs de telefone e de código partilham o [LoginViewModel]. */
class LoginPhoneFragment : Fragment(R.layout.fragment_login_phone) {
    private val viewModel: LoginViewModel by activityViewModels { LoginViewModel.Factory }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        val b = FragmentLoginPhoneBinding.bind(view)
        b.phoneInput.doAfterTextChanged { viewModel.setPhone(it?.toString().orEmpty()) }
        b.phoneContinue.setOnClickListener { findNavController().navigate(R.id.loginCodeFragment) }
        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                viewModel.state.collect { s -> b.phoneContinue.isEnabled = s.phoneValid }
            }
        }
    }
}

/** Código de 4 dígitos. Ao entrar, volta à Página inicial e deixa de ser possível regressar ao login. */
class LoginCodeFragment : Fragment(R.layout.fragment_login_code) {
    private val viewModel: LoginViewModel by activityViewModels { LoginViewModel.Factory }
    private val homeViewModel: HomeViewModel by activityViewModels { HomeViewModel.Factory }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        val b = FragmentLoginCodeBinding.bind(view)
        b.codeSentTo.text = getString(R.string.login_code_sent, viewModel.state.value.fullPhone)
        // O campo segue o estado (volta a vazio após um código errado) sem voltar a avisar o ViewModel.
        var syncing = false
        b.codeInput.doAfterTextChanged { if (!syncing) viewModel.setCode(it?.toString().orEmpty()) }
        b.codeBack.setOnClickListener { findNavController().popBackStack() }
        b.codeNext.setOnClickListener { viewModel.submit() }
        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                viewModel.state.collect { s ->
                    b.codeNext.isEnabled = s.codeValid && !s.loading
                    b.codeError.isVisible = s.error != null
                    s.error?.let { b.codeError.setText(it.messageRes()) }
                    if (b.codeInput.text.toString() != s.code) {
                        syncing = true
                        b.codeInput.setText(s.code)
                        b.codeInput.setSelection(s.code.length)
                        syncing = false
                    }
                    if (s.signedIn) {
                        viewModel.reset()
                        homeViewModel.refresh(userInitiated = false)
                        findNavController().navigate(
                            R.id.homeFragment, null,
                            androidx.navigation.NavOptions.Builder().setPopUpTo(R.id.nav_main, true).build(),
                        )
                    }
                }
            }
        }
    }
}
