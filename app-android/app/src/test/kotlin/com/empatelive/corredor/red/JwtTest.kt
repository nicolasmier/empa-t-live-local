package com.empatelive.corredor.red

import java.util.Base64
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class JwtTest {
    private fun construirTokenFalso(sub: String): String {
        fun segmento(json: String) =
            Base64.getUrlEncoder().withoutPadding().encodeToString(json.toByteArray())

        val cabecera = segmento("""{"alg":"HS256","typ":"JWT"}""")
        val payload = segmento("""{"sub":"$sub","tipo":"corredor","iat":1,"exp":2}""")
        return "$cabecera.$payload.firma-no-verificada-en-el-cliente"
    }

    @Test
    fun `extrae el id de corredor del claim sub`() {
        assertEquals(42, extraerCorredorIdDeToken(construirTokenFalso("42")))
    }

    @Test
    fun `token con formato invalido no revienta, devuelve null`() {
        assertNull(extraerCorredorIdDeToken("no-es-un-jwt"))
    }

    @Test
    fun `sub no numerico devuelve null en vez de lanzar`() {
        assertNull(extraerCorredorIdDeToken(construirTokenFalso("no-un-numero")))
    }
}
