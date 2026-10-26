package com.qolari.userlite

import android.view.View
import androidx.test.core.app.ActivityScenario
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.junit.Assert.assertNotNull
import org.junit.Test
import org.junit.runner.RunWith

/** Smoke: a Activity arranca e o NavHost e montado (nao valida fluxos). */
@RunWith(AndroidJUnit4::class)
class SmokeTest {

    @Test
    fun mainActivityHasNavHost() {
        ActivityScenario.launch(MainActivity::class.java).use { scenario ->
            scenario.onActivity { activity ->
                assertNotNull(activity.findViewById<View>(R.id.navHost))
            }
        }
    }
}
