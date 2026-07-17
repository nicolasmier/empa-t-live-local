from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.evento import Evento
    from app.models.inscripcion import Inscripcion


class Incidencia(Base):
    __tablename__ = "incidencias"

    id: Mapped[int] = mapped_column(primary_key=True)
    evento_id: Mapped[int] = mapped_column(ForeignKey("eventos.id"))
    # Sin inscripcion_id: incidencia sistémica (p. ej. caída del servidor).
    inscripcion_id: Mapped[int | None] = mapped_column(
        ForeignKey("inscripciones.id"), nullable=True
    )
    tipo: Mapped[str] = mapped_column(String(50))
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    resuelto_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    evento: Mapped["Evento"] = relationship(back_populates="incidencias")
    inscripcion: Mapped["Inscripcion | None"] = relationship(back_populates="incidencias")
