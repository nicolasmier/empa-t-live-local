"""Espaciado inicial entre corredores para simulaciones de demostración.

Por defecto el simulador arranca todos los corredores desde el punto 0 del
GPX (pensado para el test de carga de S4). Para comprobar visualmente el
recorrido en el mapa interesa que no salgan todos apilados en el mismo punto,
sino repartidos como en una salida real.
"""

from __future__ import annotations

import random


def generar_offsets_km(
    n: int, espaciado_min_m: float, espaciado_max_m: float
) -> list[float]:
    """Distancia inicial (km) de cada corredor sobre la ruta.

    El primer corredor sale desde el punto 0; cada siguiente se coloca un
    hueco aleatorio (`espaciado_min_m`-`espaciado_max_m` metros) por delante
    del anterior, acumulado. Con `espaciado_max_m == 0` todos arrancan en el
    punto 0 (comportamiento original, usado por el test de carga S4).
    """
    offsets_km = [0.0]
    acumulado_m = 0.0
    for _ in range(1, n):
        if espaciado_max_m > 0:
            acumulado_m += random.uniform(espaciado_min_m, espaciado_max_m)
        offsets_km.append(acumulado_m / 1000.0)
    return offsets_km
