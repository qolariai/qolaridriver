package com.qolari.userlite.ui.ride

/**
 * Viagem terminal já vista nesta sessão. O `/rt/lite/active` devolve o desfecho recente
 * (completed/cancelled/no_drivers) para a avaliação; sem esta marca, o Início voltava a
 * abrir o mesmo ecrã em ciclo depois de o utilizador carregar em "Voltar ao início".
 */
object SeenTrips {
    @Volatile
    var lastTerminal: String? = null
}
