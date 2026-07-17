from datetime import date, timedelta
from pathlib import Path

from sqlalchemy.orm import Session

from app.almacenamiento import ruta_storage, url_publica
from app.database import SessionLocal
from app.models import Corredor, Distancia, Evento, Inscripcion, Usuario
from app.security.passwords import hash_password
from app.servicios.gpx import procesar_gpx

CODIGO_EVENTO_SEED = "MADRID2026"
GPX_SEED = Path(__file__).resolve().parent / "rutas" / "villacabra-11k.gpx"


def _obtener_o_crear_usuario(
    db: Session, email: str, nombre: str, rol: str, password: str
) -> Usuario:
    usuario = db.query(Usuario).filter_by(email=email).one_or_none()
    if usuario:
        return usuario
    usuario = Usuario(nombre=nombre, email=email, password_hash=hash_password(password), rol=rol)
    db.add(usuario)
    db.flush()
    return usuario


def _obtener_o_crear_evento(db: Session, creador: Usuario) -> Evento:
    evento = db.query(Evento).filter_by(codigo_acceso=CODIGO_EVENTO_SEED).one_or_none()
    if evento:
        return evento
    evento = Evento(
        nombre="Carrera Popular Madrid 2026",
        codigo_acceso=CODIGO_EVENTO_SEED,
        fecha=date.today() + timedelta(days=30),
        estado="publicado",
        creado_por=creador.id,
    )
    db.add(evento)
    db.flush()
    return evento


def _obtener_o_crear_distancias(db: Session, evento: Evento) -> list[Distancia]:
    existentes = db.query(Distancia).filter_by(evento_id=evento.id).order_by(Distancia.id).all()
    if existentes:
        return existentes
    distancias = [
        Distancia(evento_id=evento.id, nombre="Villacabra 11K"),
        Distancia(evento_id=evento.id, nombre="22K"),
    ]
    db.add_all(distancias)
    db.flush()
    return distancias


def _cargar_gpx_seed(db: Session, distancia: Distancia) -> None:
    if distancia.gpx_url or not GPX_SEED.exists():
        return
    contenido = GPX_SEED.read_bytes()
    resultado = procesar_gpx(contenido)
    destino = ruta_storage("gpx", f"{distancia.id}.gpx")
    destino.write_bytes(contenido)
    distancia.gpx_url = url_publica("gpx", f"{distancia.id}.gpx")
    distancia.mapa_config = {**(distancia.mapa_config or {}), "bbox": resultado["bbox"]}


def _sembrar_corredores_inscritos(db: Session, distancias: list[Distancia]) -> None:
    total_inscritos = (
        db.query(Inscripcion)
        .filter(Inscripcion.distancia_id.in_([d.id for d in distancias]))
        .count()
    )
    if total_inscritos >= 20:
        return

    for i in range(1, 21):
        email = f"corredor{i:02d}@example.com"
        corredor = db.query(Corredor).filter_by(email=email).one_or_none()
        if not corredor:
            corredor = Corredor(
                nombre=f"Corredor{i:02d}",
                apellidos="Seed",
                club="Club Seed" if i % 3 == 0 else None,
                email=email,
                password_hash=hash_password("corredor1234"),
            )
            db.add(corredor)
            db.flush()

        distancia = distancias[i % len(distancias)]
        ya_inscrito = (
            db.query(Inscripcion)
            .filter_by(corredor_id=corredor.id, distancia_id=distancia.id)
            .one_or_none()
        )
        if not ya_inscrito:
            db.add(
                Inscripcion(
                    corredor_id=corredor.id, distancia_id=distancia.id, dorsal=str(1000 + i)
                )
            )


def run() -> None:
    db = SessionLocal()
    try:
        admin = _obtener_o_crear_usuario(
            db, "admin@example.com", "Admin Seed", "admin", "admin1234"
        )
        _obtener_o_crear_usuario(
            db, "operador@example.com", "Operador Seed", "operador", "operador1234"
        )
        evento = _obtener_o_crear_evento(db, admin)
        distancias = _obtener_o_crear_distancias(db, evento)
        _cargar_gpx_seed(db, distancias[0])
        _sembrar_corredores_inscritos(db, distancias)
        db.commit()
        print("Seed aplicado correctamente.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run()
