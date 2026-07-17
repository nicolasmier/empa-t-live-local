from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.dominio.estado_transmision import SIN_SENAL, TRANSMITIENDO, calcular_estado_transmision
from app.models import Incidencia, Inscripcion

TIPO_SIN_SENAL = "sin_senal"


def _incidencia_abierta(db: Session, inscripcion_id: int) -> Incidencia | None:
    return (
        db.query(Incidencia)
        .filter(
            Incidencia.inscripcion_id == inscripcion_id,
            Incidencia.tipo == TIPO_SIN_SENAL,
            Incidencia.resuelto_en.is_(None),
        )
        .one_or_none()
    )


def resolver_si_recupera_senal(db: Session, inscripcion_id: int) -> None:
    """Recuperación (spec v10 §5, EA-006): al llegar una nueva posición, cierra la
    incidencia de falta de señal abierta, si la había."""
    incidencia = _incidencia_abierta(db, inscripcion_id)
    if incidencia is not None:
        incidencia.resuelto_en = datetime.now(UTC)


def sincronizar_incidencias_sin_senal(
    db: Session, evento_id: int, inscripciones: list[Inscripcion], umbral_sin_senal_seg: int
) -> None:
    """Crea/resuelve incidencias `sin_senal` según el estado calculado actual.

    Se invoca desde los endpoints de lectura pública y de estado, que se sondean
    cada 3-5 s durante el evento En directo (spec v10 §6 RF-015): no hace falta un
    proceso en segundo plano aparte para mantener la tabla de incidencias al día.

    Una consulta por inscripción para "¿tiene incidencia abierta?" es un N+1 que a
    escala de carrera real (cientos de corredores, sondeado cada 3-5 s por cada
    pantalla conectada) deja este endpoint en varios segundos de latencia —
    hallado en el ensayo general a 800 corredores; de ahí el batching de abajo.
    """
    ids_con_posicion = [i.id for i in inscripciones if i.posicion_actual is not None]
    abiertas_por_inscripcion = {
        i.inscripcion_id: i
        for i in db.query(Incidencia).filter(
            Incidencia.inscripcion_id.in_(ids_con_posicion),
            Incidencia.tipo == TIPO_SIN_SENAL,
            Incidencia.resuelto_en.is_(None),
        )
    }

    for inscripcion in inscripciones:
        actual = inscripcion.posicion_actual
        if actual is None:
            continue  # nunca ha transmitido: no hay incidencia que registrar todavía

        estado = calcular_estado_transmision(actual.timestamp_dispositivo, umbral_sin_senal_seg)
        incidencia_abierta = abiertas_por_inscripcion.get(inscripcion.id)

        if estado == SIN_SENAL and incidencia_abierta is None:
            db.add(
                Incidencia(
                    evento_id=evento_id,
                    inscripcion_id=inscripcion.id,
                    tipo=TIPO_SIN_SENAL,
                    descripcion=f"Sin señal desde {actual.timestamp_dispositivo.isoformat()}",
                )
            )
        elif estado == TRANSMITIENDO and incidencia_abierta is not None:
            incidencia_abierta.resuelto_en = datetime.now(UTC)
