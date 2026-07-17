package com.empatelive.corredor.red

import kotlinx.coroutines.runBlocking
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

/** Prueba la capa de red de verdad contra un servidor HTTP real (MockWebServer),
 * no contra mocks de Retrofit — así se comprueba también la serialización y
 * el interceptor de autenticación, no solo la lógica de la app. */
class ApiClientTest {
    private lateinit var servidor: MockWebServer
    private lateinit var api: ApiService
    private var tokenActual: String? = null

    @Before
    fun montar() {
        servidor = MockWebServer()
        servidor.start()
        api = ApiClient.crear(
            baseUrl = servidor.url("/").toString(),
            depurar = false,
            obtenerTokenSesion = { tokenActual },
        )
    }

    @After
    fun apagar() {
        servidor.shutdown()
    }

    @Test
    fun `login exitoso decodifica la sesion`() = runBlocking {
        servidor.enqueue(
            MockResponse()
                .setResponseCode(200)
                .setBody("""{"access_token":"tok123","token_type":"bearer","expira_en":"2026-01-01T00:00:00Z"}"""),
        )

        val resultado = llamarApi { api.loginCorredor(LoginCorredorEntrada("a@b.com", "12345678")) }

        assertTrue(resultado is ResultadoApi.Ok)
        assertEquals("tok123", (resultado as ResultadoApi.Ok).datos.accessToken)
    }

    @Test
    fun `error de la API se traduce al mensaje del envoltorio, no una excepcion`() = runBlocking {
        servidor.enqueue(
            MockResponse()
                .setResponseCode(401)
                .setBody("""{"error":{"code":"credenciales_invalidas","message":"Email o contraseña incorrectos."}}"""),
        )

        val resultado = llamarApi { api.loginCorredor(LoginCorredorEntrada("a@b.com", "mala")) }

        assertTrue(resultado is ResultadoApi.Error)
        assertEquals("Email o contraseña incorrectos.", (resultado as ResultadoApi.Error).mensaje)
        assertEquals(401, resultado.codigoHttp)
    }

    @Test
    fun `el interceptor adjunta el Bearer solo cuando hay token guardado`() = runBlocking {
        tokenActual = "sesion-guardada"
        servidor.enqueue(MockResponse().setResponseCode(200).setBody("""{"id":1,"nombre":"A","apellidos":"B","club":null,"foto_url":null,"email":"a@b.com"}"""))

        llamarApi { api.obtenerPerfil(1) }

        val peticion = servidor.takeRequest()
        assertEquals("Bearer sesion-guardada", peticion.getHeader("Authorization"))
    }

    @Test
    fun `sin token guardado no se manda cabecera Authorization`() = runBlocking {
        tokenActual = null
        servidor.enqueue(
            MockResponse()
                .setResponseCode(200)
                .setBody("""{"access_token":"x","token_type":"bearer","expira_en":"2026-01-01T00:00:00Z"}"""),
        )

        llamarApi { api.loginCorredor(LoginCorredorEntrada("a@b.com", "12345678")) }

        val peticion = servidor.takeRequest()
        assertNull(peticion.getHeader("Authorization"))
    }
}
