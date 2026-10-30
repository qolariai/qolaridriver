package com.qolari.userlite

import android.app.Application
import com.qolari.userlite.data.AppGraph

class QolariApp : Application() {
    override fun onCreate() {
        super.onCreate()
        AppGraph.init(this)
    }
}
