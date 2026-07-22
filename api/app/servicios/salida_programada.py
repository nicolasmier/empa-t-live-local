"""Salida programada: pasa a En directo automáticamente los eventos en
Preparación cuya `hora_programada_directo` ya se ha cumplido (comparada
contra el reloj del propio servidor, no el del navegador del Administrador)."""

import logging
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Evento
from app.servicios.auditoria import registrar_auditoria

logger = logging.getLogger(__name__)


def activar_salidas_programadas(db: Session | None = None) -> None:
    """`db=None` (uso real, vía el scheduler) abre y cierra su propia sesión,
    igual que `respaldar_eventos_en_directo`; los tests inyectan `db_session`
    para poder ver los cambios hechos por el `TestClient` en la misma
    transacción de prueba (que nunca llega a un commit real)."""
    db_propia = db is None
    if db is None:
        db = SessionLocal()
    try:
        ahora = datetime.now(UTC)
        pendientes = (
            db.query(Evento)
            .filter(
                Evento.estado == "preparacion",
                Evento.hora_programada_directo.isnot(None),
                Evento.hora_programada_directo <= ahora,
            )
            .all()
        )
        for evento in pendientes:
            hora_programada = evento.hora_programada_directo
            evento.estado = "en_directo"
            evento.hora_programada_directo = None
            # Marca de inicio para el cronómetro de la web (se refresca en cada
            # entrada a En directo, ver Evento.inicio_directo).
            evento.inicio_directo = ahora
            registrar_auditoria(
                db,
                evento.creado_por,
                "evento_salida_automatica",
                "evento",
                str(evento.id),
                detalle={"hora_programada": hora_programada.isoformat() if hora_programada else None},
            )
            logger.info("Evento %s pasado a En directo por salida programada", evento.id)
        db.commit()
    finally:
        if db_propia:
            db.close()
