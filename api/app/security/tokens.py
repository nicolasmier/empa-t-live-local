import hashlib
import secrets
from datetime import UTC, datetime, timedelta

import jwt

from app.config import settings

ALGORITMO = "HS256"

# Duraciones de sesión (decisión clarify 2026-07-16, spec v10 Anexo B §3).
TTL_SESION_PANEL = timedelta(hours=12)
TTL_SESION_CORREDOR = timedelta(days=30)


def _crear_token(
    sub: str, tipo: str, ttl: timedelta, claims_extra: dict | None = None
) -> tuple[str, datetime]:
    ahora = datetime.now(UTC)
    expira = ahora + ttl
    payload = {
        "sub": sub,
        "tipo": tipo,
        "iat": int(ahora.timestamp()),
        "exp": int(expira.timestamp()),
    }
    if claims_extra:
        payload.update(claims_extra)
    token = jwt.encode(payload, settings.secret_key, algorithm=ALGORITMO)
    return token, expira


def crear_token_sesion_panel(usuario_id: int, rol: str) -> tuple[str, datetime]:
    return _crear_token(str(usuario_id), "panel", TTL_SESION_PANEL, {"rol": rol})


def crear_token_sesion_corredor(corredor_id: int) -> tuple[str, datetime]:
    return _crear_token(str(corredor_id), "corredor", TTL_SESION_CORREDOR)


def decodificar_token(token: str) -> dict:
    return jwt.decode(token, settings.secret_key, algorithms=[ALGORITMO])


def generar_token_dispositivo() -> str:
    return secrets.token_urlsafe(32)


def hash_token_dispositivo(token: str) -> str:
    # Alta entropía (256 bits): un hash rápido basta, a diferencia de las contraseñas
    # de usuario (Anexo E, corrección v9: "se almacena el hash, nunca el token en claro").
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
