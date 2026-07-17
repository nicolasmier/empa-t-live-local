import threading

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.servicios.auditoria import registrar_auditoria
from app.servicios.pg_dump import generar_backup


def registrar_solicitud_backup(db: Session, usuario_id: int, evento_id: int, motivo: str) -> None:
    """Deja constancia en auditoría, dentro de la MISMA transacción que el cambio
    de estado. El backup físico se dispara aparte, después del commit (ver
    `disparar_backup_en_segundo_plano`), para no capturar datos aún no confirmados.
    """
    registrar_auditoria(
        db,
        usuario_id,
        "backup_solicitado",
        "evento",
        str(evento_id),
        detalle={"motivo": motivo},
    )


def _ejecutar_backup(evento_id: int, usuario_id: int) -> None:
    db = SessionLocal()
    try:
        ruta = generar_backup(evento_id)
        registrar_auditoria(
            db,
            usuario_id,
            "backup_completado",
            "evento",
            str(evento_id),
            detalle={"ruta": str(ruta)},
        )
        db.commit()
    except Exception as exc:
        db.rollback()
        registrar_auditoria(
            db,
            usuario_id,
            "backup_fallido",
            "evento",
            str(evento_id),
            detalle={"error": str(exc)[:500]},
        )
        db.commit()
    finally:
        db.close()


def disparar_backup_en_segundo_plano(usuario_id: int, evento_id: int) -> None:
    """Lanza el `pg_dump` real en un hilo aparte, sin bloquear la respuesta HTTP.

    Debe llamarse DESPUÉS de confirmar (`commit`) la transacción que originó el
    backup, para que el dump vea ya los datos confirmados (p. ej. el evento en
    Finalizado, no todavía En directo).
    """
    hilo = threading.Thread(target=_ejecutar_backup, args=(evento_id, usuario_id), daemon=True)
    hilo.start()
