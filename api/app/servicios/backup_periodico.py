"""Backup periódico durante En directo (Anexo D: cada 30 min, `settings.backup_intervalo_min`)."""

import logging

from app.database import SessionLocal
from app.models import Evento
from app.servicios.auditoria import registrar_auditoria
from app.servicios.pg_dump import generar_backup

logger = logging.getLogger(__name__)


def respaldar_eventos_en_directo() -> None:
    db = SessionLocal()
    try:
        eventos_activos = db.query(Evento).filter(Evento.estado == "en_directo").all()
        for evento in eventos_activos:
            try:
                ruta = generar_backup(evento.id)
                registrar_auditoria(
                    db,
                    evento.creado_por,
                    "backup_periodico_completado",
                    "evento",
                    str(evento.id),
                    detalle={"ruta": str(ruta)},
                )
            except Exception as exc:
                logger.exception("Backup periódico fallido para evento %s", evento.id)
                registrar_auditoria(
                    db,
                    evento.creado_por,
                    "backup_periodico_fallido",
                    "evento",
                    str(evento.id),
                    detalle={"error": str(exc)[:500]},
                )
        db.commit()
    finally:
        db.close()
