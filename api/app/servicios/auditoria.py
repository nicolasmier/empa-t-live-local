from typing import Any

from sqlalchemy.orm import Session

from app.models import Auditoria


def registrar_auditoria(
    db: Session,
    usuario_id: int,
    accion: str,
    entidad_tipo: str,
    entidad_id: str,
    detalle: dict[str, Any] | None = None,
) -> None:
    """Registra toda escritura de gestión (spec v10 §12: auditoría transversal)."""
    db.add(
        Auditoria(
            usuario_id=usuario_id,
            accion=accion,
            entidad_tipo=entidad_tipo,
            entidad_id=entidad_id,
            detalle=detalle,
        )
    )
