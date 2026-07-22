# RolesAdminYOperador

**Pregunta:** ¿Qué roles hay en el panel y qué puede hacer cada uno?

## Los dos roles

Los usuarios del panel (`Usuario.rol`) son **admin** u **operador**. La distinción
se implementa en `api/app/security/dependencies.py` con dos dependencias:

- **`requiere_panel`** — cualquier usuario de panel autenticado (admin **o**
  operador).
- **`requiere_admin`** — solo `rol == "admin"`; si no, `403 prohibido`.

## Qué puede cada uno

| | Admin | Operador |
|---|---|---|
| Entrar al panel | ✅ | ✅ |
| Ver estado operativo del evento (resumen, corredores) | ✅ | ✅ |
| Crear/editar eventos, distancias, contenido | ✅ | ❌ |
| Cambiar el estado del evento (dar salida, finalizar…) | ✅ | ❌ |
| Importar Excel / añadir / editar / borrar corredores | ✅ | ❌ |
| Configuración del evento | ✅ | ❌ |

En la práctica, casi toda la API de gestión usa `requiere_admin`; el **operador**
sirve para dar acceso de **operación/consulta** durante el evento sin poder
tocar la configuración.

## Semilla de desarrollo

`api/seed/seed.py` crea:

- `admin@example.com` / `admin1234` (rol admin)
- `operador@example.com` / `operador1234` (rol operador)

> Nota: estos son usuarios del **panel**, distintos de las cuentas de
> **corredor** (ver [ComoSeEnlaza](ComoSeEnlaza.md)).
