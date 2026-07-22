from datetime import date, datetime
from typing import Any

from pydantic import BaseModel


class EventoCrear(BaseModel):
    nombre: str
    codigo_acceso: str
    fecha: date


class EventoActualizar(BaseModel):
    nombre: str | None = None
    codigo_acceso: str | None = None
    fecha: date | None = None
    intervalo_gps_parado_seg: int | None = None
    intervalo_gps_movimiento_seg: int | None = None
    umbral_sin_senal_seg: int | None = None
    colores_config: dict[str, Any] | None = None
    info_visible_config: dict[str, Any] | None = None
    cartel_url: str | None = None
    hora_programada_directo: datetime | None = None


class CambioEstadoEntrada(BaseModel):
    estado: str


class EventoSalida(BaseModel):
    id: int
    nombre: str
    codigo_acceso: str
    fecha: date
    estado: str
    intervalo_gps_parado_seg: int
    intervalo_gps_movimiento_seg: int
    umbral_sin_senal_seg: int
    colores_config: dict[str, Any] | None
    info_visible_config: dict[str, Any] | None
    cartel_url: str | None
    hora_programada_directo: datetime | None
    inicio_directo: datetime | None
    creado_por: int
    creado_en: datetime

    model_config = {"from_attributes": True}
