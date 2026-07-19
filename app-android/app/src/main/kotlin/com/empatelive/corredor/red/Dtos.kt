package com.empatelive.corredor.red

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

/** Espejo de `api/app/schemas/auth.py` (RegistroCorredorEntrada/LoginCorredorEntrada).
 * `telefono` es opcional: solo hace falta si el organizador cargó al corredor
 * en el Excel con un email distinto (o ninguno) al que usa aquí — sirve para
 * enlazar con esa cuenta pre-importada en vez de crear una nueva sin
 * inscripción (decisión 2026-07-19). */
@Serializable
data class RegistroCorredorEntrada(
    val nombre: String,
    val apellidos: String,
    val email: String,
    val password: String,
    val telefono: String? = null,
)

@Serializable
data class LoginCorredorEntrada(
    val email: String,
    val password: String,
)

/** Espejo de `SesionSalida` (api/app/schemas/auth.py) — vale tanto para
 * registro como para login de corredor. */
@Serializable
data class SesionSalida(
    @SerialName("access_token") val accessToken: String,
    @SerialName("token_type") val tokenType: String = "bearer",
    @SerialName("expira_en") val expiraEn: String,
)

/** Espejo de `CorredorSalida`/`CorredorActualizar` (api/app/schemas/corredores.py). */
@Serializable
data class CorredorSalida(
    val id: Int,
    val nombre: String,
    val apellidos: String,
    val club: String? = null,
    @SerialName("foto_url") val fotoUrl: String? = null,
    val email: String,
)

@Serializable
data class CorredorActualizar(
    val nombre: String? = null,
    val apellidos: String? = null,
    val club: String? = null,
)

/** Espejo de `UnirseEntrada` (api/app/schemas/unirse.py) — confirmación de
 * dorsal (decisión 2026-07-19): el código de evento solo identifica la
 * carrera, no al corredor; pedir también el dorsal que le dio el organizador
 * es el respaldo contra un email/teléfono mal enlazado — mejor que la app lo
 * detecte aquí a que el corredor descubra en directo que está viendo la señal
 * equivocada. */
@Serializable
data class UnirseEntrada(val dorsal: String)

/** Espejo de `UnirseSalida` (api/app/schemas/unirse.py). El `token_dispositivo`
 * es un token distinto al de sesión: es el que se usa luego para ingesta de
 * posiciones (A2/A3) y para consultar el estado de la inscripción (A4).
 * `eventoId`/`inscripcionId`: hueco de contrato que no devolvía `unirse`
 * hasta ahora — la app los necesita para `POST /eventos/{id}/posiciones` y
 * `GET /inscripciones/{id}/estado`, y no hay otra forma de obtenerlos (el
 * token de dispositivo es opaco). Añadidos al schema del servidor en la
 * misma sesión que este cliente. */
@Serializable
data class UnirseSalida(
    @SerialName("evento_id") val eventoId: Int,
    @SerialName("inscripcion_id") val inscripcionId: Int,
    @SerialName("distancia_id") val distanciaId: Int,
    @SerialName("distancia_nombre") val distanciaNombre: String,
    val dorsal: String,
    @SerialName("token_dispositivo") val tokenDispositivo: String,
    @SerialName("evento_estado") val eventoEstado: String,
)

/** Espejo de `PuntoPosicionEntrada`/`IngestaSalida` (api/app/schemas/posiciones.py). */
@Serializable
data class PuntoPosicionEntrada(
    @SerialName("timestamp_dispositivo") val timestampDispositivo: String,
    val latitud: Double,
    val longitud: Double,
    @SerialName("precision_m") val precisionM: Float? = null,
    @SerialName("velocidad_kmh") val velocidadKmh: Float? = null,
    @SerialName("bateria_pct") val bateriaPct: Int? = null,
)

@Serializable
data class IngestaSalida(val procesados: Int)

/** Espejo de `InscripcionEstadoSalida` (api/app/schemas/posiciones.py) — A4. */
@Serializable
data class InscripcionEstadoSalida(
    val dorsal: String,
    @SerialName("distancia_nombre") val distanciaNombre: String,
    @SerialName("estado_transmision") val estadoTransmision: String,
    val latitud: Double? = null,
    val longitud: Double? = null,
    @SerialName("timestamp_dispositivo") val timestampDispositivo: String? = null,
    @SerialName("timestamp_recepcion") val timestampRecepcion: String? = null,
    @SerialName("bateria_pct") val bateriaPct: Int? = null,
    @SerialName("estado_evento") val estadoEvento: String,
)

/** Espejo del formato de error único de la API (Anexo B §1):
 * `{"error": {"code": "...", "message": "..."}}`. */
@Serializable
data class ErrorApiEnvoltorio(val error: ErrorApiDetalle)

@Serializable
data class ErrorApiDetalle(val code: String, val message: String)
