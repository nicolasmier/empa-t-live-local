# SalidaProgramadaYRestablecer

**Pregunta:** ¿Cómo se programa la hora de salida de un evento y cómo se
restablece si se dio por error?

## Programar la salida (paso automático a En directo)

Con el evento en **Preparación**, en el panel (pestaña **General → Salida
programada**) puedes fijar una **hora de salida**. Un proceso en segundo plano
del servidor (`api/app/servicios/salida_programada.py`) comprueba cada
`salida_programada_intervalo_seg` (10 s por defecto) y, cuando llega la hora,
pasa el evento a **En directo** automáticamente.

- La hora se compara contra el **reloj del propio servidor** (UTC), no el del
  navegador del admin.
- El input del panel usa la hora local del PC (que es el mismo que sirve).
- "Cancelar programación" borra la hora sin cambiar de estado.

Campo en BD: `eventos.hora_programada_directo` (nullable, con zona horaria).

## Restablecer la salida (deshacer un En directo)

Con el evento ya **En directo**, en el panel aparece **"Restablecer salida"**:
devuelve el evento a **Preparación** (retroceso de un paso, spec §11).

- Los corredores **dejan de poder transmitir** hasta la nueva salida.
- **No se borran** las posiciones ya recibidas (el histórico se conserva).
- Al volver a Preparación reaparece el control para **fijar la hora** o lanzar la
  salida a mano de nuevo.

Implementación: botón en `panel/src/componentes/pestanas/SalidaProgramada.tsx`
(llama a `POST /eventos/{id}/estado` con `preparacion`). Cualquier cambio de
estado, además, invalida una hora programada pendiente.

Ver también: [EstadosDelEvento](EstadosDelEvento.md).
