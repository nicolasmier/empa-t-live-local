package com.empatelive.corredor.datos

import androidx.room.Entity
import androidx.room.PrimaryKey

/** Cola local de posiciones GPS (A3): toda posición se encola siempre aquí
 * y solo se marca [enviada] al recibir el `202` de la API — sin conexión
 * (da igual si es el móvil o el servidor, spec §5) la cola crece sin
 * perder puntos. Solo el esquema en esta ronda (A1); la lógica de envío
 * por lotes respetando el rate limit es de A3. */
@Entity(tableName = "posiciones_pendientes")
data class PosicionEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    // Hora de la LECTURA GPS en el dispositivo, no la del envío — es lo que
    // permite al servidor reconstruir el recorrido tras una sincronización
    // tardía (ISO-8601, mismo formato que espera `PuntoPosicionEntrada`).
    val timestampDispositivo: String,
    val latitud: Double,
    val longitud: Double,
    val precisionM: Float?,
    val velocidadKmh: Float?,
    val bateriaPct: Int?,
    val enviada: Boolean = false,
)
