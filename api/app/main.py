from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import anyio
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.almacenamiento import directorio_storage
from app.config import settings
from app.database import engine
from app.errores import registrar_manejadores_error
from app.routers import (
    auditoria,
    auth,
    contenido,
    corredores,
    corredores_admin,
    distancias,
    eventos,
    gpx,
    importacion,
    incidencias,
    operacion,
    posiciones,
)
from app.servicios.backup_periodico import respaldar_eventos_en_directo
from app.servicios.salida_programada import activar_salidas_programadas


@asynccontextmanager
async def _lifespan(_: FastAPI) -> AsyncIterator[None]:
    # Los endpoints son `def` síncronos y corren en el threadpool de AnyIO (límite
    # por defecto ~40); se iguala al pool de BD para no crear un cuello de botella
    # distinto bajo el pico de ingesta (spec §7, hallazgo de la FASE S4).
    limitador = anyio.to_thread.current_default_thread_limiter()
    limitador.total_tokens = settings.db_pool_size + settings.db_max_overflow

    scheduler = BackgroundScheduler()
    scheduler.add_job(
        respaldar_eventos_en_directo,
        "interval",
        minutes=settings.backup_intervalo_min,
        id="backup_periodico_en_directo",
    )
    scheduler.add_job(
        activar_salidas_programadas,
        "interval",
        seconds=settings.salida_programada_intervalo_seg,
        id="salida_programada",
    )
    scheduler.start()
    try:
        yield
    finally:
        scheduler.shutdown(wait=False)


app = FastAPI(title="EmpateLive API", version="0.1.0", lifespan=_lifespan)

# Panel y web pública son consumidores LAN de confianza (spec v10 Anexo E); la separación
# real de superficies se hace a nivel de túnel/proxy, no de CORS (Anexo B §2).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

registrar_manejadores_error(app)

app.mount("/media", StaticFiles(directory=directorio_storage()), name="media")

app.include_router(auth.router)
app.include_router(eventos.router)
app.include_router(distancias.router)
app.include_router(auditoria.router)
app.include_router(importacion.router)
app.include_router(gpx.router)
app.include_router(contenido.router)
app.include_router(corredores.router)
app.include_router(corredores_admin.router)
app.include_router(posiciones.router)
app.include_router(operacion.router)
app.include_router(incidencias.router)


@app.get("/salud")
def salud() -> dict[str, str]:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"estado": "ok"}
