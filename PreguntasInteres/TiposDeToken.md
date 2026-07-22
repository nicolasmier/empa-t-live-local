# TiposDeToken

**Pregunta:** ¿Qué tipos de token hay en el sistema y para qué sirve cada uno?

## Los tres tokens

| Token | Quién lo tiene | Vida | Para qué |
|---|---|---|---|
| **Sesión de panel** (JWT) | Admin / Operador | **12 h** | Entrar al panel de administración |
| **Sesión de corredor** (JWT) | Corredor | **30 días** | Login en la app: unirse, perfil, estado |
| **Token de dispositivo** | El móvil unido a un evento | Hasta revocación | **Enviar posiciones** de ese dorsal |

Definiciones: `api/app/security/tokens.py`
(`TTL_SESION_PANEL = 12h`, `TTL_SESION_CORREDOR = 30 días`).

## Detalles importantes

### Sesión de panel y de corredor (JWT)

- Firmados con `SECRET_KEY`. El de panel lleva el claim `rol` (admin/operador).
- El de corredor "sobrevive a cerrar y reabrir la app" (se guarda cifrado en el
  móvil, Keystore, ver `SesionSeguraStorage`).

### Token de dispositivo (el clave para la ingesta)

- Lo devuelve `POST /eventos/codigo/{codigo}/unirse`, ligado a una **inscripción**
  concreta.
- Se guarda **hasheado** en BD (`TokenDispositivo.token_hash`); nunca en claro.
- **Un solo token activo por inscripción** (SUP-008): unirse desde un segundo
  móvil **revoca** el anterior.
- Se **revoca** al pasar el evento a **finalizado**; no se reactiva si el evento
  retrocede a En directo.

## Al cerrar sesión en la app

El logout borra del móvil **tanto** la sesión de corredor **como** el token de
dispositivo (`SesionSeguraStorage.cerrarSesion`) y detiene la transmisión.

Ver también: [ComoSeEnlaza](ComoSeEnlaza.md),
[QueSeExponePorInternet](QueSeExponePorInternet.md).
