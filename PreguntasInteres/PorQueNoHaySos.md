# PorQueNoHaySos

**Pregunta:** ¿Por qué la app no tiene botón de SOS / emergencia?

## Respuesta

El **SOS está pospuesto a la v1.1**. Se eliminó de todos los flujos, modelo de
datos, API y UI de la **v1.0** (spec v10, corrección **C** de la cabecera).

Aunque la spec dejó *definido a nivel de flujo* cómo debería comportarse en el
futuro (envío inmediato, fuera del intervalo normal de GPS y exento del límite de
frecuencia), **no se implementa** todavía.

> Regla del proyecto (CLAUDE.md): **"Nunca implementar SOS (pospuesto a v1.1)."**

Es una decisión de alcance deliberada, no un olvido: no añadir SOS parcial ni
"provisional" en la v1.0.
