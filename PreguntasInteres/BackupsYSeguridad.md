# BackupsYSeguridad

**Pregunta:** ¿Cómo se protegen los datos? ¿Contraseñas, tokens, copias de
seguridad?

## Contraseñas

Se hashean con **argon2id** (decisión clarify 2026-07-16). Nunca se guardan en
claro. Verificación en `api/app/security/passwords.py`.

- Cuentas de corredor **pre-importadas** tienen `password_hash = NULL` hasta que
  el corredor se registra y la activa.

## Tokens

- Los JWT (panel y corredor) van firmados con `SECRET_KEY`.
- El **token de dispositivo** se guarda **hasheado** en BD, nunca en claro, y hay
  **uno activo por inscripción** (se revoca al reunirse desde otro móvil o al
  finalizar el evento). Ver [TiposDeToken](TiposDeToken.md).

## Rate limiting del login

`api/app/security/rate_limit.py` (Anexo B §7): **5 intentos fallidos / 15 min →
bloqueo de 15 min**, por clave (email). Aplica a login de panel y de corredor.

## Separación de superficies

El panel y la web pública son LAN-only; solo la API del corredor sale por el
túnel, y la restricción se hace a nivel de proxy (no solo por token). Ver
[QueSeExponePorInternet](QueSeExponePorInternet.md).

## Copias de seguridad

- **Periódicas durante En directo**: cada `backup_intervalo_min` = **30 min**
  (`api/app/servicios/backup_periodico.py`, Anexo D).
- **Al finalizar** el evento: se dispara un backup automático (además de revocar
  los tokens de dispositivo).
- Se hacen con **pg_dump** y se cifran con `BACKUP_PASSPHRASE` (ver `.env`).
  Existe la opción de un directorio secundario (`BACKUP_DIR_SECUNDARIO`).

Ver también: [EstadosDelEvento](EstadosDelEvento.md).
