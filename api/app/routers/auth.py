from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.errores import ErrorAPI
from app.models import Corredor, Usuario
from app.schemas.auth import (
    LoginCorredorEntrada,
    LoginPanelEntrada,
    RegistroCorredorEntrada,
    SesionSalida,
)
from app.security.passwords import hash_password, verificar_password
from app.security.rate_limit import limitador_login
from app.security.tokens import crear_token_sesion_corredor, crear_token_sesion_panel

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=SesionSalida)
def login_panel(datos: LoginPanelEntrada, db: Session = Depends(get_db)) -> SesionSalida:
    clave = f"panel:{datos.email.lower()}"
    if limitador_login.bloqueado(clave):
        raise ErrorAPI(
            429, "demasiados_intentos", "Cuenta bloqueada temporalmente por demasiados intentos."
        )

    usuario = db.query(Usuario).filter_by(email=datos.email).one_or_none()
    if usuario is None or not verificar_password(datos.password, usuario.password_hash):
        limitador_login.registrar_fallo(clave)
        raise ErrorAPI(401, "credenciales_invalidas", "Email o contraseña incorrectos.")

    limitador_login.registrar_exito(clave)
    token, expira = crear_token_sesion_panel(usuario.id, usuario.rol)
    return SesionSalida(access_token=token, expira_en=expira)


@router.post("/corredores/registro", response_model=SesionSalida, status_code=201)
def registro_corredor(
    datos: RegistroCorredorEntrada, db: Session = Depends(get_db)
) -> SesionSalida:
    existente = db.query(Corredor).filter_by(email=datos.email).one_or_none()

    # email/telefono alternativos (decisión 2026-07-19): si el email no coincide
    # con ninguna cuenta pero el corredor aporta el teléfono que el organizador
    # cargó en el Excel, se activa esa cuenta pre-importada en vez de crear una
    # nueva sin inscripción (el problema original: un email mal escrito dejaba
    # la inscripción huérfana sin forma de recuperarla).
    if existente is None and datos.telefono:
        existente = db.query(Corredor).filter_by(telefono=datos.telefono).one_or_none()

    if existente is not None:
        if existente.password_hash is not None:
            if existente.email == datos.email:
                raise ErrorAPI(
                    409, "email_duplicado", "Ya existe una cuenta de corredor con ese email."
                )
            raise ErrorAPI(
                409, "telefono_duplicado", "Ya existe una cuenta de corredor con ese teléfono."
            )
        # Cuenta pre-importada desde Excel (RF-002): activarla fijando la contraseña,
        # sin tocar nombre/apellidos/club ya cargados por el organizador. Si le
        # faltaba el email (Excel solo con teléfono) o el teléfono, se rellenan
        # con lo que trae este registro.
        existente.password_hash = hash_password(datos.password)
        if existente.email is None:
            existente.email = datos.email
        if existente.telefono is None and datos.telefono:
            existente.telefono = datos.telefono
        db.commit()
        db.refresh(existente)
        token, expira = crear_token_sesion_corredor(existente.id)
        return SesionSalida(access_token=token, expira_en=expira)

    corredor = Corredor(
        nombre=datos.nombre,
        apellidos=datos.apellidos,
        club=datos.club,
        email=datos.email,
        telefono=datos.telefono,
        password_hash=hash_password(datos.password),
    )
    db.add(corredor)
    db.commit()
    db.refresh(corredor)

    token, expira = crear_token_sesion_corredor(corredor.id)
    return SesionSalida(access_token=token, expira_en=expira)


@router.post("/corredores/login", response_model=SesionSalida)
def login_corredor(datos: LoginCorredorEntrada, db: Session = Depends(get_db)) -> SesionSalida:
    clave = f"corredor:{datos.email.lower()}"
    if limitador_login.bloqueado(clave):
        raise ErrorAPI(
            429, "demasiados_intentos", "Cuenta bloqueada temporalmente por demasiados intentos."
        )

    corredor = db.query(Corredor).filter_by(email=datos.email).one_or_none()
    if corredor is not None and corredor.password_hash is None:
        raise ErrorAPI(
            401,
            "cuenta_no_activada",
            "Tu inscripción ya está cargada; completa el registro en la app con este "
            "mismo email para fijar tu contraseña.",
        )
    if corredor is None or not verificar_password(datos.password, corredor.password_hash):
        limitador_login.registrar_fallo(clave)
        raise ErrorAPI(401, "credenciales_invalidas", "Email o contraseña incorrectos.")

    limitador_login.registrar_exito(clave)
    token, expira = crear_token_sesion_corredor(corredor.id)
    return SesionSalida(access_token=token, expira_en=expira)
