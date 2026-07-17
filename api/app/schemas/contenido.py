from datetime import datetime

from pydantic import BaseModel


class PatrocinadorCrear(BaseModel):
    nombre: str
    logo_url: str | None = None
    enlace_url: str | None = None
    orden: int = 0


class PatrocinadorActualizar(BaseModel):
    nombre: str | None = None
    logo_url: str | None = None
    enlace_url: str | None = None
    orden: int | None = None


class PatrocinadorSalida(BaseModel):
    id: int
    evento_id: int
    nombre: str
    logo_url: str | None
    enlace_url: str | None
    orden: int

    model_config = {"from_attributes": True}


class NoticiaCrear(BaseModel):
    titulo: str
    contenido: str


class NoticiaActualizar(BaseModel):
    titulo: str | None = None
    contenido: str | None = None


class NoticiaSalida(BaseModel):
    id: int
    evento_id: int
    titulo: str
    contenido: str
    publicado_en: datetime

    model_config = {"from_attributes": True}
