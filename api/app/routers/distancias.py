from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.errores import ErrorAPI
from app.models import Distancia, Evento, Inscripcion, Usuario
from app.schemas.distancias import DistanciaActualizar, DistanciaCrear, DistanciaSalida
from app.security.dependencies import requiere_admin
from app.servicios.auditoria import registrar_auditoria
from app.servicios.inscripciones import eliminar_inscripcion_y_dependientes

router = APIRouter(tags=["distancias"])


def _obtener_evento_o_404(db: Session, evento_id: int) -> Evento:
    evento = db.get(Evento, evento_id)
    if evento is None:
        raise ErrorAPI(404, "no_encontrado", "Evento no encontrado.")
    return evento


def _obtener_distancia_o_404(db: Session, distancia_id: int) -> Distancia:
    distancia = db.get(Distancia, distancia_id)
    if distancia is None:
        raise ErrorAPI(404, "no_encontrado", "Distancia no encontrada.")
    return distancia


@router.get("/eventos/{evento_id}/distancias", response_model=list[DistanciaSalida])
def listar_distancias(evento_id: int, db: Session = Depends(get_db)) -> list[Distancia]:
    # Lectura pública LAN (Anexo B §6, "contenido del evento"): la web pública
    # necesita las distancias y su gpx_url/mapa_config para las pestañas del
    # mapa sin autenticarse. Mismo criterio que patrocinadores/noticias.
    _obtener_evento_o_404(db, evento_id)
    return db.query(Distancia).filter_by(evento_id=evento_id).order_by(Distancia.id).all()


@router.post("/eventos/{evento_id}/distancias", response_model=DistanciaSalida, status_code=201)
def crear_distancia(
    evento_id: int,
    datos: DistanciaCrear,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requiere_admin),
) -> Distancia:
    _obtener_evento_o_404(db, evento_id)
    distancia = Distancia(evento_id=evento_id, nombre=datos.nombre)
    db.add(distancia)
    db.flush()
    registrar_auditoria(db, usuario.id, "distancia_creada", "distancia", str(distancia.id))
    db.commit()
    db.refresh(distancia)
    return distancia


@router.put("/distancias/{distancia_id}", response_model=DistanciaSalida)
def actualizar_distancia(
    distancia_id: int,
    datos: DistanciaActualizar,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requiere_admin),
) -> Distancia:
    distancia = _obtener_distancia_o_404(db, distancia_id)
    cambios = datos.model_dump(exclude_unset=True)
    for campo, valor in cambios.items():
        setattr(distancia, campo, valor)
    registrar_auditoria(
        db,
        usuario.id,
        "distancia_actualizada",
        "distancia",
        str(distancia.id),
        detalle=datos.model_dump(exclude_unset=True, mode="json"),
    )
    db.commit()
    db.refresh(distancia)
    return distancia


@router.delete("/distancias/{distancia_id}", status_code=204)
def eliminar_distancia(
    distancia_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requiere_admin),
) -> None:
    distancia = _obtener_distancia_o_404(db, distancia_id)

    # Se borra en cascada aunque tenga corredores inscritos (p. ej. para
    # deshacer un error tras publicar el evento): cada inscripción se borra
    # con todo lo que cuelga de ella (posiciones, tokens, incidencias) antes
    # de borrar la propia distancia. El aviso fuerte va en la confirmación
    # del panel, no aquí — a nivel de API no hay medias tintas útiles.
    inscripciones = db.query(Inscripcion).filter(Inscripcion.distancia_id == distancia_id).all()
    for inscripcion in inscripciones:
        eliminar_inscripcion_y_dependientes(db, inscripcion)

    registrar_auditoria(
        db,
        usuario.id,
        "distancia_eliminada",
        "distancia",
        str(distancia.id),
        detalle={"corredores_eliminados": len(inscripciones)},
    )
    db.delete(distancia)
    db.commit()
