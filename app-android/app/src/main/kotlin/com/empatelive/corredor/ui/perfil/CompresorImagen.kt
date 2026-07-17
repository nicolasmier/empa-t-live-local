package com.empatelive.corredor.ui.perfil

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.net.Uri
import java.io.ByteArrayOutputStream

private const val LADO_MAXIMO_PX = 1024

// Margen deliberado bajo el límite real del servidor (5 MB, api/app/servicios/imagenes.py):
// comprimir en el dispositivo, no delegar en la API el rechazo de fotos de
// cámara moderna de 30-40 MB (spec A1 punto 2).
private const val LIMITE_BYTES = 4 * 1024 * 1024

/** Redimensiona (lado máximo 1024px) y comprime a JPEG bajando la calidad
 * hasta quedar por debajo de [LIMITE_BYTES]. El servidor igualmente
 * redimensiona a 512×512 al recibirla — esto es solo para no subir 30 MB
 * de una cámara moderna por una red potencialmente lenta el día de la carrera. */
fun comprimirImagenParaSubir(context: Context, uri: Uri): ByteArray {
    val bitmapOriginal = context.contentResolver.openInputStream(uri).use { flujo ->
        BitmapFactory.decodeStream(flujo)
    } ?: error("No se pudo leer la imagen seleccionada.")

    val escala = LADO_MAXIMO_PX.toFloat() / maxOf(bitmapOriginal.width, bitmapOriginal.height)
    val bitmap = if (escala < 1f) {
        Bitmap.createScaledBitmap(
            bitmapOriginal,
            (bitmapOriginal.width * escala).toInt(),
            (bitmapOriginal.height * escala).toInt(),
            true,
        )
    } else {
        bitmapOriginal
    }

    var calidad = 90
    var bytes: ByteArray
    do {
        val buffer = ByteArrayOutputStream()
        bitmap.compress(Bitmap.CompressFormat.JPEG, calidad, buffer)
        bytes = buffer.toByteArray()
        calidad -= 10
    } while (bytes.size > LIMITE_BYTES && calidad > 10)

    return bytes
}
