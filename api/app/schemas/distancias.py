from typing import Any

from pydantic import BaseModel


class DistanciaCrear(BaseModel):
    nombre: str


class DistanciaActualizar(BaseModel):
    nombre: str | None = None
    gpx_url: str | None = None
    mapa_config: dict[str, Any] | None = None


class DistanciaSalida(BaseModel):
    id: int
    evento_id: int
    nombre: str
    gpx_url: str | None
    mapa_config: dict[str, Any] | None

    model_config = {"from_attributes": True}
