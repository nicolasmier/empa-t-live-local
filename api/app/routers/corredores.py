import io

from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.orm import Session

from app.almacenamiento import ruta_storage, url_publica
from app.database import get_db
from app.errores import ErrorAPI
from app.models import Corredor
from app.schemas.corredores import CorredorActualizar, CorredorSalida
from app.security.dependencies import obtener_corredor_actual
from app.servicios.imagenes import redimensionar_para_perfil, validar_y_leer_imagen

router = APIRouter(prefix="/corredores", tags=["corredores"])


def _verificar_propio(corredor_id: int, corredor: Corredor) -> None:
    if corredor_id != corredor.id:
        raise ErrorAPI(403, "prohibido", "Solo puedes acceder a tu propio perfil.")


@router.get("/{corredor_id}", response_model=CorredorSalida)
def obtener_perfil(
    corredor_id: int, corredor: Corredor = Depends(obtener_corredor_actual)
) -> Corredor:
    _verificar_propio(corredor_id, corredor)
    return corredor


@router.put("/{corredor_id}", response_model=CorredorSalida)
def actualizar_perfil(
    corredor_id: int,
    datos: CorredorActualizar,
    db: Session = Depends(get_db),
    corredor: Corredor = Depends(obtener_corredor_actual),
) -> Corredor:
    _verificar_propio(corredor_id, corredor)
    cambios = datos.model_dump(exclude_unset=True)
    for campo, valor in cambios.items():
        setattr(corredor, campo, valor)
    db.commit()
    db.refresh(corredor)
    return corredor


@router.post("/{corredor_id}/foto", response_model=CorredorSalida)
def subir_foto(
    corredor_id: int,
    archivo: UploadFile,
    db: Session = Depends(get_db),
    corredor: Corredor = Depends(obtener_corredor_actual),
) -> Corredor:
    _verificar_propio(corredor_id, corredor)

    contenido = archivo.file.read()
    imagen = validar_y_leer_imagen(contenido)
    imagen = redimensionar_para_perfil(imagen)

    destino = ruta_storage("fotos", f"{corredor_id}.jpg")
    buffer = io.BytesIO()
    imagen.save(buffer, format="JPEG", quality=85)
    destino.write_bytes(buffer.getvalue())

    corredor.foto_url = url_publica("fotos", f"{corredor_id}.jpg")
    db.commit()
    db.refresh(corredor)
    return corredor
