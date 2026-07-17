import type { Coordenada } from "./interpolacion";

/** Extrae los puntos de recorrido (`trkpt`) de un GPX (spec v10: trazado en rojo). */
export function extraerPuntosGpx(xmlTexto: string): Coordenada[] {
  const doc = new DOMParser().parseFromString(xmlTexto, "application/xml");
  if (doc.querySelector("parsererror")) return [];

  return Array.from(doc.getElementsByTagName("trkpt"))
    .map((nodo) => {
      const lat = Number.parseFloat(nodo.getAttribute("lat") ?? "");
      const lon = Number.parseFloat(nodo.getAttribute("lon") ?? "");
      return { lat, lon };
    })
    .filter((punto) => Number.isFinite(punto.lat) && Number.isFinite(punto.lon));
}
