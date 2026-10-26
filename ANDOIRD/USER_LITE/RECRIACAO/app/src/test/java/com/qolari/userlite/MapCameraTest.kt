package com.qolari.userlite

import com.qolari.userlite.ui.map.MapCamera
import org.junit.Assert.assertEquals
import org.junit.Test

class MapCameraTest {

    @Test
    fun zoomInAndOutAreBounded() {
        var camera = MapCamera()
        repeat(20) { camera = camera.zoomIn() }
        assertEquals(MapCamera.MAX, camera.zoom)
        repeat(20) { camera = camera.zoomOut() }
        assertEquals(MapCamera.MIN, camera.zoom)
    }

    @Test
    fun zoomInIncreasesScale() {
        val camera = MapCamera().zoomIn()
        assertEquals(1.25f, camera.zoom)
        assertEquals(1.25f, camera.scale)
    }

    @Test
    fun recenterReturnsToDefault() {
        val camera = MapCamera().zoomIn().zoomIn()
        assertEquals(MapCamera(), camera.recenter())
    }
}
