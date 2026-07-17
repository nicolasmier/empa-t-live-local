from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://empatelive:empatelive@localhost:5432/empatelive"
    entorno: str = "desarrollo"
    secret_key: str = "clave-de-desarrollo-cambiar-en-produccion"
    storage_dir: str = "storage"
    # Dimensionado para el pico de ingesta de la spec (~50 peticiones/s, 300-800
    # corredores concurrentes, sección 7); el valor por defecto de SQLAlchemy
    # (5 + 10 overflow = 15) se agota bajo esa carga (hallazgo de la FASE S4).
    db_pool_size: int = 20
    db_max_overflow: int = 40
    # Backups (Anexo D): destino local obligatorio, destino secundario opcional
    # (USB o nube montada como carpeta), cifrados con una passphrase simétrica.
    backup_dir: str = "storage/backups"
    backup_dir_secundario: str | None = None
    backup_passphrase: str = "clave-de-backup-cambiar-en-produccion"
    backup_intervalo_min: int = 30
    # Salida programada (Preparación -> En directo automático): intervalo de
    # comprobación corto porque, a diferencia del backup, aquí sí importa la
    # precisión percibida por quien mira el cronómetro de cuenta atrás.
    salida_programada_intervalo_seg: int = 10
    # Primer Administrador (docker-compose.prod.yml): la contraseña se genera al
    # azar y se imprime una única vez en el arranque (scripts/bootstrap_admin.py).
    admin_bootstrap_email: str = "admin@localhost"


settings = Settings()
