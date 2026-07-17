import jwt as pyjwt
from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.database import get_db
from app.errores import ErrorAPI
from app.models import Corredor, Inscripcion, TokenDispositivo, Usuario
from app.security.tokens import decodificar_token, hash_token_dispositivo


def _extraer_token(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise ErrorAPI(401, "no_autenticado", "Falta el token de autenticación.")
    return authorization.split(" ", 1)[1]


def obtener_usuario_panel(
    authorization: str | None = Header(default=None), db: Session = Depends(get_db)
) -> Usuario:
    token = _extraer_token(authorization)
    try:
        payload = decodificar_token(token)
    except pyjwt.PyJWTError as exc:
        raise ErrorAPI(401, "token_invalido", "El token no es válido o ha expirado.") from exc
    if payload.get("tipo") != "panel":
        raise ErrorAPI(401, "token_invalido", "El token no corresponde a una sesión de panel.")
    usuario = db.get(Usuario, int(payload["sub"]))
    if usuario is None:
        raise ErrorAPI(401, "token_invalido", "El usuario del token ya no existe.")
    return usuario


def requiere_panel(usuario: Usuario = Depends(obtener_usuario_panel)) -> Usuario:
    """Cualquier usuario de panel autenticado (Admin u Operador): acceso de lectura."""
    return usuario


def requiere_admin(usuario: Usuario = Depends(obtener_usuario_panel)) -> Usuario:
    """Solo Admin: acciones de escritura (Anexo E, matriz de permisos)."""
    if usuario.rol != "admin":
        raise ErrorAPI(403, "prohibido", "Esta acción requiere el rol de administrador.")
    return usuario


def obtener_corredor_actual(
    authorization: str | None = Header(default=None), db: Session = Depends(get_db)
) -> Corredor:
    token = _extraer_token(authorization)
    try:
        payload = decodificar_token(token)
    except pyjwt.PyJWTError as exc:
        raise ErrorAPI(401, "token_invalido", "El token no es válido o ha expirado.") from exc
    if payload.get("tipo") != "corredor":
        raise ErrorAPI(401, "token_invalido", "El token no corresponde a una sesión de corredor.")
    corredor = db.get(Corredor, int(payload["sub"]))
    if corredor is None:
        raise ErrorAPI(401, "token_invalido", "El corredor del token ya no existe.")
    return corredor


def obtener_inscripcion_por_token_dispositivo(
    authorization: str | None = Header(default=None), db: Session = Depends(get_db)
) -> Inscripcion:
    """Token de dispositivo (Anexo B §3): alcance limitado a `/posiciones` y `/estado`.

    No es JWT: es un secreto opaco de alta entropía, verificado por comparación de
    hash contra `tokens_dispositivo` (corrección v9: nunca se guarda en claro).
    """
    token = _extraer_token(authorization)
    token_hash = hash_token_dispositivo(token)
    fila = (
        db.query(TokenDispositivo)
        .filter(
            TokenDispositivo.token_hash == token_hash, TokenDispositivo.revocado_en.is_(None)
        )
        .one_or_none()
    )
    if fila is None:
        raise ErrorAPI(
            401, "token_invalido", "El token de dispositivo no es válido o ha sido revocado."
        )
    return fila.inscripcion
