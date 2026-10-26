package com.qolari.drivereplica

import android.app.Application
import com.qolari.drivereplica.data.AppGraph
import com.qolari.drivereplica.push.PushNotifications
import com.qolari.drivereplica.push.PushRegistrar
import com.qolari.drivereplica.state.UiPrefs

class QolariApp : Application() {
    override fun onCreate() {
        super.onCreate()
        UiPrefs.apply(this)
        AppGraph.init(this)
        PushNotifications.createChannel(this)
        PushRegistrar.register()
    }
}
