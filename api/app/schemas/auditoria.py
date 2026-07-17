from datetime import datetime
from typing import Any

from pydantic import BaseModel


class AuditoriaSalida(BaseModel):
    id: int
    usuario_id: int
    accion: str
    entidad_tipo: str
    entidad_id: str
    detalle: dict[str, Any] | None
    creado_en: datetime

    model_config = {"from_attributes": True}
