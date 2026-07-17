from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.corredor import Corredor
    from app.models.distancia import Distancia
    from app.models.incidencia import Incidencia
    from app.models.posicion_actual import PosicionActual
    from app.models.posicion_historico import PosicionHistorico
    from app.models.token_dispositivo import TokenDispositivo


class Inscripcion(Base):
    __tablename__ = "inscripciones"
    __table_args__ = (
        # El dorsal es único por distancia, no globalmente (spec v10, Anexo A).
        UniqueConstraint("distancia_id", "dorsal", name="uq_inscripciones_distancia_dorsal"),
        UniqueConstraint("corredor_id", "distancia_id", name="uq_inscripciones_corredor_distancia"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    corredor_id: Mapped[int] = mapped_column(ForeignKey("corredores.id"))
    distancia_id: Mapped[int] = mapped_column(ForeignKey("distancias.id"))
    dorsal: Mapped[str] = mapped_column(String(20))
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    corredor: Mapped["Corredor"] = relationship(back_populates="inscripciones")
    distancia: Mapped["Distancia"] = relationship(back_populates="inscripciones")
    posicion_actual: Mapped["PosicionActual | None"] = relationship(
        back_populates="inscripcion", uselist=False
    )
    posiciones_historico: Mapped[list["PosicionHistorico"]] = relationship(
        back_populates="inscripcion"
    )
    tokens_dispositivo: Mapped[list["TokenDispositivo"]] = relationship(
        back_populates="inscripcion"
    )
    incidencias: Mapped[list["Incidencia"]] = relationship(back_populates="inscripcion")
