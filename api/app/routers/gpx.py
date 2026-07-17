from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.orm import Session

from app.almacenamiento import ruta_storage, url_publica
from app.database import get_db
from app.errores import ErrorAPI
from app.models import Distancia, Usuario
from app.schemas.distancias import DistanciaSalida
from app.security.dependencies import requiere_admin
from app.servicios.auditoria import registrar_auditoria
from app.servicios.gpx import procesar_gpx

router = APIRouter(tags=["gpx"])


@router.post("/distancias/{distancia_id}/gpx", response_model=DistanciaSalida)
def subir_gpx(
    distancia_id: int,
    archivo: UploadFile,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requiere_admin),
) -> Distancia:
    distancia = db.get(Distancia, distancia_id)
    if distancia is None:
        raise ErrorAPI(404, "no_encontrado", "Distancia no encontrada.")

    contenido = archivo.file.read()
    try:
        resultado = procesar_gpx(contenido)
    except ValueError as exc:
        raise ErrorAPI(400, "gpx_invalido", str(exc)) from exc

    destino = ruta_storage("gpx", f"{distancia_id}.gpx")
    destino.write_bytes(contenido)

    distancia.gpx_url = url_publica("gpx", f"{distancia_id}.gpx")
    distancia.mapa_config = {**(distancia.mapa_config or {}), "bbox": resultado["bbox"]}

    registrar_auditoria(
        db,
        usuario.id,
        "gpx_subido",
        "distancia",
        str(distancia_id),
        detalle={"puntos": resultado["puntos"]},
    )
    db.commit()
    db.refresh(distancia)
    return distancia
