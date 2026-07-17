# Simulador de corredores

FASE S4 del plan de Servidor (`docs/Plan_Implementacion_1_Servidor_v2.md`). Genera N
corredores virtuales que recorren una ruta GPX a ritmos realistas y envían sus
posiciones a la API real con tokens reales (registro → unirse → ingesta), igual que
haría la app Android. Es el entregable clave para que el agente Web desarrolle la
pantalla pública contra datos vivos, y sirve para probar el pipeline de ingesta a
escala (300-800 corredores) sin depender de móviles físicos.

## Uso

```bash
cd simulador
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

python -m simulador --gpx rutas_ejemplo/5k_ejemplo.gpx --corredores 50 --duracion-min 5
```

Requiere el servidor levantado (`docker compose -f docker-compose.dev.yml up`) y un
usuario Admin válido (por defecto usa el admin del seed: `admin@example.com`).

## Parámetros principales

| Parámetro | Por defecto | Descripción |
|---|---|---|
| `--gpx` | (obligatorio) | Ruta al fichero GPX del recorrido |
| `--corredores` | 800 | Número de corredores virtuales |
| `--duracion-min` | 30 | Duración simulada de la carrera |
| `--perdida-cobertura` | 0.10 | Fracción de corredores que sufren un corte de cobertura (paran y sincronizan un lote al volver) |
| `--reloj-desviado` | 0.02 | Fracción de corredores con el reloj del móvil desviado |
| `--factor-aceleracion` | 8.0 | Comprime el tiempo simulado (8.0 ≈ 30 min simulados en ~4 min reales); usa `1.0` para tiempo real |
| `--codigo-evento` | (autogenerado) | Reutiliza un evento existente en vez de crear uno nuevo |
| `--espaciado-min-m` / `--espaciado-max-m` | 0 / 0 | Hueco aleatorio (metros) entre la salida de un corredor y el siguiente, acumulado — por defecto (`0`) todos arrancan del punto 0 del GPX (comportamiento original de S4); útil para demos visuales donde interesa ver los corredores repartidos por el mapa desde el principio en vez de apilados en la salida (ver `/Simulaciones`) |

El simulador crea su propio evento y distancia (con el GPX dado), importa los
corredores por Excel (igual que haría un Administrador real), los une al evento y
los pasa a En directo automáticamente. Al final imprime un resumen (puntos, lotes,
errores 5xx) — el criterio de aceptación del plan S4 es una simulación de 800
corredores / 30 min / 10% de pérdida de cobertura sin errores 5xx.
