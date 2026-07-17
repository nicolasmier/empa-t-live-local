"""Backup físico: `pg_dump` en formato custom + cifrado simétrico (Anexo D/E)."""

import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from app.config import settings


def _uri_libpq() -> str:
    # settings.database_url usa el prefijo de SQLAlchemy (postgresql+psycopg://);
    # pg_dump/pg_restore (libpq) esperan el esquema postgresql:// a secas.
    url = settings.database_url
    if url.startswith("postgresql+"):
        return "postgresql://" + url.split("://", 1)[1]
    return url


def generar_backup(evento_id: int) -> Path:
    """`pg_dump -Fc` de toda la base + cifrado AES-256 (openssl), con copia al
    destino secundario si está configurado (Anexo D: local + USB/nube).

    Devuelve la ruta del fichero cifrado. Lanza `subprocess.CalledProcessError`
    si `pg_dump` u `openssl` fallan (el llamador decide cómo registrarlo).
    """
    directorio = Path(settings.backup_dir)
    directorio.mkdir(parents=True, exist_ok=True)

    marca_tiempo = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    nombre_base = f"evento-{evento_id}-{marca_tiempo}.dump"
    ruta_dump = directorio / nombre_base
    ruta_cifrada = directorio / f"{nombre_base}.enc"

    try:
        subprocess.run(
            ["pg_dump", "-Fc", "-f", str(ruta_dump), _uri_libpq()],
            check=True,
            capture_output=True,
            timeout=600,
        )
        subprocess.run(
            [
                "openssl",
                "enc",
                "-aes-256-cbc",
                "-pbkdf2",
                "-salt",
                "-in",
                str(ruta_dump),
                "-out",
                str(ruta_cifrada),
                "-pass",
                f"pass:{settings.backup_passphrase}",
            ],
            check=True,
            capture_output=True,
            timeout=120,
        )
    finally:
        ruta_dump.unlink(missing_ok=True)  # nunca dejar el dump sin cifrar en disco

    if settings.backup_dir_secundario:
        destino = Path(settings.backup_dir_secundario)
        destino.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ruta_cifrada, destino / ruta_cifrada.name)

    return ruta_cifrada
