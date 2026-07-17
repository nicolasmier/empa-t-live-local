package com.empatelive.corredor.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider

/** Fábrica genérica para crear `ViewModel`s con [com.empatelive.corredor.di.AppContainer]
 * inyectado a mano (sin Hilt/Koin, ver AppContainer). */
class ViewModelFactory(private val crear: () -> ViewModel) : ViewModelProvider.Factory {
    @Suppress("UNCHECKED_CAST")
    override fun <T : ViewModel> create(modelClass: Class<T>): T = crear() as T
}
