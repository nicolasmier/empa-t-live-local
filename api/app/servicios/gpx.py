"""Procesamiento de ficheros GPX: validación + bounding box (Anexo B §4).

Compartido entre el router de subida y el seed de desarrollo (que carga un
GPX real de ejemplo), para no duplicar la lógica de cálculo del bbox.
"""

import gpxpy


def procesar_gpx(contenido: bytes) -> dict:
    """Valida un GPX y calcula su bounding box. Lanza ValueError si no es válido."""
    try:
        gpx = gpxpy.parse(contenido)
    except Exception as exc:
        raise ValueError("El fichero GPX no es válido o está corrupto.") from exc

    puntos = [
        punto for pista in gpx.tracks for segmento in pista.segments for punto in segmento.points
    ]
    if not puntos:
        raise ValueError("El GPX no contiene ningún punto de recorrido (track).")

    return {
        "puntos": len(puntos),
        "bbox": {
            "norte": max(p.latitude for p in puntos),
            "sur": min(p.latitude for p in puntos),
            "este": max(p.longitude for p in puntos),
            "oeste": min(p.longitude for p in puntos),
        },
    }
