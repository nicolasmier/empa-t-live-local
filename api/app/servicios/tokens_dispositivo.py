from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Distancia, Inscripcion, TokenDispositivo


def revocar_tokens_dispositivo_evento(db: Session, evento_id: int) -> int:
    """Revocación masiva al pasar a Finalizado (spec v10 §11).

    Los tokens revocados no se reactivan si el evento retrocede a En directo
    (decisión clarify 2026-07-16): al no existir aquí ninguna ruta de
    reactivación, esa regla se cumple por diseño.
    """
    inscripcion_ids = select(Inscripcion.id).join(Distancia).where(Distancia.evento_id == evento_id)
    ahora = datetime.now(UTC)
    return (
        db.query(TokenDispositivo)
        .filter(TokenDispositivo.inscripcion_id.in_(inscripcion_ids))
        .filter(TokenDispositivo.revocado_en.is_(None))
        .update({TokenDispositivo.revocado_en: ahora}, synchronize_session=False)
    )
