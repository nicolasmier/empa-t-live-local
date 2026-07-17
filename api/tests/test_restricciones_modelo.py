from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import Corredor, Distancia, Evento, Inscripcion, Usuario


def _crear_admin(db_session, email: str = "admin.test@example.com") -> Usuario:
    admin = Usuario(nombre="Admin", email=email, password_hash="x", rol="admin")
    db_session.add(admin)
    db_session.flush()
    return admin


def test_codigo_acceso_evento_es_unico(db_session) -> None:
    admin = _crear_admin(db_session)
    db_session.add(
        Evento(nombre="A", codigo_acceso="DUP2026", fecha=date.today(), creado_por=admin.id)
    )
    db_session.flush()

    db_session.add(
        Evento(nombre="B", codigo_acceso="DUP2026", fecha=date.today(), creado_por=admin.id)
    )
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_estado_evento_fuera_de_lista_cerrada_falla(db_session) -> None:
    admin = _crear_admin(db_session)
    db_session.add(
        Evento(
            nombre="C",
            codigo_acceso="ESTADOINVALIDO2026",
            fecha=date.today(),
            creado_por=admin.id,
            estado="inventado",
        )
    )
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_dorsal_duplicado_en_misma_distancia_falla(db_session) -> None:
    admin = _crear_admin(db_session)
    evento = Evento(nombre="D", codigo_acceso="DORSAL2026", fecha=date.today(), creado_por=admin.id)
    db_session.add(evento)
    db_session.flush()
    distancia = Distancia(evento_id=evento.id, nombre="10K")
    db_session.add(distancia)
    db_session.flush()

    c1 = Corredor(nombre="Uno", apellidos="Test", email="uno@example.com", password_hash="x")
    c2 = Corredor(nombre="Dos", apellidos="Test", email="dos@example.com", password_hash="x")
    db_session.add_all([c1, c2])
    db_session.flush()

    db_session.add(Inscripcion(corredor_id=c1.id, distancia_id=distancia.id, dorsal="1"))
    db_session.flush()
    db_session.add(Inscripcion(corredor_id=c2.id, distancia_id=distancia.id, dorsal="1"))
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_mismo_dorsal_en_distancias_distintas_es_valido(db_session) -> None:
    admin = _crear_admin(db_session)
    evento = Evento(
        nombre="E", codigo_acceso="DORSALOK2026", fecha=date.today(), creado_por=admin.id
    )
    db_session.add(evento)
    db_session.flush()
    d1 = Distancia(evento_id=evento.id, nombre="10K")
    d2 = Distancia(evento_id=evento.id, nombre="22K")
    db_session.add_all([d1, d2])
    db_session.flush()

    c1 = Corredor(nombre="Tres", apellidos="Test", email="tres@example.com", password_hash="x")
    c2 = Corredor(nombre="Cuatro", apellidos="Test", email="cuatro@example.com", password_hash="x")
    db_session.add_all([c1, c2])
    db_session.flush()

    db_session.add(Inscripcion(corredor_id=c1.id, distancia_id=d1.id, dorsal="7"))
    db_session.add(Inscripcion(corredor_id=c2.id, distancia_id=d2.id, dorsal="7"))
    db_session.flush()
