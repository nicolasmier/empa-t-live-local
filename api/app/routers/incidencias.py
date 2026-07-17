from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.errores import ErrorAPI
from app.models import Evento, Incidencia, Usuario
from app.schemas.incidencias import IncidenciaSalida
from app.security.dependencies import requiere_panel
from app.servicios.auditoria import registrar_auditoria

router = APIRouter(tags=["incidencias"])


def _a_salida(incidencia: Incidencia) -> IncidenciaSalida:
    return IncidenciaSalida(
        id=incidencia.id,
        evento_id=incidencia.evento_id,
        inscripcion_id=incidencia.inscripcion_id,
        dorsal=incidencia.inscripcion.dorsal if incidencia.inscripcion else None,
        tipo=incidencia.tipo,
        descripcion=incidencia.descripcion,
        creado_en=incidencia.creado_en,
        resuelto_en=incidencia.resuelto_en,
    )


@router.get("/eventos/{evento_id}/incidencias", response_model=list[IncidenciaSalida])
def listar_incidencias(
    evento_id: int,
    db: Session = Depends(get_db),
    resuelta: bool | None = Query(default=None),
    _: Usuario = Depends(requiere_panel),
) -> list[IncidenciaSalida]:
    """Anexo B §4: GET/PUT de incidencias, Admin/Operador (lectura y resolución)."""
    if db.get(Evento, evento_id) is None:
        raise ErrorAPI(404, "no_encontrado", "Evento no encontrado.")

    consulta = db.query(Incidencia).filter(Incidencia.evento_id == evento_id)
    if resuelta is True:
        consulta = consulta.filter(Incidencia.resuelto_en.isnot(None))
    elif resuelta is False:
        consulta = consulta.filter(Incidencia.resuelto_en.is_(None))

    incidencias = consulta.order_by(Incidencia.creado_en.desc()).all()
    return [_a_salida(i) for i in incidencias]


@router.put("/incidencias/{incidencia_id}/resolver", response_model=IncidenciaSalida)
def resolver_incidencia(
    incidencia_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requiere_panel),
) -> IncidenciaSalida:
    incidencia = db.get(Incidencia, incidencia_id)
    if incidencia is None:
        raise ErrorAPI(404, "no_encontrado", "Incidencia no encontrada.")
    if incidencia.resuelto_en is None:
        incidencia.resuelto_en = datetime.now(UTC)
        registrar_auditoria(
            db, usuario.id, "incidencia_resuelta", "incidencia", str(incidencia.id)
        )
        db.commit()
        db.refresh(incidencia)
    return _a_salida(incidencia)
