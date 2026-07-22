# AltaIndividualDeCorredores

**Pregunta:** ¿Se pueden dar de alta corredores uno a uno desde el panel, sin
Excel?

## Respuesta

Sí. Panel → evento → pestaña **Corredores** → selecciona la **distancia** →
**"Añadir corredor"**. Útil para los que se quedaron sin meter en el Excel o para
hacer pruebas.

Campos: **dorsal**, **nombre**, **apellidos** (obligatorios) + **email o
teléfono** (al menos uno) + **club** (opcional).

## Reglas (idénticas a la importación de Excel)

- Enlaza con una cuenta existente por **email** y, si no, por **teléfono**; si no
  existe, crea una cuenta **pre-importada sin contraseña**.
- **Dorsal duplicado** en esa distancia → `409 dorsal_duplicado`.
- Falta nombre/apellidos/dorsal o no hay email ni teléfono → `422
  campos_faltantes`.
- El corredor ya inscrito en esa distancia → `409 ya_inscrito`.

Tras el alta, el corredor se registra en la app con ese mismo email/teléfono para
**activar** su cuenta y poder unirse (ver [ComoSeEnlaza](ComoSeEnlaza.md)).

## Implementación

- Backend: `POST /distancias/{distancia_id}/corredores`
  (`api/app/routers/corredores_admin.py::crear_corredor`, solo admin).
- Panel: formulario "Añadir corredor" en
  `panel/src/componentes/pestanas/Corredores.tsx`.

Ver también: [ImportarCorredoresExcel](ImportarCorredoresExcel.md).
