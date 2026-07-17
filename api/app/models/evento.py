from datetime import date, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.distancia import Distancia
    from app.models.incidencia import Incidencia
    from app.models.noticia import Noticia
    from app.models.patrocinador import Patrocinador
    from app.models.usuario import Usuario

# Máquina de estados (spec v10 §11): avance en orden, retroceso de un paso salvo desde Archivado.
ESTADOS_EVENTO = ("borrador", "publicado", "preparacion", "en_directo", "finalizado", "archivado")
_valores_estado_sql = ", ".join(f"'{estado}'" for estado in ESTADOS_EVENTO)


class Evento(Base):
    __tablename__ = "eventos"
    __table_args__ = (
        CheckConstraint(f"estado IN ({_valores_estado_sql})", name="ck_eventos_estado"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(200))
    codigo_acceso: Mapped[str] = mapped_column(String(50), unique=True)
    fecha: Mapped[date] = mapped_column(Date)
    estado: Mapped[str] = mapped_column(String(20), server_default="borrador")
    intervalo_gps_parado_seg: Mapped[int] = mapped_column(Integer, server_default="90")
    intervalo_gps_movimiento_seg: Mapped[int] = mapped_column(Integer, server_default="20")
    umbral_sin_senal_seg: Mapped[int] = mapped_column(Integer, server_default="180")
    colores_config: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    info_visible_config: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    cartel_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # Salida programada: si está en Preparación y llega esta hora, un job en
    # segundo plano pasa el evento a En directo automáticamente (ver
    # app/servicios/salida_programada.py). Se guarda con zona horaria (UTC en
    # BD); la hora de referencia para dispararlo es la del propio servidor.
    hora_programada_directo: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    creado_por: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    creador: Mapped["Usuario"] = relationship(back_populates="eventos_creados")
    distancias: Mapped[list["Distancia"]] = relationship(back_populates="evento")
    patrocinadores: Mapped[list["Patrocinador"]] = relationship(back_populates="evento")
    noticias: Mapped[list["Noticia"]] = relationship(back_populates="evento")
    incidencias: Mapped[list["Incidencia"]] = relationship(back_populates="evento")
