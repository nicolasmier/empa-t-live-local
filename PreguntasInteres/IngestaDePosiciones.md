# IngestaDePosiciones

**Pregunta:** ¿Cómo procesa el servidor los puntos GPS que envía la app?

## Endpoint

`POST /eventos/{evento_id}/posiciones` (`api/app/routers/posiciones.py`),
autenticado con el **token de dispositivo** (no el de sesión). Solo funciona con
el evento en **En directo** (si no, `409 evento_no_en_directo`).

## Reglas de la ingesta

- **Lote máximo**: `MAX_PUNTOS_POR_LOTE = 500` puntos por petición; más → `413/400
  lote_demasiado_grande`, hay que dividir el envío.
- **El evento del token debe casar** con el evento de la ruta (un token de un
  evento no sirve para otro).
- **Clasificación de cada punto** según la desviación entre la hora del
  dispositivo y la de recepción:
  - `directo` si la desviación ≤ **10 s** (`UMBRAL_DIRECTO_SEG`).
  - `sincronizado` si es mayor (punto que venía encolado sin conexión).
  - Marcado **sospechoso** si la desviación supera **600 s**
    (`UMBRAL_SOSPECHOSO_SEG`) o si hay incoherencias.
- **Nunca retrocede la posición actual** (EA-007): la "posición actual" solo se
  actualiza si el punto más reciente del lote es **posterior** al almacenado
  (UPSERT condicionado). Un lote desordenado no hace saltar hacia atrás al
  corredor en el mapa.

## Qué se guarda

- `PosicionActual`: el último punto por inscripción (lo que pinta la web).
- `PosicionHistorico`: la traza completa.
- Además, la ingesta actualiza el estado de **incidencias de sin señal** por lote.

Ver también: [EstadoTransmitiendoVsSinSenal](EstadoTransmitiendoVsSinSenal.md),
[TransmisionGpsYSinConexion](TransmisionGpsYSinConexion.md).
