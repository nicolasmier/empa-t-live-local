from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.dominio.estado_transmision import TRANSMITIENDO, calcular_estado_transmision
from app.models import Distancia, Evento, Incidencia, Inscripcion
from app.schemas.operacion import EventoActivoResumen, ResumenOperativo
from app.servicios.incidencias import sincronizar_incidencias_sin_senal

router = APIRouter(tags=["operacion"])


@router.get("/operacion/resumen", response_model=ResumenOperativo)
def resumen_operativo(db: Session = Depends(get_db)) -> ResumenOperativo:
    """Para el launcher (Anexo C, semáforos de estado): agregados no sensibles,
    LAN-only y sin autenticación — mismo criterio que la lectura pública de
    posiciones (spec v10 Anexo B §6), solo con números en vez de identidades.
    """
    evento = db.query(Evento).filter(Evento.estado == "en_directo").order_by(Evento.id).first()
    if evento is None:
        return ResumenOperativo(
            evento_activo=None,
            corredores_transmitiendo=0,
            corredores_sin_senal=0,
            incidencias_abiertas=0,
        )

    # Misma corrección N+1 que en `listar_posiciones_publicas` (posiciones.py):
    # este resumen lo sondea el launcher y sufre la misma latencia a escala.
    inscripciones = (
        db.query(Inscripcion)
        .join(Distancia)
        .filter(Distancia.evento_id == evento.id)
        .options(selectinload(Inscripcion.posicion_actual))
        .all()
    )
    sincronizar_incidencias_sin_senal(db, evento.id, inscripciones, evento.umbral_sin_senal_seg)
    db.commit()

    transmitiendo = 0
    sin_senal = 0
    for inscripcion in inscripciones:
        actual = inscripcion.posicion_actual
        estado = calcular_estado_transmision(
            actual.timestamp_dispositivo if actual else None, evento.umbral_sin_senal_seg
        )
        if estado == TRANSMITIENDO:
            transmitiendo += 1
        else:
            sin_senal += 1

    incidencias_abiertas = (
        db.query(Incidencia)
        .filter(Incidencia.evento_id == evento.id, Incidencia.resuelto_en.is_(None))
        .count()
    )

    return ResumenOperativo(
        evento_activo=EventoActivoResumen(
            id=evento.id,
            nombre=evento.nombre,
            codigo_acceso=evento.codigo_acceso,
            estado=evento.estado,
        ),
        corredores_transmitiendo=transmitiendo,
        corredores_sin_senal=sin_senal,
        incidencias_abiertas=incidencias_abiertas,
    )
