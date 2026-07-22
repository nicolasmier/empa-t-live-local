# EstadoTransmitiendoVsSinSenal

**Pregunta:** ¿Cómo sabe el sistema si un corredor está "transmitiendo" o "sin
señal"?

## Respuesta

Se calcula a partir del **tiempo desde el último punto GPS** recibido, comparado
con el umbral del evento `umbral_sin_senal_seg` (por defecto **180 s**).

- Si el último punto es más reciente que el umbral → **transmitiendo**.
- Si ha pasado más tiempo → **sin señal**.

Lógica: `api/app/dominio/estado_transmision.py::calcular_estado_transmision`.

## Dónde se ve

- **Web pública**: color del dorsal sobre el mapa (sondeo cada ~3–5 s).
- **Panel** (pestaña Corredores): insignia de estado por corredor.
- **App del corredor** (pantalla de estado): "Transmitiendo" / "Sin señal".

Los colores del semáforo son **fijos** (spec Anexo E) e independientes del tema
de color de la app, para que su significado no cambie.

## Incidencias asociadas

Durante el evento En directo, el paso de un corredor a **sin señal** abre una
**incidencia**, que se cierra sola cuando vuelve a transmitir
(`api/app/servicios/incidencias.py`). Esto alimenta el panel de operación.

Ver también: [IngestaDePosiciones](IngestaDePosiciones.md).
