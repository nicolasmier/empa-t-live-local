from pathlib import Path

from app.config import settings


def directorio_storage() -> Path:
    directorio = Path(settings.storage_dir)
    directorio.mkdir(parents=True, exist_ok=True)
    return directorio


def ruta_storage(*partes: str) -> Path:
    """Ruta de destino dentro del volumen local; crea los directorios intermedios."""
    destino = directorio_storage().joinpath(*partes)
    destino.parent.mkdir(parents=True, exist_ok=True)
    return destino


def url_publica(*partes: str) -> str:
    """URL servida en la LAN vía el montaje StaticFiles en /media (app/main.py)."""
    return "/media/" + "/".join(partes)
