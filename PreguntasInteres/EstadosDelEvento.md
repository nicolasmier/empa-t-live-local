# EstadosDelEvento

**Pregunta:** ¿Qué estados tiene un evento y qué transiciones son válidas?

## Respuesta

La máquina de estados vive aislada en `api/app/dominio/estados_evento.py`
(spec v10 §11). Orden:

```
borrador → publicado → preparacion → en_directo → finalizado → archivado
```

### Reglas de transición (`transicion_valida`)

- **Avance**: a cualquier estado posterior (se pueden saltar pasos).
- **Retroceso**: solo **un paso** hacia atrás (p. ej. `en_directo → preparacion`).
- **`archivado` es terminal**: no admite ninguna transición, ni siquiera el
  retroceso.

### Qué significa cada uno para los corredores

| Estado | ¿Se pueden unir? | ¿Pueden transmitir GPS? |
|---|---|---|
| borrador | No | No |
| publicado | Sí | No |
| preparacion | Sí | No |
| **en_directo** | Sí | **Sí** |
| finalizado | No | No (se revocan los tokens de dispositivo) |
| archivado | No | No |

- La **ingesta de posiciones** exige `en_directo` (`posiciones.py`: si no, `409
  evento_no_en_directo`).
- Al pasar a **finalizado** se **revocan todos los tokens de dispositivo** y se
  dispara un **backup automático**.
- Cualquier cambio de estado **borra** una hora de salida programada pendiente.

Ver también: [SalidaProgramadaYRestablecer](SalidaProgramadaYRestablecer.md),
[IngestaDePosiciones](IngestaDePosiciones.md).
