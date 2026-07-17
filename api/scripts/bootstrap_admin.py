"""Crea la primera cuenta de Administrador si todavía no existe ninguna.

Idempotente: si ya hay un usuario con rol admin, no hace nada. Pensado para el
arranque del stack de producción (docker-compose.prod.yml), donde NO se ejecuta
el seed de desarrollo (crearía cuentas con contraseñas conocidas públicamente).
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

        password = secrets.token_urlsafe(12)
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
        print(f"  Password: {password}")
        print("Guarda esta contraseña ahora: no se volverá a mostrar.")
        print("=" * 64)
    finally:
        if debe_cerrar:
            db.close()


if __name__ == "__main__":
    run()
