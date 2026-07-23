# PersistenciaLoginApp

**Pregunta:** Cuando un usuario se crea nuevo en la app, ¿dónde persisten los
datos para el login?

## Respuesta corta

Las **credenciales** viven en el **servidor** (PostgreSQL); la **app nunca
guarda la contraseña**, solo un **token de sesión cifrado** para no pedir login
cada vez.

## Dónde persiste cada cosa

### 1. Credenciales de login → servidor (PostgreSQL)

Al registrarse (`POST /auth/corredores/registro`) se crea/activa una fila en la
tabla **`corredores`** con `email`, `telefono`, `nombre`, `apellidos`, `club`,
`foto_url` y **`password_hash`**.

- La contraseña se guarda **hasheada con argon2id** (`api/app/security/passwords.py`,
  `PasswordHasher`), **nunca en claro**.
- Esa fila es la **única fuente de verdad** del login: el servidor hashea lo que
  escribes y lo compara con `password_hash`.
- En producción vive en el volumen de la BD (`empatelive-prod_db_data`) y entra
  en los backups cifrados.

### 2. "Estar logueado" en el móvil → app (cifrado, NO es la contraseña)

La app **no guarda la contraseña en ningún sitio**. Tras registrarse/entrar
guarda lo que devuelve el servidor:

- **Token de sesión** (JWT, 30 días) + `corredorId`.
- En **`EncryptedSharedPreferences`** ("sesion_segura"), cifrado con el **Android
  Keystore** (AES-256) — clase `SesionSeguraStorage`.

Eso es lo que evita tener que volver a loguearse en cada arranque. Al unirse a
una carrera, se guarda además el **token de dispositivo** + dorsal/inscripción.

## Tabla resumen

| Dato | Dónde vive | Formato |
|---|---|---|
| Email + contraseña (login) | Servidor (Postgres, `corredores`) | contraseña **hasheada** (argon2id) |
| "Estar logueado" en el móvil | App (`EncryptedSharedPreferences` + Keystore) | **token JWT** cifrado (no la contraseña) |
| "Estar unido a la carrera" | App (mismo storage) | token de dispositivo + dorsal |

## Consecuencias prácticas

- Si el corredor **cierra sesión** o cambia de móvil, el token local se pierde →
  vuelve a entrar con email+contraseña (validado contra Postgres).
- Si **reinstala la app**, pierde el token local pero **su cuenta sigue en el
  servidor**.
- La misma cuenta entra desde **otro móvil** con email+contraseña (las
  credenciales no están atadas al dispositivo; el token de *dispositivo* sí —
  unirse desde un segundo móvil revoca el del primero, SUP-008).

Ver también: [TiposDeToken](TiposDeToken.md), [ComoSeEnlaza](ComoSeEnlaza.md).
