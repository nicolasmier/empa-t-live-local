import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database import engine, get_db
from app.main import app


@pytest.fixture()
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture()
def cliente(db_session):
    """TestClient cuyas peticiones usan la misma sesión/transacción que `db_session`.

    Así los cambios hechos vía API son visibles para las aserciones directas sobre
    `db_session`, y todo se revierte al final del test (nada queda en la BD de desarrollo).
    """

    def _get_db_override():
        yield db_session

    app.dependency_overrides[get_db] = _get_db_override
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_db, None)
