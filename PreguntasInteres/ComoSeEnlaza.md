# ComoSeEnlaza

**Pregunta:** ¿Puede un corredor crear una cuenta en la app sin que el admin
haya precargado sus datos? ¿Cómo se enlaza todo esto?

## Respuesta corta

**Sí**, un corredor puede crear una cuenta en la app sin que el admin lo haya
precargado. Pero eso solo le da una **cuenta**; para **participar** (unirse a la
carrera y transmitir) necesita una **inscripción con dorsal**, y esa **solo la
crea el admin** (importar Excel o el alta individual desde el panel).

Son dos cosas distintas que es fácil confundir:

| Concepto | Qué es | Quién lo crea |
|---|---|---|
| **Cuenta** (`Corredor`) | email/teléfono + contraseña + nombre/foto | El propio corredor al registrarse *(o el admin al precargar, sin contraseña)* |
| **Inscripción** (`Inscripcion`) | vínculo corredor ↔ distancia + **dorsal** | **Solo el admin** (importar Excel o "Añadir corredor") |

## Cómo se enlaza todo

La **llave que une** "la persona que se registra en la app" con "la persona que
el admin cargó" es el **email o el teléfono**. El **dorsal** es una segunda
confirmación en el momento de unirse.

```
Admin precarga (Excel o alta manual)
  → crea Corredor SIN contraseña  +  Inscripcion(dorsal)
                    │
     el corredor abre la app y se REGISTRA
                    │
   ┌── ¿su email coincide con un Corredor precargado? ──► SÍ: activa esa cuenta
   │        (le pone la contraseña, conserva nombre/dorsal)
   ├── ¿no coincide el email pero SÍ el teléfono? ──────► SÍ: igual, por teléfono
   │        (arregla el caso "email mal escrito en el Excel")
   └── ¿no coincide ni email ni teléfono? ─────────────► crea cuenta NUEVA sin inscripción
                                                          (tiene cuenta, pero no puede unirse)
```

Fuente en el código:

- **Registro** (`api/app/routers/auth.py::registro_corredor`): busca un
  `Corredor` por email; si no, por teléfono. Si encuentra uno **sin contraseña**
  (precargado), lo **activa** poniéndole la contraseña sin tocar
  nombre/apellidos/club. Si no encuentra nada, crea una cuenta nueva desde cero.
- **Unirse** (`api/app/routers/eventos.py::unirse_a_evento`): exige una
  `Inscripcion` que case por `(corredor, dorsal)` dentro del evento. Si no existe
  → `404 "sin_inscripcion; contacta con el organizador"`. Si el corredor tiene
  inscripción pero teclea otro dorsal → `409 "dorsal_no_coincide"`.

## Los tres escenarios en la práctica

1. **Precargado + se registra con el mismo email** → activa su cuenta, ya tiene
   dorsal, se une sin problema. *(Es el flujo normal de una carrera real.)*
2. **Precargado solo con teléfono (o email mal escrito) + aporta el teléfono al
   registrarse** → engancha por teléfono con su cuenta precargada. *(Es lo que
   resuelve la decisión "email/teléfono alternativos", 2026-07-19.)*
3. **No precargado, se registra libre** → obtiene una cuenta válida (puede
   loguearse, editar perfil), pero al intentar unirse le sale "no se ha
   encontrado tu inscripción". No puede transmitir hasta que el admin le dé de
   alta con un dorsal.

## Detalle útil: el orden da igual

Si un corredor se registra **libre primero** y **luego** el admin lo
importa/añade con ese mismo email o teléfono, la importación **no crea un
duplicado**: enlaza el dorsal a la cuenta que ya existe (y rellena el
email/teléfono que faltara). Así que da lo mismo quién llegue antes — la llave
email/teléfono los reconcilia en ambos sentidos.

## Para una prueba de campo

Para probar con un corredor "de verdad" desde cero hay dos vías:

- **Rápida:** en el panel → Corredores → **Añadir corredor** (con dorsal +
  email), y luego en el móvil te registras con ese email → activa y ya puedes
  unirte.
- **Realista end-to-end:** importas el Excel, y cada corredor se registra con su
  email.

Un corredor que se registre "a lo loco" sin que el admin lo haya dado de alta
**no podrá unirse** — por diseño, para que nadie transmita como un dorsal que no
es suyo.
