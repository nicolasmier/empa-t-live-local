import { describe, expect, it } from "vitest";
import { extraerPuntosGpx } from "./gpx";

const GPX_VALIDO = `<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1">
  <trk>
    <trkseg>
      <trkpt lat="40.000000" lon="-3.500000"><ele>600</ele></trkpt>
      <trkpt lat="40.001000" lon="-3.501000"></trkpt>
    </trkseg>
  </trk>
</gpx>`;

describe("extraerPuntosGpx", () => {
  it("extrae todos los puntos de recorrido en orden", () => {
    const puntos = extraerPuntosGpx(GPX_VALIDO);
    expect(puntos).toEqual([
      { lat: 40.0, lon: -3.5 },
      { lat: 40.001, lon: -3.501 },
    ]);
  });

  it("devuelve una lista vacía para XML no válido", () => {
    expect(extraerPuntosGpx("esto no es xml")).toEqual([]);
  });

  it("devuelve una lista vacía para un GPX sin puntos", () => {
    const sinPuntos = `<?xml version="1.0"?><gpx><trk><trkseg></trkseg></trk></gpx>`;
    expect(extraerPuntosGpx(sinPuntos)).toEqual([]);
  });
});
