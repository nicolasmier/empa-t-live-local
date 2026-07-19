from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class LoginPanelEntrada(BaseModel):
    email: EmailStr
    password: str


class RegistroCorredorEntrada(BaseModel):
    nombre: str
    apellidos: str
    email: EmailStr
    password: str = Field(min_length=8)
    club: str | None = None
    # Opcional: si el organizador solo tenía el teléfono en el Excel (sin email o
    # con uno distinto al que el corredor usa aquí), aportarlo permite enlazar con
    # esa cuenta pre-importada en vez de crear un corredor duplicado sin
    # inscripción (decisión 2026-07-19).
    telefono: str | None = None


class LoginCorredorEntrada(BaseModel):
    email: EmailStr
    password: str


class SesionSalida(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expira_en: datetime
