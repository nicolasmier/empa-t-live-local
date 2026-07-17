from app.models import Usuario
from scripts.bootstrap_admin import run as bootstrap_run


def test_bootstrap_admin_es_idempotente(db_session) -> None:
    total_antes = db_session.query(Usuario).filter_by(rol="admin").count()
    assert total_antes >= 1  # el seed de desarrollo ya crea uno

    bootstrap_run(db_session)
    bootstrap_run(db_session)

    total_despues = db_session.query(Usuario).filter_by(rol="admin").count()
    assert total_despues == total_antes
