import { describe, expect, it } from "vitest";
import {
  siguienteEstadoMarcadores,
  UMBRAL_SALTO_METROS,
  type EstadoMarcador,
  type PosicionPublica,
} from "./interpolacion";

function crearPosicion(overrides: Partial<PosicionPublica> = {}): PosicionPublica {
  return {
    inscripcion_id: 1,
    dorsal: "101",
    nombre: "Ana",
    apellidos: "Gómez",
    club: null,
    foto_url: null,
    latitud: 40.0,
    longitud: -3.5,
    timestamp_dispositivo: "2026-07-17T10:00:00Z",
    estado: "transmitiendo",
    ...overrides,
  };
}

describe("caso límite 1: corredor nuevo", () => {
  it("aparece directamente en su posición, sin animar desde ningún sitio", () => {
    const posicion = crearPosicion();
    const siguiente = siguienteEstadoMarcadores(new Map(), [posicion]);

    const marcador = siguiente.get(1)!;
    expect(marcador.desde).toBeNull();
    expect(marcador.hasta).toEqual({ lat: 40.0, lon: -3.5 });
    expect(marcador.saltar).toBe(true);
  });
});

describe("caso límite 2: corredor sin_senal", () => {
  it("se congela en su última posición conocida, sin animar", () => {
    const anterior = new Map<number, EstadoMarcador>([
      [
        1,
        {
          inscripcionId: 1,
          datos: crearPosicion(),
          desde: { lat: 39.9, lon: -3.6 },
          hasta: { lat: 40.0, lon: -3.5 },
          saltar: false,
        },
      ],
    ]);

    const posicionSinSenal = crearPosicion({
      estado: "sin_senal",
      // El backend deja de mandar lat/lon en algunos casos; el marcador debe
      // seguir mostrando la última posición conocida, no desaparecer.
      latitud: null,
      longitud: null,
    });

    const siguiente = siguienteEstadoMarcadores(anterior, [posicionSinSenal]);
    const marcador = siguiente.get(1)!;

    expect(marcador.hasta).toEqual({ lat: 40.0, lon: -3.5 });
    expect(marcador.desde).toEqual({ lat: 40.0, lon: -3.5 });
    expect(marcador.saltar).toBe(true);
  });
});

describe("caso límite 3: fallo de sondeo y reconexión", () => {
  it("un sondeo fallido no se procesa; al reconectar, un cambio pequeño anima con normalidad", () => {
    const t0 = crearPosicion({ latitud: 40.0, longitud: -3.5 });
    let estado = siguienteEstadoMarcadores(new Map(), [t0]);

    // El sondeo intermedio falla: la app no llama al reductor, el estado no cambia.
    expect(estado.get(1)!.hasta).toEqual({ lat: 40.0, lon: -3.5 });

    // Reconexión: llega un cambio pequeño y realista (unos metros).
    const t2 = crearPosicion({
      latitud: 40.0002,
      longitud: -3.5002,
      timestamp_dispositivo: "2026-07-17T10:00:20Z",
    });
    estado = siguienteEstadoMarcadores(estado, [t2]);
    const marcador = estado.get(1)!;

    expect(marcador.desde).toEqual({ lat: 40.0, lon: -3.5 });
    expect(marcador.hasta).toEqual({ lat: 40.0002, lon: -3.5002 });
    expect(marcador.saltar).toBe(false); // se anima, no es un salto
  });

  it("no cambia nada si el sondeo devuelve exactamente el mismo timestamp (sin datos nuevos)", () => {
    const t0 = crearPosicion();
    let estado = siguienteEstadoMarcadores(new Map(), [t0]);
    estado = siguienteEstadoMarcadores(estado, [t0]);

    const marcador = estado.get(1)!;
    expect(marcador.hasta).toEqual({ lat: 40.0, lon: -3.5 });
    expect(marcador.saltar).toBe(true);
  });
});

describe("caso límite 4: salto grande legítimo (lote sincronizado)", () => {
  it("corta directo a la nueva posición en vez de animar por el hueco", () => {
    const t0 = crearPosicion({ latitud: 40.0, longitud: -3.5 });
    let estado = siguienteEstadoMarcadores(new Map(), [t0]);

    // Tras 15 min sin cobertura, el dispositivo manda un lote y la posición
    // salta varios kilómetros de golpe.
    const trasSincronizar = crearPosicion({
      latitud: 40.03,
      longitud: -3.53,
      timestamp_dispositivo: "2026-07-17T10:15:00Z",
    });
    estado = siguienteEstadoMarcadores(estado, [trasSincronizar]);
    const marcador = estado.get(1)!;

    expect(marcador.saltar).toBe(true);
    expect(marcador.hasta).toEqual({ lat: 40.03, lon: -3.53 });
  });

  it("el umbral de salto es coherente con un ritmo de carrera realista", () => {
    // ~15 km/h durante 20 s ≈ 83 m: por debajo del umbral, no es un salto.
    expect(UMBRAL_SALTO_METROS).toBeGreaterThan(83);
  });
});
