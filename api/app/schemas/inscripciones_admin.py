from pydantic import BaseModel


class InscripcionActualizar(BaseModel):
    dorsal: str | None = None
    nombre: str | None = None
    apellidos: str | None = None
    club: str | None = None


class InscripcionCrear(BaseModel):
    """Alta individual de un corredor en una distancia desde el panel (para los
    que se quedaron sin importar por Excel o para pruebas). Mismas reglas que la
    importación (Anexo B §4, decisión 2026-07-19): nombre/apellidos/dorsal
    obligatorios y al menos uno de email/telefono."""

    dorsal: str
    nombre: str
    apellidos: str
    club: str | None = None
    email: str | None = None
    telefono: str | None = None


class EliminarInscripcionesEntrada(BaseModel):
    inscripcion_ids: list[int]


class EliminarInscripcionesSalida(BaseModel):
    eliminadas: int
