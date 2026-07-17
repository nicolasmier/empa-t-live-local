from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.evento import Evento


class Patrocinador(Base):
    __tablename__ = "patrocinadores"

    id: Mapped[int] = mapped_column(primary_key=True)
    evento_id: Mapped[int] = mapped_column(ForeignKey("eventos.id"))
    nombre: Mapped[str] = mapped_column(String(200))
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    enlace_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    orden: Mapped[int] = mapped_column(Integer, server_default="0")

    evento: Mapped["Evento"] = relationship(back_populates="patrocinadores")
