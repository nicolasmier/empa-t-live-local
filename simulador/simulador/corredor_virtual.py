"""Simula un corredor real: avanza sobre la ruta y genera puntos a ritmos realistas
(RF-009: caminando/corriendo 15-20 s), con pérdida de cobertura y reloj desviado opcionales.

Los puntos se acumulan en una cola y solo se envían cuando ha pasado suficiente
tiempo REAL desde el último envío de ese dispositivo (Anexo B §7: 1 petición / 5 s).
Con `--factor-aceleracion` el ritmo simulado se comprime, así que el envío deja de
ser "un punto por petición" y pasa a agrupar varios puntos por lote — igual que
haría cualquier cliente que respete el límite del servidor.
"""

from __future__ import annotations

import asyncio
import os
import random
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx

from simulador.api_cliente import ClienteAPI
from simulador.ruta import Ruta

VELOCIDAD_MIN_KMH = 9.0
VELOCIDAD_MAX_KMH = 15.0
INTERVALO_MIN_SEG = 15
INTERVALO_MAX_SEG = 20
# Margen sobre el límite real del servidor (5 s): con muchos corredores concurrentes
# el bucle de eventos de asyncio introduce jitter, así que se deja holgura extra.
INTERVALO_MINIMO_ENVIO_SEG = 6.0
DEBUG = bool(os.environ.get("SIM_DEBUG"))


@dataclass
class EstadisticasRunner:
    puntos_enviados: int = 0
    lotes_enviados: int = 0
    errores_5xx: int = 0
    errores_otros: int = 0


async def simular_corredor(
    cliente: ClienteAPI,
    evento_id: int,
    token_dispositivo: str,
    ruta: Ruta,
    duracion_seg: float,
    con_perdida_cobertura: bool,
    desviacion_reloj_seg: float,
    factor_aceleracion: float,
    stats: EstadisticasRunner,
    offset_inicial_km: float = 0.0,
) -> None:
    velocidad_kmh = random.uniform(VELOCIDAD_MIN_KMH, VELOCIDAD_MAX_KMH)
    distancia_km = offset_inicial_km
    tiempo_transcurrido = 0.0

    # Ventana de pérdida de cobertura: un tramo aleatorio de 1-3 min de la carrera.
    perdida_inicio = random.uniform(0.2, 0.7) * duracion_seg if con_perdida_cobertura else None
    perdida_duracion = random.uniform(60, 180) if con_perdida_cobertura else 0.0
    cola_pendiente: list[dict[str, Any]] = []
    ultimo_envio = 0.0

    while tiempo_transcurrido < duracion_seg and distancia_km < ruta.distancia_total_km:
        intervalo = random.uniform(INTERVALO_MIN_SEG, INTERVALO_MAX_SEG)
        tiempo_transcurrido += intervalo
        distancia_km += velocidad_kmh * (intervalo / 3600)
        lat, lon = ruta.punto_en_distancia(distancia_km)

        ts_dispositivo = datetime.now(UTC) + timedelta(seconds=desviacion_reloj_seg)
        bateria_pct = max(1, 100 - int(tiempo_transcurrido / duracion_seg * 60))
        cola_pendiente.append(
            {
                "timestamp_dispositivo": ts_dispositivo.isoformat(),
                "latitud": lat,
                "longitud": lon,
                "precision_m": round(random.uniform(3, 12), 1),
                "velocidad_kmh": round(velocidad_kmh, 1),
                "bateria_pct": bateria_pct,
            }
        )

        en_perdida = (
            con_perdida_cobertura
            and perdida_inicio is not None
            and perdida_inicio <= tiempo_transcurrido < perdida_inicio + perdida_duracion
        )
        tiempo_desde_ultimo_envio = time.monotonic() - ultimo_envio

        if not en_perdida and tiempo_desde_ultimo_envio >= INTERVALO_MINIMO_ENVIO_SEG:
            enviado = await _enviar_lote(
                cliente, evento_id, token_dispositivo, cola_pendiente, stats
            )
            if enviado:
                # Si falló (p. ej. 429 puntual bajo carga), se reintenta en el
                # siguiente ciclo en vez de perder los puntos silenciosamente.
                cola_pendiente = []
                ultimo_envio = time.monotonic()

        await asyncio.sleep(intervalo / factor_aceleracion)

    if cola_pendiente:
        await _enviar_lote(cliente, evento_id, token_dispositivo, cola_pendiente, stats)


async def _enviar_lote(
    cliente: ClienteAPI,
    evento_id: int,
    token_dispositivo: str,
    lote: list[dict[str, Any]],
    stats: EstadisticasRunner,
) -> bool:
    """Devuelve True si el lote se envió con éxito (2xx), False si hay que reintentarlo."""
    if not lote:
        return True
    try:
        respuesta = await cliente.enviar_posiciones(token_dispositivo, evento_id, lote)
    except httpx.HTTPError as exc:
        stats.errores_otros += 1
        if DEBUG:
            print("DEBUG excepcion", type(exc).__name__, str(exc)[:200])
        return False
    stats.lotes_enviados += 1
    if respuesta.status_code >= 500:
        stats.errores_5xx += 1
        return False
    if respuesta.status_code >= 400:
        stats.errores_otros += 1
        if DEBUG:
            print("DEBUG", respuesta.status_code, respuesta.text[:200])
        return False
    stats.puntos_enviados += len(lote)
    return True
