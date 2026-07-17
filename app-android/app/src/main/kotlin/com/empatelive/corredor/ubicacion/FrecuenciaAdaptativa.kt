package com.empatelive.corredor.ubicacion

/** Frecuencia adaptativa según velocidad (spec v10 §6/RF-009): parado
 * 60-120 s, caminando/corriendo 15-20 s. Función pura y testeable sin
 * depender de Android/`Service` — el servicio solo la llama con la última
 * velocidad conocida (m/s, la que da `Location.speed`) cada vez que decide
 * si hay que reconfigurar el intervalo de `FusedLocationProviderClient`. */

private const val UMBRAL_PARADO_KMH = 2.0
private const val INTERVALO_PARADO_MS = 90_000L // punto medio de 60-120 s
private const val INTERVALO_MOVIMIENTO_MS = 17_500L // punto medio de 15-20 s

fun calcularIntervaloMs(velocidadKmh: Float?): Long {
    if (velocidadKmh == null) return INTERVALO_MOVIMIENTO_MS // sin dato aún: pecar de frecuente, no de escaso
    return if (velocidadKmh < UMBRAL_PARADO_KMH) INTERVALO_PARADO_MS else INTERVALO_MOVIMIENTO_MS
}

fun metrosPorSegundoAKmh(metrosPorSegundo: Float): Float = metrosPorSegundo * 3.6f
