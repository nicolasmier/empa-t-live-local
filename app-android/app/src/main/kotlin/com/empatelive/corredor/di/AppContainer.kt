package com.empatelive.corredor.di

import android.content.Context
import com.empatelive.corredor.BuildConfig
import com.empatelive.corredor.almacenamiento.SesionSeguraStorage
import com.empatelive.corredor.datos.AppDatabase
import com.empatelive.corredor.datos.PosicionDao
import com.empatelive.corredor.red.ApiClient
import com.empatelive.corredor.red.ApiService

/** Contenedor de dependencias manual: sin Hilt/Koin a propósito (FASE A1
 * tiene pocas pantallas — menos piezas que depurar mientras se monta el
 * toolchain de Android por primera vez en este proyecto). Si el `Service`
 * de A2 necesita inyección más allá de esto, reconsiderar Hilt entonces. */
class AppContainer(context: Context) {
    val sesion: SesionSeguraStorage = SesionSeguraStorage(context.applicationContext)

    val api: ApiService = ApiClient.crear(
        baseUrl = BuildConfig.BASE_URL,
        depurar = BuildConfig.DEBUG,
        obtenerTokenSesion = { sesion.obtenerTokenSesion() },
    )

    val posicionDao: PosicionDao = AppDatabase.obtener(context.applicationContext).posicionDao()
}
