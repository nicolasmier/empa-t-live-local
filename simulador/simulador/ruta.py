"""Carga un GPX y permite interpolar un punto (lat, lon) a una distancia dada del inicio."""

from __future__ import annotations

import math
from dataclasses import dataclass

import gpxpy


@dataclass
class Ruta:
    puntos: list[tuple[float, float]]  # (lat, lon)
    distancias_acumuladas_km: list[float]

    @property
    def distancia_total_km(self) -> float:
        return self.distancias_acumuladas_km[-1]

    def punto_en_distancia(self, distancia_km: float) -> tuple[float, float]:
        distancia_km = max(0.0, min(distancia_km, self.distancia_total_km))
        for i in range(1, len(self.distancias_acumuladas_km)):
            if self.distancias_acumuladas_km[i] >= distancia_km:
                d0 = self.distancias_acumuladas_km[i - 1]
                d1 = self.distancias_acumuladas_km[i]
                frac = 0.0 if d1 == d0 else (distancia_km - d0) / (d1 - d0)
                lat0, lon0 = self.puntos[i - 1]
                lat1, lon1 = self.puntos[i]
                return (lat0 + (lat1 - lat0) * frac, lon0 + (lon1 - lon0) * frac)
        return self.puntos[-1]


def _haversine_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    radio_tierra_km = 6371.0
    lat1, lon1 = math.radians(a[0]), math.radians(a[1])
    lat2, lon2 = math.radians(b[0]), math.radians(b[1])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * radio_tierra_km * math.asin(math.sqrt(h))


def cargar_ruta(ruta_gpx: str) -> Ruta:
    with open(ruta_gpx, encoding="utf-8") as f:
        gpx = gpxpy.parse(f)
    puntos = [
        (p.latitude, p.longitude)
        for pista in gpx.tracks
        for segmento in pista.segments
        for p in segmento.points
    ]
    if len(puntos) < 2:
        raise ValueError("El GPX debe contener al menos dos puntos de recorrido.")

    acumulado = [0.0]
    for i in range(1, len(puntos)):
        acumulado.append(acumulado[-1] + _haversine_km(puntos[i - 1], puntos[i]))
    return Ruta(puntos=puntos, distancias_acumuladas_km=acumulado)
