from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dominio.estado_transmision import calcular_estado_transmision
from app.errores import ErrorAPI
from app.models import Distancia, Inscripcion, Usuario
from app.schemas.inscripciones_admin import (
    EliminarInscripcionesEntrada,
    EliminarInscripcionesSalida,
    InscripcionActualizar,
)
from app.schemas.posiciones import PosicionPublica
from app.security.dependencies import requiere_admin
from app.servicios.auditoria import registrar_auditoria
from app.servicios.inscripciones import eliminar_inscripcion_y_dependientes

router = APIRouter(tags=["corredores-admin"])


def _obtener_inscripcion_de_distancia_o_404(
    db: Session, distancia_id: int, inscripcion_id: int
) -> Inscripcion:
    inscripcion = db.get(Inscripcion, inscripcion_id)
    if inscripcion is None or inscripcion.distancia_id != distancia_id:
        raise ErrorAPI(404, "no_encontrado", "Corredor no encontrado en esta distancia.")
    return inscripcion


def _a_posicion_publica(inscripcion: Inscripcion) -> PosicionPublica:
    actual = inscripcion.posicion_actual
    corredor = inscripcion.corredor
    estado = calcular_estado_transmision(
        actual.timestamp_dispositivo if actual else None,
        inscripcion.distancia.evento.umbral_sin_senal_seg,
    )
    return PosicionPublica(
        inscripcion_id=inscripcion.id,
        dorsal=inscripcion.dorsal,
        nombre=corredor.nombre,
        apellidos=corredor.apellidos,
        club=corredor.club,
        foto_url=corredor.foto_url,
        latitud=float(actual.latitud) if actual else None,
        longitud=float(actual.longitud) if actual else None,
        timestamp_dispositivo=actual.timestamp_dispositivo if actual else None,
        estado=estado,
    )


@router.put(
    "/distancias/{distancia_id}/corredores/{inscripcion_id}", response_model=PosicionPublica
)
def actualizar_corredor(
    distancia_id: int,
    inscripcion_id: int,
    datos: InscripcionActualizar,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requiere_admin),
) -> PosicionPublica:
    inscripcion = _obtener_inscripcion_de_distancia_o_404(db, distancia_id, inscripcion_id)

    if datos.dorsal is not None and datos.dorsal != inscripcion.dorsal:
        colision = (
            db.query(Inscripcion)
            .filter(
                Inscripcion.distancia_id == distancia_id,
                Inscripcion.dorsal == datos.dorsal,
                Inscripcion.id != inscripcion_id,
            )
            .one_or_none()
        )
        if colision is not None:
            raise ErrorAPI(
                409,
                "dorsal_duplicado",
                f"El dorsal '{datos.dorsal}' ya está asignado a otro corredor en esta distancia.",
            )
        inscripcion.dorsal = datos.dorsal

    corredor = inscripcion.corredor
    if datos.nombre is not None:
        corredor.nombre = datos.nombre
    if datos.apellidos is not None:
        corredor.apellidos = datos.apellidos
    if datos.club is not None:
        corredor.club = datos.club

    registrar_auditoria(
        db,
        usuario.id,
        "corredor_actualizado",
        "inscripcion",
        str(inscripcion.id),
        detalle=datos.model_dump(exclude_unset=True, mode="json"),
    )
    db.commit()
    db.refresh(inscripcion)
    return _a_posicion_publica(inscripcion)


@router.delete("/distancias/{distancia_id}/corredores/{inscripcion_id}", status_code=204)
def eliminar_corredor(
    distancia_id: int,
    inscripcion_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requiere_admin),
) -> None:
    inscripcion = _obtener_inscripcion_de_distancia_o_404(db, distancia_id, inscripcion_id)
    registrar_auditoria(db, usuario.id, "corredor_eliminado", "inscripcion", str(inscripcion.id))
    eliminar_inscripcion_y_dependientes(db, inscripcion)
    db.commit()


@router.post(
    "/distancias/{distancia_id}/corredores/eliminar", response_model=EliminarInscripcionesSalida
)
def eliminar_corredores_en_bloque(
    distancia_id: int,
    datos: EliminarInscripcionesEntrada,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requiere_admin),
) -> EliminarInscripcionesSalida:
    if not db.get(Distancia, distancia_id):
        raise ErrorAPI(404, "no_encontrado", "Distancia no encontrada.")

    inscripciones = (
        db.query(Inscripcion)
        .filter(
            Inscripcion.distancia_id == distancia_id,
            Inscripcion.id.in_(datos.inscripcion_ids),
        )
        .all()
    )
    for inscripcion in inscripciones:
        eliminar_inscripcion_y_dependientes(db, inscripcion)

    registrar_auditoria(
        db,
        usuario.id,
        "corredores_eliminados",
        "distancia",
        str(distancia_id),
        detalle={"eliminadas": len(inscripciones), "ids": [i.id for i in inscripciones]},
    )
    db.commit()
    return EliminarInscripcionesSalida(eliminadas=len(inscripciones))
