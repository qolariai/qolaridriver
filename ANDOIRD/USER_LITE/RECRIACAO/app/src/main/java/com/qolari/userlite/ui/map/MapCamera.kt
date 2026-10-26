package com.qolari.userlite.ui.map

/**
 * Zoom do mapa desenhado. Puro (sem Android) para poder ser testado: os botoes do mapa
 * mudam a camara, nao um texto. Minimo 1 para o desenho nunca deixar bordas vazias.
 */
data class MapCamera(val zoom: Float = 1f) {

    val scale: Float get() = zoom.coerceIn(MIN, MAX)

    fun zoomIn(): MapCamera = copy(zoom = (zoom * STEP).coerceAtMost(MAX))

    fun zoomOut(): MapCamera = copy(zoom = (zoom / STEP).coerceAtLeast(MIN))

    fun recenter(): MapCamera = MapCamera()

    companion object {
        const val MIN = 1f
        const val MAX = 2.2f
        const val STEP = 1.25f
    }
}
