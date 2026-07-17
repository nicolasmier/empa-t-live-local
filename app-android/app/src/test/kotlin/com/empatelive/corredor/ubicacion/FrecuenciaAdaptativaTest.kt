package com.empatelive.corredor.ubicacion

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class FrecuenciaAdaptativaTest {
    @Test
    fun `sin dato de velocidad usa el intervalo mas frecuente`() {
        assertEquals(17_500L, calcularIntervaloMs(null))
    }

    @Test
    fun `parado usa un intervalo entre 60 y 120 s`() {
        val intervalo = calcularIntervaloMs(0.0f)
        assertTrue(intervalo in 60_000..120_000)
    }

    @Test
    fun `justo por debajo del umbral de parado sigue siendo intervalo largo`() {
        val intervalo = calcularIntervaloMs(1.9f)
        assertTrue(intervalo in 60_000..120_000)
    }

    @Test
    fun `caminando o corriendo usa un intervalo entre 15 y 20 s`() {
        val intervalo = calcularIntervaloMs(10.0f)
        assertTrue(intervalo in 15_000..20_000)
    }

    @Test
    fun `conversion de metros por segundo a kmh`() {
        assertEquals(36.0f, metrosPorSegundoAKmh(10.0f), 0.01f)
    }
}
