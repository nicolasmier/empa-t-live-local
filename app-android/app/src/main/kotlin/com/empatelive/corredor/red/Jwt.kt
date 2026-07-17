package com.empatelive.corredor.red

import java.util.Base64
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive

/** El login/registro de corredor no devuelve el id del corredor de forma
 * explícita, solo el JWT de sesión — igual que hace `panel/src/auth.ts` en
 * el frontend web, se lee el claim `sub` del payload sin verificar la
 * firma (eso lo hace el servidor en cada petición; esto es solo para que
 * el propio cliente sepa su id, ya que no existe un endpoint `/corredores/me`).
 *
 * `java.util.Base64` (no `android.util.Base64`) a propósito: disponible
 * desde API 26 (nuestro minSdk) y, a diferencia del de Android, se puede
 * probar con JUnit normal en `src/test` sin Robolectric ni un dispositivo. */
fun extraerCorredorIdDeToken(token: String): Int? {
    val partes = token.split(".")
    if (partes.size != 3) return null
    return runCatching {
        val payloadBytes = Base64.getUrlDecoder().decode(partes[1])
        val payload = Json.parseToJsonElement(String(payloadBytes, Charsets.UTF_8)).jsonObject
        payload["sub"]?.jsonPrimitive?.content?.toIntOrNull()
    }.getOrNull()
}
