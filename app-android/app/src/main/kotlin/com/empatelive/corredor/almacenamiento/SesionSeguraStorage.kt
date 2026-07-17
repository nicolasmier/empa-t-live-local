package com.empatelive.corredor.almacenamiento

import android.content.Context
import android.content.SharedPreferences
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey

/** Guarda en claro cero datos sensibles: el token de sesión (corredor) y el
 * de dispositivo viven cifrados en disco vía Keystore (A1 punto 3 del plan).
 *
 * Dos tokens con vidas distintas:
 * - Token de SESIÓN: identifica al corredor (login), 30 días de validez.
 * - Token de DISPOSITIVO: lo devuelve `unirse` a un evento concreto; es el
 *   que se usará para enviar posiciones (A2/A3) y consultar el estado
 *   (A4). Se pierde/regenera cada vez que se vuelve a unir (SUP-008).
 */
class SesionSeguraStorage(context: Context) {
    private val prefs: SharedPreferences by lazy {
        val clavePrincipal = MasterKey.Builder(context)
            .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
            .build()

        EncryptedSharedPreferences.create(
            context,
            "sesion_segura",
            clavePrincipal,
            EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
            EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM,
        )
    }

    fun guardarSesion(corredorId: Int, tokenSesion: String) {
        prefs.edit()
            .putInt(CLAVE_CORREDOR_ID, corredorId)
            .putString(CLAVE_TOKEN_SESION, tokenSesion)
            .apply()
    }

    fun obtenerTokenSesion(): String? = prefs.getString(CLAVE_TOKEN_SESION, null)

    fun obtenerCorredorId(): Int? =
        if (prefs.contains(CLAVE_CORREDOR_ID)) prefs.getInt(CLAVE_CORREDOR_ID, -1) else null

    fun haySesion(): Boolean = obtenerTokenSesion() != null && obtenerCorredorId() != null

    fun guardarUnion(
        eventoId: Int,
        inscripcionId: Int,
        distanciaId: Int,
        distanciaNombre: String,
        dorsal: String,
        tokenDispositivo: String,
    ) {
        prefs.edit()
            .putInt(CLAVE_EVENTO_ID, eventoId)
            .putInt(CLAVE_INSCRIPCION_ID, inscripcionId)
            .putInt(CLAVE_DISTANCIA_ID, distanciaId)
            .putString(CLAVE_DISTANCIA_NOMBRE, distanciaNombre)
            .putString(CLAVE_DORSAL, dorsal)
            .putString(CLAVE_TOKEN_DISPOSITIVO, tokenDispositivo)
            .apply()
    }

    fun obtenerTokenDispositivo(): String? = prefs.getString(CLAVE_TOKEN_DISPOSITIVO, null)

    fun obtenerEventoId(): Int? =
        if (prefs.contains(CLAVE_EVENTO_ID)) prefs.getInt(CLAVE_EVENTO_ID, -1) else null

    fun obtenerInscripcionId(): Int? =
        if (prefs.contains(CLAVE_INSCRIPCION_ID)) prefs.getInt(CLAVE_INSCRIPCION_ID, -1) else null

    fun obtenerDorsal(): String? = prefs.getString(CLAVE_DORSAL, null)

    fun obtenerDistanciaNombre(): String? = prefs.getString(CLAVE_DISTANCIA_NOMBRE, null)

    fun hayInscripcion(): Boolean = obtenerTokenDispositivo() != null

    fun cerrarSesion() {
        prefs.edit().clear().apply()
    }

    private companion object {
        const val CLAVE_CORREDOR_ID = "corredor_id"
        const val CLAVE_TOKEN_SESION = "token_sesion"
        const val CLAVE_EVENTO_ID = "evento_id"
        const val CLAVE_INSCRIPCION_ID = "inscripcion_id"
        const val CLAVE_DISTANCIA_ID = "distancia_id"
        const val CLAVE_DISTANCIA_NOMBRE = "distancia_nombre"
        const val CLAVE_DORSAL = "dorsal"
        const val CLAVE_TOKEN_DISPOSITIVO = "token_dispositivo"
    }
}
