package com.qolari.drivereplica

import android.app.Application
import com.qolari.drivereplica.data.AppGraph

class QolariApp : Application() {
    override fun onCreate() {
        super.onCreate()
        AppGraph.init(this)
    }
}
