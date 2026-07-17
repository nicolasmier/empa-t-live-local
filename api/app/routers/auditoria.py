from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Auditoria, Usuario
from app.schemas.auditoria import AuditoriaSalida
from app.security.dependencies import requiere_admin

router = APIRouter(prefix="/auditoria", tags=["auditoria"])


@router.get("", response_model=list[AuditoriaSalida])
def listar_auditoria(
    db: Session = Depends(get_db),
    evento_id: int | None = Query(default=None),
    desde: datetime | None = Query(default=None),
    hasta: datetime | None = Query(default=None),
    usuario_id: int | None = Query(default=None),
    accion: str | None = Query(default=None),
    _: Usuario = Depends(requiere_admin),
) -> list[Auditoria]:
    consulta = db.query(Auditoria)
    if evento_id is not None:
        # Ámbito acotado a entradas sobre el propio evento (creación, edición, cambios de
        # estado); ampliar a entidades relacionadas (distancias, incidencias...) requerirá
        # una columna evento_id dedicada cuando se auditen esas escrituras en fases futuras.
        consulta = consulta.filter(
            Auditoria.entidad_tipo == "evento", Auditoria.entidad_id == str(evento_id)
        )
    if desde is not None:
        consulta = consulta.filter(Auditoria.creado_en >= desde)
    if hasta is not None:
        consulta = consulta.filter(Auditoria.creado_en <= hasta)
    if usuario_id is not None:
        consulta = consulta.filter(Auditoria.usuario_id == usuario_id)
    if accion is not None:
        consulta = consulta.filter(Auditoria.accion == accion)
    return consulta.order_by(Auditoria.creado_en.desc()).all()
