package com.empatelive.corredor.ubicacion

import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

/** El único punto de verdad de "¿está transmitiendo ahora mismo?" para la
 * UI — más fiable que una bandera local en el ViewModel, porque el sistema
 * puede matar el `Service` sin que la Activity se entere por otro camino. */
object EstadoServicioUbicacion {
    private val _activo = MutableStateFlow(false)
    val activo: StateFlow<Boolean> = _activo.asStateFlow()

    fun marcarActivo(valor: Boolean) {
        _activo.value = valor
    }
}
