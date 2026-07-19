package com.empatelive.corredor.red

import okhttp3.MultipartBody
import okhttp3.ResponseBody
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.Header
import retrofit2.http.Multipart
import retrofit2.http.PUT
import retrofit2.http.POST
import retrofit2.http.Part
import retrofit2.http.Path

/** Los 5 endpoints que necesita la FASE A1 (spec v10 Anexo B, sección
 * corredor). Cada `Response<T>` se envuelve luego en [ResultadoApi] para
 * traducir los códigos de error al formato único `{"error": {...}}` de la
 * API en vez de dejar que Retrofit lance una excepción genérica. */
interface ApiService {
    @POST("auth/corredores/registro")
    suspend fun registrarCorredor(@Body datos: RegistroCorredorEntrada): Response<SesionSalida>

    @POST("auth/corredores/login")
    suspend fun loginCorredor(@Body datos: LoginCorredorEntrada): Response<SesionSalida>

    @GET("corredores/{id}")
    suspend fun obtenerPerfil(@Path("id") corredorId: Int): Response<CorredorSalida>

    @PUT("corredores/{id}")
    suspend fun actualizarPerfil(
        @Path("id") corredorId: Int,
        @Body datos: CorredorActualizar,
    ): Response<CorredorSalida>

    @Multipart
    @POST("corredores/{id}/foto")
    suspend fun subirFoto(
        @Path("id") corredorId: Int,
        @Part archivo: MultipartBody.Part,
    ): Response<CorredorSalida>

    @POST("eventos/codigo/{codigoAcceso}/unirse")
    suspend fun unirseAEvento(
        @Path("codigoAcceso") codigoAcceso: String,
        @Body datos: UnirseEntrada,
    ): Response<UnirseSalida>

    // Token de DISPOSITIVO explícito (@Header), no el de sesión que añade
    // el interceptor por defecto (ver ApiClient) — son credenciales
    // distintas (spec Anexo E).
    @POST("eventos/{eventoId}/posiciones")
    suspend fun enviarPosiciones(
        @Header("Authorization") autorizacionDispositivo: String,
        @Path("eventoId") eventoId: Int,
        @Body puntos: List<PuntoPosicionEntrada>,
    ): Response<IngestaSalida>

    @GET("inscripciones/{inscripcionId}/estado")
    suspend fun obtenerEstadoInscripcion(
        @Header("Authorization") autorizacionDispositivo: String,
        @Path("inscripcionId") inscripcionId: Int,
    ): Response<InscripcionEstadoSalida>
}

/** Retrofit no expone el cuerpo del error en `Response.errorBody()` ya
 * parseado — hay que decodificarlo a mano contra [ErrorApiEnvoltorio]. */
fun ResponseBody?.aMensajeDeError(json: kotlinx.serialization.json.Json): String? {
    val texto = this?.string() ?: return null
    return runCatching { json.decodeFromString<ErrorApiEnvoltorio>(texto).error.message }
        .getOrNull()
}
