from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.inscripcion import Inscripcion

# origen ∈ {directo, sincronizado} (spec v10, Anexo A notas por entidad).
ORIGENES_POSICION = ("directo", "sincronizado")
_valores_origen_sql = ", ".join(f"'{origen}'" for origen in ORIGENES_POSICION)


class PosicionHistorico(Base):
    __tablename__ = "posiciones_historico"
    __table_args__ = (
        CheckConstraint(
            f"origen IN ({_valores_origen_sql})", name="ck_posiciones_historico_origen"
        ),
        Index(
            "ix_posiciones_historico_inscripcion_timestamp",
            "inscripcion_id",
            "timestamp_dispositivo",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    inscripcion_id: Mapped[int] = mapped_column(ForeignKey("inscripciones.id"))
    timestamp_dispositivo: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    timestamp_recepcion: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    latitud: Mapped[float] = mapped_column(Numeric(9, 6))
    longitud: Mapped[float] = mapped_column(Numeric(9, 6))
    precision_m: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    velocidad_kmh: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    bateria_pct: Mapped[int | None] = mapped_column(Integer, nullable=True)
    origen: Mapped[str] = mapped_column(String(20))
    sospechoso: Mapped[bool] = mapped_column(Boolean, server_default="false")

    inscripcion: Mapped["Inscripcion"] = relationship(back_populates="posiciones_historico")
