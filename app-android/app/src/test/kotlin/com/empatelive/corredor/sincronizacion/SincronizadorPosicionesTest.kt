package com.empatelive.corredor.sincronizacion

import com.empatelive.corredor.almacenamiento.SesionSeguraStorage
import com.empatelive.corredor.datos.PosicionDao
import com.empatelive.corredor.datos.PosicionEntity
import com.empatelive.corredor.red.ApiClient
import com.empatelive.corredor.red.ApiService
import kotlinx.coroutines.runBlocking
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import org.mockito.Mockito.mock
import org.mockito.Mockito.`when` as cuando

/** Dao falso en memoria: probar el sincronizador contra un Room de verdad
 * exigiría Robolectric solo para esto — con una implementación mínima de la
 * interfaz basta para comprobar la lógica de reintento/purga sin arrastrar
 * el framework de Android en un test JVM puro. */
private class PosicionDaoFalso : PosicionDao {
    val filas = mutableListOf<PosicionEntity>()
    private var siguienteId = 1L

    override suspend fun insertar(posicion: PosicionEntity): Long {
        val conId = posicion.copy(id = siguienteId++)
        filas.add(conId)
        return conId.id
    }

    override suspend fun obtenerPendientes(limite: Int): List<PosicionEntity> =
        filas.filter { !it.enviada }.sortedBy { it.timestampDispositivo }.take(limite)

    override suspend fun actualizar(posiciones: List<PosicionEntity>) {
        posiciones.forEach { actualizada ->
            val indice = filas.indexOfFirst { it.id == actualizada.id }
            if (indice >= 0) filas[indice] = actualizada
        }
    }

    override suspend fun purgarEnviadas() {
        filas.removeAll { it.enviada }
    }

    override suspend fun contarPendientes(): Int = filas.count { !it.enviada }
}

class SincronizadorPosicionesTest {
    private lateinit var servidor: MockWebServer
    private lateinit var api: ApiService
    private lateinit var dao: PosicionDaoFalso
    private lateinit var sesion: SesionSeguraStorage
    private lateinit var sincronizador: SincronizadorPosiciones

    @Before
    fun montar() {
        servidor = MockWebServer()
        servidor.start()
        api = ApiClient.crear(servidor.url("/").toString(), depurar = false) { null }
        dao = PosicionDaoFalso()
        sesion = mock(SesionSeguraStorage::class.java)
        cuando(sesion.obtenerTokenDispositivo()).thenReturn("token-dispositivo-123")
        cuando(sesion.obtenerEventoId()).thenReturn(7)
        sincronizador = SincronizadorPosiciones(api, dao, sesion)
    }

    @After
    fun apagar() {
        servidor.shutdown()
    }

    private fun posicion(id: Long, ts: String) = PosicionEntity(
        id = id,
        timestampDispositivo = ts,
        latitud = 43.48,
        longitud = -5.43,
        precisionM = 5f,
        velocidadKmh = 10f,
        bateriaPct = 80,
    )

    @Test
    fun `sin pendientes no llama a la API y devuelve exito`() = runBlocking {
        assertTrue(sincronizador.sincronizarUnaVez())
        assertEquals(0, servidor.requestCount)
    }

    @Test
    fun `envio con exito marca como enviadas y purga`() = runBlocking {
        dao.insertar(posicion(0, "2026-01-01T00:00:00Z"))
        dao.insertar(posicion(0, "2026-01-01T00:00:10Z"))
        servidor.enqueue(MockResponse().setResponseCode(202).setBody("""{"procesados":2}"""))

        val exito = sincronizador.sincronizarUnaVez()

        assertTrue(exito)
        assertTrue(dao.filas.isEmpty()) // purgadas tras confirmarse el envío
        val peticion = servidor.takeRequest()
        assertEquals("Bearer token-dispositivo-123", peticion.getHeader("Authorization"))
        assertTrue(peticion.path!!.contains("/eventos/7/posiciones"))
    }

    @Test
    fun `fallo del servidor no marca nada como enviado - se reintenta despues`() = runBlocking {
        dao.insertar(posicion(0, "2026-01-01T00:00:00Z"))
        servidor.enqueue(MockResponse().setResponseCode(500))

        val exito = sincronizador.sincronizarUnaVez()

        assertFalse(exito)
        assertEquals(1, dao.contarPendientes()) // sigue en la cola, nada se pierde
    }

    @Test
    fun `sin token de dispositivo no intenta nada`() = runBlocking {
        cuando(sesion.obtenerTokenDispositivo()).thenReturn(null)
        dao.insertar(posicion(0, "2026-01-01T00:00:00Z"))

        assertTrue(sincronizador.sincronizarUnaVez())
        assertEquals(0, servidor.requestCount)
    }
}
