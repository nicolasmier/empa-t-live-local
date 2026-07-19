from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.inscripcion import Inscripcion


class Corredor(Base):
    __tablename__ = "corredores"
    __table_args__ = (
        CheckConstraint(
            "email IS NOT NULL OR telefono IS NOT NULL", name="ck_corredores_email_o_telefono"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(200))
    apellidos: Mapped[str] = mapped_column(String(200))
    club: Mapped[str | None] = mapped_column(String(200), nullable=True)
    foto_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # email/telefono: identificadores alternativos para el matching Excel↔cuenta
    # (decisión 2026-07-19 — antes solo email, y un email mal escrito en el Excel o
    # en el registro dejaba la inscripción huérfana sin forma de recuperarla). Al
    # menos uno de los dos es obligatorio (CHECK arriba); el email sigue siendo el
    # único que sirve para iniciar sesión (`POST /auth/corredores/login`), así que
    # una cuenta pre-importada solo con teléfono no puede loguearse hasta que el
    # corredor complete el registro y aporte un email.
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    telefono: Mapped[str | None] = mapped_column(String(30), unique=True, nullable=True)
    # NULL = cuenta pre-importada desde Excel, aún sin activar por el corredor en la app
    # (spec v10 Anexo B §4: "si el email no existe, se crea la cuenta"; sin contraseña
    # hasta que el corredor complete el registro con ese mismo email).
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    inscripciones: Mapped[list["Inscripcion"]] = relationship(back_populates="corredor")
