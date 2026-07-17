from pydantic import BaseModel


class ImportacionFila(BaseModel):
    fila: int
    email: str | None
    dorsal: str | None
    estado: str  # "creado" | "actualizado" | "sin_cambios" | "error"
    motivo: str | None = None


class ImportacionResultado(BaseModel):
    total_filas: int
    creados: int
    actualizados: int
    sin_cambios: int
    errores: int
    filas: list[ImportacionFila]
