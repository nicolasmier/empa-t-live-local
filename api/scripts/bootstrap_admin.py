"""Crea la cuenta genérica de Administrador si todavía no existe ninguna.

Idempotente: si ya hay un usuario con rol admin, no hace nada. Pensado para el
arranque del stack de producción (docker-compose.prod.yml). Usa las credenciales
de `settings.admin_bootstrap_email` / `admin_bootstrap_password` (por defecto la
cuenta genérica del proyecto, CronoEmpate); si `admin_bootstrap_password` se deja
vacío, se genera una aleatoria y se imprime una sola vez.
"""

import secrets

from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.models import Usuario
from app.security.passwords import hash_password


def run(db: Session | None = None) -> None:
    debe_cerrar = db is None
    db = db or SessionLocal()
    try:
        existente = db.query(Usuario).filter_by(rol="admin").first()
        if existente is not None:
            print(f"Ya existe un Administrador ({existente.email}); no se crea ninguno nuevo.")
            return

        password = settings.admin_bootstrap_password or secrets.token_urlsafe(12)
        usuario = Usuario(
            nombre="Administrador",
            email=settings.admin_bootstrap_email,
            password_hash=hash_password(password),
            rol="admin",
        )
        db.add(usuario)
        db.commit()

        print("=" * 64)
        print("Cuenta de Administrador creada:")
        print(f"  Email:    {settings.admin_bootstrap_email}")
        if settings.admin_bootstrap_password:
            print("  Password: (la configurada en admin_bootstrap_password)")
        else:
            print(f"  Password: {password}")
            print("Guarda esta contraseña ahora: no se volverá a mostrar.")
        print("=" * 64)
    finally:
        if debe_cerrar:
            db.close()


if __name__ == "__main__":
    run()
