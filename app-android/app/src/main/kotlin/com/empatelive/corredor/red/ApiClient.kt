package com.empatelive.corredor.red

import kotlinx.serialization.json.Json
import okhttp3.Interceptor
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.kotlinx.serialization.asConverterFactory

/** Construye el cliente Retrofit. El token que adjunta el interceptor es el
 * de SESIÓN (corredor) — el token de DISPOSITIVO (el que devuelve
 * `unirse`) es distinto y se usará explícitamente en la ingesta de
 * posiciones (A2/A3), no aquí. */
object ApiClient {
    private val json = Json { ignoreUnknownKeys = true }

    fun crear(baseUrl: String, depurar: Boolean, obtenerTokenSesion: () -> String?): ApiService {
        // Si la llamada ya trae su propia cabecera Authorization (p. ej.
        // `enviarPosiciones`/`obtenerEstadoInscripcion`, con el token de
        // DISPOSITIVO explícito vía @Header), se respeta tal cual — el
        // interceptor solo añade el de sesión cuando no hay ninguno.
        val interceptorAuth = Interceptor { chain ->
            val original = chain.request()
            val peticion = if (original.header("Authorization") != null) {
                original
            } else {
                val token = obtenerTokenSesion()
                if (token != null) {
                    original.newBuilder().addHeader("Authorization", "Bearer $token").build()
                } else {
                    original
                }
            }
            chain.proceed(peticion)
        }

        val clienteHttp = OkHttpClient.Builder()
            .addInterceptor(interceptorAuth)
            .apply {
                if (depurar) {
                    addInterceptor(HttpLoggingInterceptor().apply {
                        level = HttpLoggingInterceptor.Level.BASIC
                    })
                }
            }
            .build()

        val urlConBarra = if (baseUrl.endsWith("/")) baseUrl else "$baseUrl/"

        return Retrofit.Builder()
            .baseUrl(urlConBarra)
            .client(clienteHttp)
            .addConverterFactory(json.asConverterFactory("application/json".toMediaType()))
            .build()
            .create(ApiService::class.java)
    }
}
