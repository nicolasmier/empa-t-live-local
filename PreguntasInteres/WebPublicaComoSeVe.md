# WebPublicaComoSeVe

**Pregunta:** ¿Cómo se ve la carrera en directo en la web pública?

## Respuesta

La **web pública** (`web-publica`, Vite en `:8081`, LAN / pantalla del recinto)
muestra un **mapa** (Leaflet) con:

- El **recorrido** de cada distancia dibujado a partir de su **GPX**.
- Los **dorsales** moviéndose sobre el mapa según las últimas posiciones.
- El **estado** de cada corredor por color (transmitiendo / sin señal, ver
  [EstadoTransmitiendoVsSinSenal](EstadoTransmitiendoVsSinSenal.md)).

## Actualización casi en tiempo real

La web **sondea** la API cada **~3–5 s** para traer las posiciones actuales; no
hay push. El movimiento se ve con ese pequeño retardo, que es suficiente para una
pantalla de recinto.

Endpoint que consume: `GET
/eventos/{evento_id}/distancias/{distancia_id}/posiciones`.

## Identidad visual

Fondo azul y logo blanco de cabecera (`web-publica/public/logo-horizontal.png`),
paleta azul en `web-publica/src/index.css` (`--azul-oscuro`, `--azul-acento`…).
La app Android comparte esta misma identidad.

## GPX del recorrido

El GPX se sube por distancia desde el panel; el servidor lo procesa
(`api/app/servicios/gpx.py`) y guarda su `bbox` para centrar el mapa. La semilla
carga `api/seed/rutas/villacabra-11k.gpx` en la distancia "Villacabra 11K".

Ver también: [IngestaDePosiciones](IngestaDePosiciones.md).
