from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, VerifyMismatchError

# Parámetros mínimos recomendados por OWASP (decisión clarify 2026-07-16, spec v10 Anexo E).
hasher = PasswordHasher(memory_cost=19 * 1024, time_cost=2, parallelism=1)


def hash_password(password: str) -> str:
    return hasher.hash(password)


def verificar_password(password: str, password_hash: str | None) -> bool:
    # password_hash es None en cuentas de corredor pre-importadas desde Excel, aún sin
    # activar (spec v10 Anexo B §4): nunca pueden autenticar hasta fijar su contraseña.
    if password_hash is None:
        return False
    try:
        return hasher.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError):
        return False
