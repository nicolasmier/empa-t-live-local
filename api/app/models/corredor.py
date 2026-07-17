from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.inscripcion import Inscripcion


class Corredor(Base):
    __tablename__ = "corredores"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(200))
    apellidos: Mapped[str] = mapped_column(String(200))
    club: Mapped[str | None] = mapped_column(String(200), nullable=True)
    foto_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    # NULL = cuenta pre-importada desde Excel, aún sin activar por el corredor en la app
    # (spec v10 Anexo B §4: "si el email no existe, se crea la cuenta"; sin contraseña
    # hasta que el corredor complete el registro con ese mismo email).
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    inscripciones: Mapped[list["Inscripcion"]] = relationship(back_populates="corredor")
