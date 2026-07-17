package com.empatelive.corredor.datos

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.Query
import androidx.room.Update

@Dao
interface PosicionDao {
    @Insert
    suspend fun insertar(posicion: PosicionEntity): Long

    // Orden por timestamp del dispositivo (no de inserción): al sincronizar
    // tras un corte, el lote debe respetar el orden real de la lectura GPS.
    @Query("SELECT * FROM posiciones_pendientes WHERE enviada = 0 ORDER BY timestampDispositivo ASC LIMIT :limite")
    suspend fun obtenerPendientes(limite: Int = 500): List<PosicionEntity>

    @Update
    suspend fun actualizar(posiciones: List<PosicionEntity>)

    @Query("DELETE FROM posiciones_pendientes WHERE enviada = 1")
    suspend fun purgarEnviadas()

    @Query("SELECT COUNT(*) FROM posiciones_pendientes WHERE enviada = 0")
    suspend fun contarPendientes(): Int
}
