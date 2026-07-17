from sqlalchemy.orm import Session

from app.models import Incidencia, Inscripcion, PosicionActual, PosicionHistorico, TokenDispositivo


def eliminar_inscripcion_y_dependientes(db: Session, inscripcion: Inscripcion) -> None:
    """Borra una inscripción y todo lo que cuelga de ella (posiciones, tokens,
    incidencias) — no hay `ondelete=CASCADE` a nivel de BD, así que hay que
    hacerlo explícito. Usado tanto al borrar un corredor suelto como al
    borrar una distancia entera con corredores inscritos."""
    inscripcion_id = inscripcion.id
    db.query(PosicionActual).filter(PosicionActual.inscripcion_id == inscripcion_id).delete()
    db.query(PosicionHistorico).filter(
        PosicionHistorico.inscripcion_id == inscripcion_id
    ).delete()
    db.query(TokenDispositivo).filter(TokenDispositivo.inscripcion_id == inscripcion_id).delete()
    db.query(Incidencia).filter(Incidencia.inscripcion_id == inscripcion_id).delete()
    db.delete(inscripcion)
