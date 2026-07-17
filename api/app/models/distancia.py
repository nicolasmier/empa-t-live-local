from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.evento import Evento
    from app.models.inscripcion import Inscripcion


class Distancia(Base):
    __tablename__ = "distancias"

    id: Mapped[int] = mapped_column(primary_key=True)
    evento_id: Mapped[int] = mapped_column(ForeignKey("eventos.id"))
    nombre: Mapped[str] = mapped_column(String(100))
    gpx_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    mapa_config: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    evento: Mapped["Evento"] = relationship(back_populates="distancias")
    inscripciones: Mapped[list["Inscripcion"]] = relationship(back_populates="distancia")
