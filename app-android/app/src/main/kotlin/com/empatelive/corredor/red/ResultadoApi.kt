package com.empatelive.corredor.red

import java.io.IOException
import kotlinx.serialization.json.Json
import retrofit2.Response

/** Envoltorio único para toda llamada a la API: nunca deja que una excepción
 * de red o un cuerpo de error sin parsear llegue a la UI — todo pantalla
 * de la app trabaja contra este tipo, nunca contra `Response<T>` directamente. */
sealed interface ResultadoApi<out T> {
    data class Ok<T>(val datos: T) : ResultadoApi<T>
    // `codigo` es el `code` de la API (p. ej. "cuenta_no_activada"); permite a la
    // UI reaccionar a un caso concreto sin comparar cadenas de mensaje.
    data class Error(
        val mensaje: String,
        val codigoHttp: Int?,
        val codigo: String? = null,
    ) : ResultadoApi<Nothing>
}

private val jsonLaxo = Json { ignoreUnknownKeys = true }

suspend fun <T> llamarApi(block: suspend () -> Response<T>): ResultadoApi<T> {
    return try {
        val respuesta = block()
        if (respuesta.isSuccessful) {
            val cuerpo = respuesta.body()
            if (cuerpo != null) {
                ResultadoApi.Ok(cuerpo)
            } else {
                ResultadoApi.Error("El servidor respondió sin contenido.", respuesta.code())
            }
        } else {
            val detalle = respuesta.errorBody().aErrorApi(jsonLaxo)
            ResultadoApi.Error(
                mensaje = detalle?.message ?: "Error del servidor (${respuesta.code()}).",
                codigoHttp = respuesta.code(),
                codigo = detalle?.code,
            )
        }
    } catch (e: IOException) {
        ResultadoApi.Error("No se pudo conectar con el servidor. Comprueba tu conexión.", null)
    }
}
