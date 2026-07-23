package com.empatelive.corredor.ui.unirse

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.empatelive.corredor.almacenamiento.SesionSeguraStorage
import com.empatelive.corredor.red.ApiService
import com.empatelive.corredor.red.ResultadoApi
import com.empatelive.corredor.red.UnirseEntrada
import com.empatelive.corredor.red.llamarApi
import kotlinx.coroutines.launch

class UnirseViewModel(
    private val api: ApiService,
    private val sesion: SesionSeguraStorage,
) : ViewModel() {
    var codigo by mutableStateOf("")
    // Confirmación de dorsal (decisión 2026-07-19): el código de evento identifica
    // la carrera, no al corredor — pedir también el dorsal que le dio el
    // organizador es el respaldo contra un email/teléfono mal enlazado. Nombre
    // distinto de `dorsal` (abajo) para no chocar con el dorsal YA confirmado
    // que se muestra tras unirse.
    var dorsalIntroducido by mutableStateOf("")
    var cargando by mutableStateOf(false)
        private set
    var error by mutableStateOf<String?>(null)
        private set

    // Si ya hay una inscripción guardada (relanzar la app tras unirse una
    // vez), se muestra directamente — es el criterio de aceptación de A1:
    // "el token sobrevive a cerrar y reabrir la app".
    var dorsal by mutableStateOf(sesion.obtenerDorsal())
        private set
    var distanciaNombre by mutableStateOf(sesion.obtenerDistanciaNombre())
        private set

    // Nombre y foto del corredor para la pantalla "En carrera": no vienen en el
    // token ni en `unirse`, así que se leen del perfil (GET /corredores/{id}).
    var nombreCorredor by mutableStateOf<String?>(null)
        private set
    var fotoUrl by mutableStateOf<String?>(null)
        private set

    init {
        cargarPerfilBasico()
    }

    private fun cargarPerfilBasico() {
        val corredorId = sesion.obtenerCorredorId() ?: return
        viewModelScope.launch {
            // Silencioso a propósito: la pantalla funciona igual sin foto/nombre
            // (dorsal + distancia bastan); esto solo los añade si están.
            when (val resultado = llamarApi { api.obtenerPerfil(corredorId) }) {
                is ResultadoApi.Ok -> {
                    nombreCorredor =
                        "${resultado.datos.nombre} ${resultado.datos.apellidos}".trim()
                    fotoUrl = resultado.datos.fotoUrl
                }
                is ResultadoApi.Error -> Unit
            }
        }
    }

    fun unirse() {
        val codigoLimpio = codigo.trim().uppercase()
        val dorsalLimpio = dorsalIntroducido.trim()
        if (codigoLimpio.isBlank()) {
            error = "Introduce el código de la carrera."
            return
        }
        if (dorsalLimpio.isBlank()) {
            error = "Introduce tu dorsal para confirmar que eres tú."
            return
        }
        viewModelScope.launch {
            cargando = true
            error = null
            val resultado = llamarApi {
                api.unirseAEvento(codigoLimpio, UnirseEntrada(dorsal = dorsalLimpio))
            }
            when (resultado) {
                is ResultadoApi.Ok -> {
                    sesion.guardarUnion(
                        eventoId = resultado.datos.eventoId,
                        inscripcionId = resultado.datos.inscripcionId,
                        distanciaId = resultado.datos.distanciaId,
                        distanciaNombre = resultado.datos.distanciaNombre,
                        dorsal = resultado.datos.dorsal,
                        tokenDispositivo = resultado.datos.tokenDispositivo,
                    )
                    dorsal = resultado.datos.dorsal
                    distanciaNombre = resultado.datos.distanciaNombre
                }
                is ResultadoApi.Error -> error = resultado.mensaje
            }
            cargando = false
        }
    }

    fun unirseAOtroEvento() {
        dorsal = null
        distanciaNombre = null
        codigo = ""
        dorsalIntroducido = ""
    }
}
