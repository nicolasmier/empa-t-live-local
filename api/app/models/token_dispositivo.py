from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.inscripcion import Inscripcion


class TokenDispositivo(Base):
    __tablename__ = "tokens_dispositivo"

    id: Mapped[int] = mapped_column(primary_key=True)
    inscripcion_id: Mapped[int] = mapped_column(ForeignKey("inscripciones.id"))
    # Se guarda el hash, nunca el token en claro (corrección v9).
    token_hash: Mapped[str] = mapped_column(String(255))
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    revocado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    inscripcion: Mapped["Inscripcion"] = relationship(back_populates="tokens_dispositivo")
