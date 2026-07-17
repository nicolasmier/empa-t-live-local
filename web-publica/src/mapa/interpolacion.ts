import type { components } from "@empatelive/web-shared";

export type PosicionPublica = components["schemas"]["PosicionPublica"];
export type Coordenada = { lat: number; lon: number };

export interface EstadoMarcador {
  inscripcionId: number;
  datos: PosicionPublica;
  /** Posición desde la que animar. `null` = no animar (aparecer directo). */
  desde: Coordenada | null;
  /** Posición final del marcador tras esta actualización. */
  hasta: Coordenada | null;
  /** true = el renderer debe fijar el marcador en `hasta` sin animar. */
  saltar: boolean;
}

// Por encima de esta distancia entre la posición anterior y la nueva, se
// considera un "salto grande legítimo" (lote sincronizado tras pérdida de
// cobertura) y se corta directo en vez de animar (spec v10 plan W2, punto 3):
// ningún corredor cubre 150 m entre dos sondeos normales (3-5 s) corriendo.
export const UMBRAL_SALTO_METROS = 150;

function distanciaMetros(a: Coordenada, b: Coordenada): number {
  const R = 6371000;
  const rLat1 = (a.lat * Math.PI) / 180;
  const rLat2 = (b.lat * Math.PI) / 180;
  const dLat = ((b.lat - a.lat) * Math.PI) / 180;
  const dLon = ((b.lon - a.lon) * Math.PI) / 180;
  const h =
    Math.sin(dLat / 2) ** 2 + Math.cos(rLat1) * Math.cos(rLat2) * Math.sin(dLon / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(h));
}

function coordenadaDe(posicion: PosicionPublica): Coordenada | null {
  if (posicion.latitud === null || posicion.longitud === null) return null;
  return { lat: posicion.latitud, lon: posicion.longitud };
}

/**
 * Reductor puro: dado el estado de marcadores mostrado hasta ahora y el
 * último sondeo de posiciones, calcula el siguiente estado de animación.
 *
 * Cubre los 4 casos límite obligatorios del plan W2:
 * 1. Corredor nuevo → aparece en su posición, sin animar desde (0,0).
 * 2. Corredor sin_senal → se congela en su última posición conocida.
 * 3. Fallo de sondeo y reconexión → no se llama a este reductor durante el
 *    fallo (el estado previo se conserva tal cual); al reconectar, esta
 *    misma función decide animar o saltar según la distancia real recorrida
 *    durante el hueco — sin tratamiento especial para "cuántos sondeos" se
 *    perdieron.
 * 4. Salto grande legítimo (lote sincronizado) → transición directa
 *    (`saltar: true`), nunca recorre el hueco a cámara lenta.
 */
export function siguienteEstadoMarcadores(
  anterior: ReadonlyMap<number, EstadoMarcador>,
  nuevasPosiciones: readonly PosicionPublica[],
): Map<number, EstadoMarcador> {
  const siguiente = new Map<number, EstadoMarcador>();

  for (const posicion of nuevasPosiciones) {
    const previo = anterior.get(posicion.inscripcion_id);
    const nuevaPos = coordenadaDe(posicion);

    if (!previo) {
      siguiente.set(posicion.inscripcion_id, {
        inscripcionId: posicion.inscripcion_id,
        datos: posicion,
        desde: null,
        hasta: nuevaPos,
        saltar: true,
      });
      continue;
    }

    if (posicion.estado === "sin_senal") {
      siguiente.set(posicion.inscripcion_id, {
        inscripcionId: posicion.inscripcion_id,
        datos: posicion,
        desde: previo.hasta,
        hasta: previo.hasta,
        saltar: true,
      });
      continue;
    }

    const posicionAnterior = previo.hasta;
    const sinCambios =
      !nuevaPos || previo.datos.timestamp_dispositivo === posicion.timestamp_dispositivo;

    if (sinCambios) {
      siguiente.set(posicion.inscripcion_id, {
        inscripcionId: posicion.inscripcion_id,
        datos: posicion,
        desde: posicionAnterior,
        hasta: posicionAnterior ?? nuevaPos,
        saltar: true,
      });
      continue;
    }

    const distancia = posicionAnterior ? distanciaMetros(posicionAnterior, nuevaPos) : Infinity;
    const esSaltoGrande = distancia > UMBRAL_SALTO_METROS;

    siguiente.set(posicion.inscripcion_id, {
      inscripcionId: posicion.inscripcion_id,
      datos: posicion,
      desde: posicionAnterior,
      hasta: nuevaPos,
      saltar: esSaltoGrande || posicionAnterior === null,
    });
  }

  return siguiente;
}
