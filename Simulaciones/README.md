# Simulaciones guardadas

Escenarios de demostración ya preparados sobre el simulador de corredores
(`/simulador`, FASE S4). No son datos grabados — son **scripts que vuelven a
generar la simulación en vivo** contra el servidor real cada vez que se
ejecutan (así que hace falta tenerlo levantado antes).

## `demo_villacabra_10_corredores.sh`

10 corredores virtuales sobre la ruta real de Villacabra 11K
(`api/seed/rutas/villacabra-11k.gpx`), repartidos en la salida con huecos
aleatorios de 2 a 100 m (no arrancan todos apilados en el mismo punto) y a
velocidad acelerada: la carrera completa se ve en la web pública en unos 4
minutos reales (frente a los ~70 min que tardaría el corredor más lento a
ritmo real) — margen pensado a propósito para poder abrir la web pública y
ponerse a mirar con calma sin perderse el arranque. Pensado para comprobar de
un vistazo cómo se comportan los corredores sobre el mapa (trazado,
interpolación, colores), no para probar carga ni resiliencia — por eso va sin
pérdida de cobertura ni relojes desviados.

**Antes de ejecutarlo**: el servidor tiene que estar arriba y accesible en
`http://localhost:8000` — vale tanto `docker-compose.dev.yml` como
`docker-compose.prod.yml` (el launcher), los dos publican la API en ese mismo
puerto. **Abre la web pública primero** (ver más abajo) y luego lanza el
script — así no se pierde ni un segundo de los 4 minutos viendo si ha
arrancado bien.

```bash
./demo_villacabra_10_corredores.sh
```

Luego, para verla: abre la web pública (`:8081` si usas el stack de
producción/launcher, o `npm run dev --workspace web-publica` en desarrollo).
**No hay ningún código que escribir en ningún sitio** — la web pública
muestra sola el evento "activo" (`GET /eventos/activo`: el de mayor id que no
esté en Borrador ni Archivado, spec v10 SUP-002 — un único evento activo por
PC). El código de acceso (`DEMO-VILLACABRA`) solo lo usan los corredores para
unirse desde la app; el simulador ya hace ese paso por ellos, no hay que
introducirlo en ningún sitio para verla.

**Importante**: como "el evento activo" es el de mayor id, si en esta misma
base de datos hay otro evento más reciente sin archivar (una prueba tuya, un
evento real en curso…), ese es el que se verá, no la demo. Antes de una demo,
comprueba con `GET /eventos/activo` cuál se está mostrando.

**Repetir la demo**: el script crea el evento con el código `DEMO-VILLACABRA`
fijo para que sea reconocible; si ya existe de una demo anterior, la creación
fallará (código de acceso único). Antes de repetir, lanza el script con
`CODIGO_EVENTO=DEMO-VILLACABRA-2 ./demo_villacabra_10_corredores.sh` para usar
uno nuevo — quedará con un id más alto y pasará a ser el evento activo sin
tocar el anterior (no hay forma de borrar un evento desde la API, solo de
archivarlo cambiando su estado, y solo siguiendo la máquina de estados hasta
Finalizado).

Variables de entorno que acepta (todas opcionales, tienen valores por
defecto pensados para este demo): `CODIGO_EVENTO`, `ADMIN_EMAIL`,
`ADMIN_PASSWORD`, `API_URL`.
