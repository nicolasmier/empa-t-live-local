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


class LoginCorredorEntrada(BaseModel):
    email: EmailStr
    password: str


class SesionSalida(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expira_en: datetime
