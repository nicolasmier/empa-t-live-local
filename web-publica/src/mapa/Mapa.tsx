import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { useEffect, useRef } from "react";
import { urlMedia } from "../api";
import { extraerPuntosGpx } from "./gpx";
import { claveIcono, construirIcono } from "./icono";
import type { Coordenada, EstadoMarcador, PosicionPublica } from "./interpolacion";
import "./Mapa.css";

export interface BBox {
  norte: number;
  sur: number;
  este: number;
  oeste: number;
}

export interface MapaProps {
  estado: ReadonlyMap<number, EstadoMarcador>;
  gpxUrl: string | null;
  bbox: BBox | null;
  mostrarCorredor: (posicion: PosicionPublica) => boolean;
  onSeleccionarCorredor: (posicion: PosicionPublica) => void;
}

const DURACION_ANIMACION_MS = 4000;

interface AnimacionActiva {
  desde: Coordenada;
  hasta: Coordenada;
  inicio: number;
}

// La proporción del contenedor se ajusta a la forma real del recorrido (en
// vez de una altura fija) para que el mapa se ciña al GPX y no sobre área
// de mapa sin usar a los lados o arriba/abajo. Los límites evitan un
// contenedor absurdamente alto/ancho en recorridos muy alargados en una
// sola dirección (p. ej. una línea casi recta norte-sur).
function calcularProporcion(bbox: BBox): number {
  const latMedia = (bbox.norte + bbox.sur) / 2;
  const anchoGrados = (bbox.este - bbox.oeste) * Math.cos((latMedia * Math.PI) / 180);
  const altoGrados = bbox.norte - bbox.sur;
  if (altoGrados <= 0) return 16 / 9;
  return Math.min(2.4, Math.max(0.6, anchoGrados / altoGrados));
}

// Límite de alejamiento (no de acercamiento): el uso real en carrera es
// acercar donde se acumulan corredores, no alejar más allá del recorrido.
const MARGEN_MAXIMO_ALEJAMIENTO_M = 500;
const METROS_POR_GRADO_LAT = 111_320;

function expandirBboxMetros(bbox: BBox, metros: number): BBox {
  const latMedia = (bbox.norte + bbox.sur) / 2;
  const metrosPorGradoLon = METROS_POR_GRADO_LAT * Math.cos((latMedia * Math.PI) / 180);
  const deltaLat = metros / METROS_POR_GRADO_LAT;
  const deltaLon = metros / metrosPorGradoLon;
  return {
    norte: bbox.norte + deltaLat,
    sur: bbox.sur - deltaLat,
    este: bbox.este + deltaLon,
    oeste: bbox.oeste - deltaLon,
  };
}

function bboxALimites(bbox: BBox): L.LatLngBounds {
  return L.latLngBounds([bbox.sur, bbox.oeste], [bbox.norte, bbox.este]);
}

// Fija cuánto se puede alejar el mapa (máximo `MARGEN_MAXIMO_ALEJAMIENTO_M`
// más allá del punto más lejano del recorrido): `setMaxBounds` limita el
// desplazamiento y `minZoom` (calculado con el tamaño real del contenedor)
// impide alejar más allá de ese límite. No restringe acercar, que es el uso
// real (ver muchos corredores agrupados en un punto).
function limitarAlejamiento(mapa: L.Map, bbox: BBox): L.LatLngBounds {
  const limitesExpandidos = bboxALimites(expandirBboxMetros(bbox, MARGEN_MAXIMO_ALEJAMIENTO_M));
  mapa.setMaxBounds(limitesExpandidos);
  mapa.setMinZoom(mapa.getBoundsZoom(limitesExpandidos, false));
  return limitesExpandidos;
}

export function Mapa({
  estado,
  gpxUrl,
  bbox,
  mostrarCorredor,
  onSeleccionarCorredor,
}: MapaProps) {
  const contenedorRef = useRef<HTMLDivElement | null>(null);
  const mapaRef = useRef<L.Map | null>(null);
  const marcadoresRef = useRef<Map<number, L.Marker>>(new Map());
  const claveIconoRef = useRef<Map<number, string>>(new Map());
  const animacionesRef = useRef<Map<number, AnimacionActiva>>(new Map());
  const limitesExpandidosRef = useRef<L.LatLngBounds | null>(null);

  // Inicializa el mapa una sola vez por montaje (App.tsx remonta con `key`
  // al cambiar de distancia, así que cada pestaña tiene su propio mapa limpio).
  useEffect(() => {
    if (!contenedorRef.current || mapaRef.current) return;
    const mapa = L.map(contenedorRef.current, {
      zoomControl: true,
      attributionControl: true,
      maxBoundsViscosity: 1.0,
    });
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "© OpenStreetMap",
      maxZoom: 19,
    }).addTo(mapa);
    mapa.setView([40.4168, -3.7038], 12);
    mapaRef.current = mapa;

    // La proporción del contenedor cambia con el bbox (ver más abajo), lo que
    // Leaflet no detecta solo: sin este observer, el mapa queda recortado o
    // con huecos en gris hasta el siguiente resize manual de la ventana. El
    // zoom mínimo también depende del tamaño del contenedor en píxeles, así
    // que se recalcula aquí también.
    const observador = new ResizeObserver(() => {
      mapa.invalidateSize();
      if (limitesExpandidosRef.current) {
        mapa.setMinZoom(mapa.getBoundsZoom(limitesExpandidosRef.current, false));
      }
    });
    observador.observe(contenedorRef.current);

    return () => {
      observador.disconnect();
      mapa.remove();
      mapaRef.current = null;
    };
  }, []);

  // Ajusta la proporción del contenedor a la forma del recorrido y encuadra
  // la vista a su bbox exacto en cuanto se conoce (spec: que no sobre mapa
  // sin usar alrededor de la ruta).
  useEffect(() => {
    const mapa = mapaRef.current;
    if (!mapa || !bbox || !contenedorRef.current) return;
    contenedorRef.current.style.aspectRatio = String(calcularProporcion(bbox));
    mapa.invalidateSize();
    mapa.fitBounds(bboxALimites(bbox), { padding: [12, 12] });
    limitesExpandidosRef.current = limitarAlejamiento(mapa, bbox);
  }, [bbox]);

  // Trazado del GPX en rojo (spec v10 RF-012).
  useEffect(() => {
    const mapa = mapaRef.current;
    if (!mapa || !gpxUrl) return;
    let cancelado = false;
    let capa: L.Polyline | null = null;

    fetch(urlMedia(gpxUrl))
      .then((respuesta) => respuesta.text())
      .then((texto) => {
        if (cancelado) return;
        const puntos = extraerPuntosGpx(texto);
        if (puntos.length === 0) return;
        capa = L.polyline(
          puntos.map((p) => [p.lat, p.lon] as [number, number]),
          { color: "#c72f2f", weight: 6, opacity: 0.9 },
        ).addTo(mapa);
        if (!bbox) {
          // Igual que el efecto de bbox: sin un bbox precalculado (GPX sin
          // reprocesar), se calcula la proporción a partir del propio trazado.
          const limites = capa.getBounds();
          const bboxTrazado: BBox = {
            norte: limites.getNorth(),
            sur: limites.getSouth(),
            este: limites.getEast(),
            oeste: limites.getWest(),
          };
          if (contenedorRef.current) {
            contenedorRef.current.style.aspectRatio = String(calcularProporcion(bboxTrazado));
            mapa.invalidateSize();
          }
          mapa.fitBounds(limites, { padding: [12, 12] });
          limitesExpandidosRef.current = limitarAlejamiento(mapa, bboxTrazado);
        }

        // Vista inicial: centrada en el INICIO del track (la salida queda
        // siempre visible al abrir la web) y un punto más acercada que el
        // encuadre completo, dejando margen para alejar (hasta ver el recorrido
        // entero, minZoom) o acercar todavía más.
        const zoomCompleto = mapa.getBoundsZoom(capa.getBounds(), false);
        mapa.setView([puntos[0].lat, puntos[0].lon], Math.min(19, zoomCompleto + 1));
      })
      .catch(() => {
        // El trazado es decorativo: si falla la carga, el mapa sigue
        // funcionando con los marcadores (spec v10 §13: degradación suave).
      });

    return () => {
      cancelado = true;
      if (capa) mapa.removeLayer(capa);
    };
  }, [gpxUrl, bbox]);

  // Sincroniza los marcadores con el último estado de posiciones.
  useEffect(() => {
    const mapa = mapaRef.current;
    if (!mapa) return;

    const idsVisibles = new Set<number>();

    for (const [id, marcadorEstado] of estado) {
      if (!marcadorEstado.hasta || !mostrarCorredor(marcadorEstado.datos)) continue;
      idsVisibles.add(id);

      const clave = claveIcono(marcadorEstado.datos);
      let marker = marcadoresRef.current.get(id);

      if (!marker) {
        marker = L.marker([marcadorEstado.hasta.lat, marcadorEstado.hasta.lon], {
          icon: construirIcono(marcadorEstado.datos),
        });
        marker.addTo(mapa);
        marcadoresRef.current.set(id, marker);
        claveIconoRef.current.set(id, clave);
      } else if (claveIconoRef.current.get(id) !== clave) {
        marker.setIcon(construirIcono(marcadorEstado.datos));
        claveIconoRef.current.set(id, clave);
      }

      marker.off("click");
      marker.on("click", () => onSeleccionarCorredor(marcadorEstado.datos));

      if (marcadorEstado.saltar || !marcadorEstado.desde) {
        marker.setLatLng([marcadorEstado.hasta.lat, marcadorEstado.hasta.lon]);
        animacionesRef.current.delete(id);
      } else {
        animacionesRef.current.set(id, {
          desde: marcadorEstado.desde,
          hasta: marcadorEstado.hasta,
          inicio: performance.now(),
        });
      }
    }

    for (const [id, marker] of marcadoresRef.current) {
      if (!idsVisibles.has(id)) {
        mapa.removeLayer(marker);
        marcadoresRef.current.delete(id);
        animacionesRef.current.delete(id);
        claveIconoRef.current.delete(id);
      }
    }
  }, [estado, mostrarCorredor, onSeleccionarCorredor]);

  // Bucle de animación: interpola linealmente las posiciones "en vuelo".
  useEffect(() => {
    let idRaf: number;

    function paso(ahora: number) {
      for (const [id, animacion] of animacionesRef.current) {
        const marker = marcadoresRef.current.get(id);
        if (!marker) {
          animacionesRef.current.delete(id);
          continue;
        }
        const t = Math.min(1, (ahora - animacion.inicio) / DURACION_ANIMACION_MS);
        const lat = animacion.desde.lat + (animacion.hasta.lat - animacion.desde.lat) * t;
        const lon = animacion.desde.lon + (animacion.hasta.lon - animacion.desde.lon) * t;
        marker.setLatLng([lat, lon]);
        if (t >= 1) animacionesRef.current.delete(id);
      }
      idRaf = requestAnimationFrame(paso);
    }

    idRaf = requestAnimationFrame(paso);
    return () => cancelAnimationFrame(idRaf);
  }, []);

  return <div ref={contenedorRef} className="mapa" />;
}
