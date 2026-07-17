from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.inscripcion import Inscripcion


class PosicionActual(Base):
    __tablename__ = "posiciones_actuales"

    inscripcion_id: Mapped[int] = mapped_column(ForeignKey("inscripciones.id"), primary_key=True)
    timestamp_dispositivo: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    timestamp_recepcion: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    latitud: Mapped[float] = mapped_column(Numeric(9, 6))
    longitud: Mapped[float] = mapped_column(Numeric(9, 6))
    precision_m: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    velocidad_kmh: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    bateria_pct: Mapped[int | None] = mapped_column(Integer, nullable=True)

    inscripcion: Mapped["Inscripcion"] = relationship(back_populates="posicion_actual")
