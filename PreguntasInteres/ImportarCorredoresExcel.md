# ImportarCorredoresExcel

**Pregunta:** ¿Cómo se importan los corredores desde Excel? ¿Qué formato y qué
reglas hay?

## Cómo

Panel → evento → pestaña **Corredores** → selecciona la **distancia** → **Importar
Excel** (`.xlsx`). Endpoint: `POST /distancias/{distancia_id}/corredores/importar`
(`api/app/routers/importacion.py`).

## Formato del Excel (spec v10 Anexo B §4)

La **primera fila** es la cabecera. Columnas:

- **Obligatorias:** `nombre`, `apellidos`, `dorsal`.
- **Identidad:** `email` **o** `telefono` — al menos una de las dos columnas debe
  existir, y cada fila debe rellenar al menos una.
- **Opcional:** `club`.
- La **distancia NO es una columna**: se toma de la ruta (la que seleccionas).

## Reglas de la importación

- **Enlace por email y luego por teléfono**: si el email no casa pero el teléfono
  sí, engancha con la cuenta ya existente (evita duplicados por email mal
  escrito). Ver [ComoSeEnlaza](ComoSeEnlaza.md).
- **Cuenta pre-importada**: si el corredor no existía, se crea **sin contraseña**
  (se activará cuando él se registre en la app con ese email/teléfono).
- **No se pisan** nombre/apellidos/club de una cuenta ya existente; solo se
  rellena el email/teléfono que faltara.
- **Dorsal duplicado**: si el dorsal ya es de **otro** corredor en esa distancia,
  esa fila da error (no bloquea el resto).
- Filas totalmente vacías se ignoran.

## Informe de resultado

La importación devuelve un resumen: **creados / actualizados / sin cambios /
errores**, y una tabla con el motivo de cada fila con error.

Ver también: [AltaIndividualDeCorredores](AltaIndividualDeCorredores.md).
