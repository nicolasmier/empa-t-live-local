package com.empatelive.corredor.sincronizacion

import com.empatelive.corredor.almacenamiento.SesionSeguraStorage
import com.empatelive.corredor.datos.PosicionDao
import com.empatelive.corredor.datos.PosicionEntity
import com.empatelive.corredor.red.ApiService
import com.empatelive.corredor.red.PuntoPosicionEntrada
import com.empatelive.corredor.red.ResultadoApi
import com.empatelive.corredor.red.llamarApi

/** A3: envía por lotes lo que haya en la cola de Room (A2 ya se encarga de
 * que TODO punto GPS acabe ahí, encolando siempre — spec §5). El orden por
 * `timestampDispositivo` ya lo da `PosicionDao.obtenerPendientes`. Un fallo
 * de red (o un error del servidor) deja las filas como estaban —
 * `enviada = false` — así que el siguiente ciclo las reintenta sin perder
 * ningún punto; solo se purgan las que el servidor confirmó con éxito. */
class SincronizadorPosiciones(
    private val api: ApiService,
    private val dao: PosicionDao,
    private val sesion: SesionSeguraStorage,
) {
    /** `true` si no había nada que enviar o si el envío tuvo éxito; `false`
     * si había pendientes y el envío falló (se reintentará en el próximo ciclo). */
    suspend fun sincronizarUnaVez(): Boolean {
        val tokenDispositivo = sesion.obtenerTokenDispositivo() ?: return true
        val eventoId = sesion.obtenerEventoId() ?: return true

        val pendientes = dao.obtenerPendientes()
        if (pendientes.isEmpty()) return true

        val resultado = llamarApi {
            api.enviarPosiciones(
                "Bearer $tokenDispositivo",
                eventoId,
                pendientes.map { it.aPuntoPosicionEntrada() },
            )
        }

        return when (resultado) {
            is ResultadoApi.Ok -> {
                dao.actualizar(pendientes.map { it.copy(enviada = true) })
                dao.purgarEnviadas()
                true
            }
            is ResultadoApi.Error -> false
        }
    }
}

private fun PosicionEntity.aPuntoPosicionEntrada() = PuntoPosicionEntrada(
    timestampDispositivo = timestampDispositivo,
    latitud = latitud,
    longitud = longitud,
    precisionM = precisionM,
    velocidadKmh = velocidadKmh,
    bateriaPct = bateriaPct,
)
