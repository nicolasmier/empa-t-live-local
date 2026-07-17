package com.empatelive.corredor.ui.estado

import android.content.Context
import android.os.BatteryManager
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.empatelive.corredor.almacenamiento.SesionSeguraStorage
import com.empatelive.corredor.datos.PosicionDao
import com.empatelive.corredor.red.ApiService
import com.empatelive.corredor.red.ResultadoApi
import com.empatelive.corredor.red.llamarApi
import com.empatelive.corredor.ubicacion.EstadoServicioUbicacion
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.launchIn
import kotlinx.coroutines.flow.onEach
import kotlinx.coroutines.launch

private const val INTERVALO_SONDEO_MS = 5_000L

/** A4: consulta pasiva (el corredor no mira el móvil corriendo) — dorsal,
 * GPS, batería, conexión y transmisión, combinando estado LOCAL (el
 * `Service` sigue vivo? cuántos puntos hay sin enviar en Room?) con la
 * confirmación del propio SERVIDOR vía `GET /inscripciones/{id}/estado`
 * (spec A4) — dos fuentes porque el servicio puede estar "transmitiendo"
 * localmente mientras la red está caída, y eso es precisamente lo que hay
 * que mostrar (encolando, no perdiendo nada). */
class EstadoViewModel(
    private val api: ApiService,
    private val dao: PosicionDao,
    private val sesion: SesionSeguraStorage,
    private val contexto: Context,
) : ViewModel() {
    var transmisionActivaLocal by mutableStateOf(EstadoServicioUbicacion.activo.value)
        private set
    var puntosPendientes by mutableStateOf(0)
        private set
    var bateriaPct by mutableStateOf<Int?>(null)
        private set
    var estadoServidor by mutableStateOf<String?>(null)
        private set
    var conectadoConServidor by mutableStateOf(true)
        private set

    init {
        EstadoServicioUbicacion.activo
            .onEach { transmisionActivaLocal = it }
            .launchIn(viewModelScope)

        viewModelScope.launch {
            while (true) {
                puntosPendientes = dao.contarPendientes()
                bateriaPct = leerPorcentajeBateria()
                sondearServidor()
                delay(INTERVALO_SONDEO_MS)
            }
        }
    }

    private suspend fun sondearServidor() {
        val tokenDispositivo = sesion.obtenerTokenDispositivo() ?: return
        val inscripcionId = sesion.obtenerInscripcionId() ?: return

        when (
            val resultado = llamarApi {
                api.obtenerEstadoInscripcion("Bearer $tokenDispositivo", inscripcionId)
            }
        ) {
            is ResultadoApi.Ok -> {
                estadoServidor = resultado.datos.estadoTransmision
                conectadoConServidor = true
            }
            is ResultadoApi.Error -> conectadoConServidor = false
        }
    }

    private fun leerPorcentajeBateria(): Int? {
        val gestor = contexto.getSystemService(Context.BATTERY_SERVICE) as? BatteryManager
            ?: return null
        return gestor.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY)
    }
}
