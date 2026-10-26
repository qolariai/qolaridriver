package com.qolari.userlite

import android.app.Application
import com.qolari.userlite.data.AppGraph
import com.qolari.userlite.data.UiPrefs
import com.qolari.userlite.push.PushNotifications
import com.qolari.userlite.push.PushRegistrar

class QolariApp : Application() {
    override fun onCreate() {
        super.onCreate()
        UiPrefs.apply(this)
        AppGraph.init(this)
        PushNotifications.createChannel(this)
        PushRegistrar.register()
    }
}
