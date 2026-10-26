package com.qolari.drivereplica.ui.compose

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.compose.runtime.Composable
import androidx.compose.ui.platform.ComposeView
import androidx.compose.ui.platform.ViewCompositionStrategy
import androidx.fragment.app.Fragment

/** Base dos ecrãs em Compose: uma `ComposeView` dentro de um Fragment (os restantes ecrãs são Views). */
abstract class ComposeFragment : Fragment() {

    @Composable
    protected abstract fun Content()

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View =
        ComposeView(requireContext()).apply {
            setViewCompositionStrategy(ViewCompositionStrategy.DisposeOnViewTreeLifecycleDestroyed)
            // this@ComposeFragment: dentro do apply, `Content()` sozinho resolveria para ComposeView.Content() (recursao infinita).
            setContent { QolariTheme { this@ComposeFragment.Content() } }
        }
}
