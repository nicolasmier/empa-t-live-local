from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dominio.estado_transmision import calcular_estado_transmision
from app.errores import ErrorAPI
from app.models import Corredor, Distancia, Inscripcion, Usuario
from app.schemas.inscripciones_admin import (
    EliminarInscripcionesEntrada,
    EliminarInscripcionesSalida,
    InscripcionActualizar,
    InscripcionCrear,
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


def _limpiar(valor: str | None) -> str | None:
    if valor is None:
        return None
    limpio = valor.strip()
    return limpio or None


@router.post(
    "/distancias/{distancia_id}/corredores", response_model=PosicionPublica, status_code=201
)
def crear_corredor(
    distancia_id: int,
    datos: InscripcionCrear,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requiere_admin),
) -> PosicionPublica:
    """Alta individual (misma lógica que la importación de Excel, pero de uno en
    uno): matching por email y, si no, por teléfono; comprobación de dorsal
    duplicado antes de crear nada."""
    distancia = db.get(Distancia, distancia_id)
    if distancia is None:
        raise ErrorAPI(404, "no_encontrado", "Distancia no encontrada.")

    nombre = _limpiar(datos.nombre)
    apellidos = _limpiar(datos.apellidos)
    dorsal = _limpiar(datos.dorsal)
    club = _limpiar(datos.club)
    email = _limpiar(datos.email)
    telefono = _limpiar(datos.telefono)

    if not nombre or not apellidos or not dorsal or not (email or telefono):
        raise ErrorAPI(
            422,
            "campos_faltantes",
            "Faltan campos obligatorios (nombre, apellidos, dorsal y al menos uno "
            "de email/teléfono).",
        )

    # email/telefono alternativos: se enlaza con una cuenta ya existente si el
    # email o el teléfono coinciden, en vez de crear un duplicado huérfano.
    corredor_existente = None
    if email:
        corredor_existente = db.query(Corredor).filter_by(email=email).one_or_none()
    if corredor_existente is None and telefono:
        corredor_existente = db.query(Corredor).filter_by(telefono=telefono).one_or_none()

    # El dorsal choca solo si pertenece a un corredor DISTINTO del que estos
    # datos identifican (por email o teléfono).
    colision = (
        db.query(Inscripcion)
        .filter(Inscripcion.distancia_id == distancia_id, Inscripcion.dorsal == dorsal)
        .one_or_none()
    )
    if colision is not None and (
        corredor_existente is None or colision.corredor_id != corredor_existente.id
    ):
        raise ErrorAPI(
            409,
            "dorsal_duplicado",
            f"El dorsal '{dorsal}' ya está asignado a otro corredor en esta distancia.",
        )

    corredor = corredor_existente
    if corredor is None:
        # Cuenta pre-importada (RF-002): sin contraseña hasta que el corredor
        # complete el registro en la app con este mismo email/teléfono.
        corredor = Corredor(
            nombre=nombre, apellidos=apellidos, club=club, email=email, telefono=telefono
        )
        db.add(corredor)
        db.flush()
    else:
        # No se pisa nombre/apellidos/club de una cuenta ya existente, pero sí se
        # rellena email/telefono si faltaba.
        if corredor.email is None and email:
            corredor.email = email
        if corredor.telefono is None and telefono:
            corredor.telefono = telefono

    ya_inscrito = (
        db.query(Inscripcion)
        .filter_by(corredor_id=corredor.id, distancia_id=distancia_id)
        .one_or_none()
    )
    if ya_inscrito is not None:
        raise ErrorAPI(
            409,
            "ya_inscrito",
            "Ese corredor ya está inscrito en esta distancia.",
        )

    inscripcion = Inscripcion(corredor_id=corredor.id, distancia_id=distancia_id, dorsal=dorsal)
    db.add(inscripcion)
    db.flush()
    registrar_auditoria(
        db,
        usuario.id,
        "corredor_creado",
        "inscripcion",
        str(inscripcion.id),
        detalle={"dorsal": dorsal, "email": email, "telefono": telefono},
    )
    db.commit()
    db.refresh(inscripcion)
    return _a_posicion_publica(inscripcion)


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
