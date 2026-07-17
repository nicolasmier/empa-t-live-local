"""Restaura un backup cifrado en una base de datos destino (Anexo D: la prueba de
un backup es restaurarlo, no solo generarlo).

Uso:
    python -m scripts.restaurar_backup <fichero.dump.enc> <url_postgres_destino>

`url_postgres_destino` debe ser una URI libpq (`postgresql://usuario:pass@host:puerto/bd`),
no el formato `postgresql+psycopg://` de SQLAlchemy.
"""

import subprocess
import sys
import tempfile
from pathlib import Path

from app.config import settings


def restaurar(ruta_cifrada: Path, url_destino: str) -> None:
    with tempfile.NamedTemporaryFile(suffix=".dump", delete=False) as tmp:
        ruta_dump = Path(tmp.name)
    try:
        subprocess.run(
            [
                "openssl",
                "enc",
                "-d",
                "-aes-256-cbc",
                "-pbkdf2",
                "-in",
                str(ruta_cifrada),
                "-out",
                str(ruta_dump),
                "-pass",
                f"pass:{settings.backup_passphrase}",
            ],
            check=True,
        )
        subprocess.run(
            [
                "pg_restore",
                "--clean",
                "--if-exists",
                "--no-owner",
                "-d",
                url_destino,
                str(ruta_dump),
            ],
            check=True,
        )
    finally:
        ruta_dump.unlink(missing_ok=True)


def main() -> None:
    if len(sys.argv) != 3:
        print("Uso: python -m scripts.restaurar_backup <fichero.dump.enc> <url_postgres_destino>")
        sys.exit(1)
    restaurar(Path(sys.argv[1]), sys.argv[2])
    print("Restauración completada.")


if __name__ == "__main__":
    main()
