import shutil
import subprocess

import pytest

from app.config import settings
from app.servicios.pg_dump import generar_backup

pytestmark = pytest.mark.skipif(
    shutil.which("pg_dump") is None, reason="pg_dump no disponible en este entorno"
)


def test_generar_backup_crea_fichero_cifrado(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "backup_dir", str(tmp_path))
    monkeypatch.setattr(settings, "backup_dir_secundario", None)

    ruta = generar_backup(evento_id=999999)

    assert ruta.exists()
    assert ruta.suffix == ".enc"
    # El dump sin cifrar nunca debe quedar en disco.
    assert not any(p.suffix == ".dump" for p in tmp_path.iterdir())


def test_generar_backup_copia_a_destino_secundario(tmp_path, monkeypatch) -> None:
    primario = tmp_path / "primario"
    secundario = tmp_path / "secundario"
    monkeypatch.setattr(settings, "backup_dir", str(primario))
    monkeypatch.setattr(settings, "backup_dir_secundario", str(secundario))

    ruta = generar_backup(evento_id=999998)

    copia = secundario / ruta.name
    assert copia.exists()
    assert copia.read_bytes() == ruta.read_bytes()


def test_backup_cifrado_se_puede_descifrar_con_la_passphrase(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "backup_dir", str(tmp_path))
    monkeypatch.setattr(settings, "backup_dir_secundario", None)

    ruta = generar_backup(evento_id=999997)

    destino = tmp_path / "descifrado.dump"
    subprocess.run(
        [
            "openssl",
            "enc",
            "-d",
            "-aes-256-cbc",
            "-pbkdf2",
            "-in",
            str(ruta),
            "-out",
            str(destino),
            "-pass",
            f"pass:{settings.backup_passphrase}",
        ],
        check=True,
    )
    # Cabecera del formato custom de pg_dump.
    assert destino.read_bytes()[:5] == b"PGDMP"


def test_backup_con_passphrase_incorrecta_no_produce_el_dump_original(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setattr(settings, "backup_dir", str(tmp_path))
    monkeypatch.setattr(settings, "backup_dir_secundario", None)

    ruta = generar_backup(evento_id=999996)

    destino = tmp_path / "descifrado_mal.dump"
    resultado = subprocess.run(
        [
            "openssl",
            "enc",
            "-d",
            "-aes-256-cbc",
            "-pbkdf2",
            "-in",
            str(ruta),
            "-out",
            str(destino),
            "-pass",
            "pass:clave-incorrecta",
        ],
        capture_output=True,
    )
    assert resultado.returncode != 0
