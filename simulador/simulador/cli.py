"""CLI del simulador (plan S4): genera N corredores virtuales que envían posiciones
reales a la API real, para probar el pipeline de ingesta a escala sin depender de
móviles físicos ni de la app Android.
"""

from __future__ import annotations

import argparse
import asyncio
import io
import random
import time
import uuid
from datetime import date, timedelta

from openpyxl import Workbook

from simulador.api_cliente import ClienteAPI
from simulador.config import ConfiguracionSimulacion
from simulador.corredor_virtual import EstadisticasRunner, simular_corredor
from simulador.espaciado import generar_offsets_km
from simulador.ruta import cargar_ruta


def _parsear_args() -> ConfiguracionSimulacion:
    parser = argparse.ArgumentParser(
        description="Simulador de corredores para EmpateLive (spec v10, plan S4)."
    )
    parser.add_argument("--api-url", default="http://localhost:8000")
    parser.add_argument("--gpx", required=True, help="Ruta al fichero GPX del recorrido")
    parser.add_argument("--corredores", type=int, default=800)
    parser.add_argument("--duracion-min", type=float, default=30.0)
    parser.add_argument("--perdida-cobertura", type=float, default=0.10)
    parser.add_argument("--reloj-desviado", type=float, default=0.02)
    parser.add_argument("--admin-email", default="admin@example.com")
    parser.add_argument("--admin-password", default="admin1234")
    parser.add_argument(
        "--codigo-evento",
        default=None,
        help="Reutiliza un evento existente por su código en vez de crear uno nuevo",
    )
    parser.add_argument(
        "--factor-aceleracion",
        type=float,
        default=8.0,
        help="Comprime el tiempo simulado (8.0 = 30 min simulados en ~4 min reales)",
    )
    parser.add_argument(
        "--espaciado-min-m",
        type=float,
        default=0.0,
        help="Hueco mínimo (metros) entre la salida de un corredor y el siguiente",
    )
    parser.add_argument(
        "--espaciado-max-m",
        type=float,
        default=0.0,
        help="Hueco máximo (metros) entre corredores; 0 = todos salen del punto 0 (por defecto)",
    )
    args = parser.parse_args()
    return ConfiguracionSimulacion(
        api_url=args.api_url,
        gpx=args.gpx,
        corredores=args.corredores,
        duracion_min=args.duracion_min,
        perdida_cobertura=args.perdida_cobertura,
        reloj_desviado=args.reloj_desviado,
        admin_email=args.admin_email,
        admin_password=args.admin_password,
        codigo_evento=args.codigo_evento or f"SIM-{uuid.uuid4().hex[:8].upper()}",
        factor_aceleracion=args.factor_aceleracion,
        espaciado_min_m=args.espaciado_min_m,
        espaciado_max_m=args.espaciado_max_m,
    )


def _excel_corredores(n: int, sufijo: str) -> bytes:
    libro = Workbook()
    hoja = libro.active
    hoja.append(["email", "nombre", "apellidos", "dorsal", "club"])
    for i in range(1, n + 1):
        hoja.append(
            [f"sim-{sufijo}-{i:04d}@example.com", f"Corredor{i:04d}", "Simulado", 1000 + i, None]
        )
    buffer = io.BytesIO()
    libro.save(buffer)
    return buffer.getvalue()


async def _preparar_evento(
    cliente: ClienteAPI, cfg: ConfiguracionSimulacion, contenido_gpx: bytes
) -> tuple[int, str, str]:
    token_admin = await cliente.login_admin(cfg.admin_email, cfg.admin_password)
    evento = await cliente.crear_evento(
        token_admin,
        nombre=f"Simulación {cfg.codigo_evento}",
        codigo_acceso=cfg.codigo_evento,
        fecha=str(date.today() + timedelta(days=1)),
    )
    distancia = await cliente.crear_distancia(token_admin, evento["id"], "Simulada")
    await cliente.subir_gpx(token_admin, distancia["id"], contenido_gpx)

    sufijo = uuid.uuid4().hex[:6]
    excel = _excel_corredores(cfg.corredores, sufijo)
    informe = await cliente.importar_corredores(token_admin, distancia["id"], excel)
    print(f"Importación: {informe['creados']} creados, {informe['errores']} errores.")

    await cliente.cambiar_estado_evento(token_admin, evento["id"], "publicado")
    return evento["id"], sufijo, token_admin


async def _unir_corredores(
    cliente: ClienteAPI, cfg: ConfiguracionSimulacion, sufijo: str
) -> list[str]:
    semaforo = asyncio.Semaphore(50)
    tokens: list[str] = [""] * cfg.corredores

    async def _unir_uno(i: int) -> None:
        async with semaforo:
            email = f"sim-{sufijo}-{i + 1:04d}@example.com"
            token_corredor = await cliente.registro_corredor(
                email, "simulado1234", f"Corredor{i + 1:04d}", "Simulado"
            )
            # El dorsal debe coincidir con el que se escribió en `_excel_corredores`
            # para este mismo corredor (1000 + posición en el Excel, 1-indexado):
            # desde que `unirse` exige confirmación de dorsal (decisión 2026-07-19),
            # el simulador tiene que "saberlo" igual que lo sabría un corredor real
            # mirando su dorsal de papel.
            union = await cliente.unirse(token_corredor, cfg.codigo_evento, str(1000 + i + 1))
            tokens[i] = union["token_dispositivo"]

    await asyncio.gather(*(_unir_uno(i) for i in range(cfg.corredores)))
    return tokens


def _elegir_desviacion_reloj_seg() -> float:
    # Mezcla de casos: reloj un poco atrasado (sincronizado, no sospechoso), muy
    # atrasado o adelantado (sospechoso) y ligeramente adelantado (aún directo).
    return random.choice([-900.0, -300.0, 300.0, 900.0])


async def main_async() -> None:
    cfg = _parsear_args()
    ruta = cargar_ruta(cfg.gpx)
    with open(cfg.gpx, "rb") as f:
        contenido_gpx = f.read()

    cliente = ClienteAPI(cfg.api_url)
    try:
        evento_id, sufijo, token_admin = await _preparar_evento(cliente, cfg, contenido_gpx)
        print(
            f"Evento {cfg.codigo_evento} (id={evento_id}) listo. "
            f"Uniendo {cfg.corredores} corredores..."
        )
        tokens_dispositivo = await _unir_corredores(cliente, cfg, sufijo)

        await cliente.cambiar_estado_evento(token_admin, evento_id, "preparacion")
        await cliente.cambiar_estado_evento(token_admin, evento_id, "en_directo")
        print("Evento En directo. Comenzando la simulación...")

        duracion_seg = cfg.duracion_min * 60
        n_perdida = int(cfg.corredores * cfg.perdida_cobertura)
        n_desviado = int(cfg.corredores * cfg.reloj_desviado)
        indices_perdida = (
            set(random.sample(range(cfg.corredores), n_perdida)) if n_perdida else set()
        )
        indices_desviado = (
            set(random.sample(range(cfg.corredores), n_desviado)) if n_desviado else set()
        )

        offsets_km = generar_offsets_km(
            cfg.corredores, cfg.espaciado_min_m, cfg.espaciado_max_m
        )
        stats = [EstadisticasRunner() for _ in range(cfg.corredores)]
        inicio = time.monotonic()
        tareas = [
            simular_corredor(
                cliente=cliente,
                evento_id=evento_id,
                token_dispositivo=tokens_dispositivo[i],
                ruta=ruta,
                duracion_seg=duracion_seg,
                con_perdida_cobertura=i in indices_perdida,
                desviacion_reloj_seg=(
                    _elegir_desviacion_reloj_seg() if i in indices_desviado else 0.0
                ),
                factor_aceleracion=cfg.factor_aceleracion,
                stats=stats[i],
                offset_inicial_km=offsets_km[i],
            )
            for i in range(cfg.corredores)
        ]
        await asyncio.gather(*tareas)
        transcurrido = time.monotonic() - inicio

        total_puntos = sum(s.puntos_enviados for s in stats)
        total_lotes = sum(s.lotes_enviados for s in stats)
        total_5xx = sum(s.errores_5xx for s in stats)
        total_otros = sum(s.errores_otros for s in stats)

        print("\n--- Resumen de la simulación ---")
        print(f"Duración real: {transcurrido:.1f} s (simulados {cfg.duracion_min} min)")
        print(
            f"Corredores: {cfg.corredores} "
            f"(pérdida cobertura: {n_perdida}, reloj desviado: {n_desviado})"
        )
        print(f"Puntos enviados: {total_puntos}  |  Lotes: {total_lotes}")
        print(f"Errores 5xx: {total_5xx}  |  Otros errores: {total_otros}")
        print("RESULTADO: FALLO (hubo errores 5xx)" if total_5xx else "RESULTADO: OK")
    finally:
        await cliente.cerrar()


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
