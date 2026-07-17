import L from "leaflet";
import { resolverColorEstado, type EstadoTransmision } from "@empatelive/web-shared";
import { urlMedia } from "../api";
import type { PosicionPublica } from "./interpolacion";

const DIAMETRO_PX = 40;

/**
 * Marcador circular minimalista: foto de perfil en miniatura si el corredor
 * tiene una, o el dorsal si no la tiene — con un anillo del color semántico
 * de su estado (verde=transmitiendo, ámbar=sin_señal).
 */
export function construirIcono(posicion: PosicionPublica): L.DivIcon {
  const color = resolverColorEstado(posicion.estado as EstadoTransmision);
  const contenido = posicion.foto_url
    ? `<img src="${urlMedia(posicion.foto_url)}" alt="" />`
    : `<span>${posicion.dorsal}</span>`;

  return L.divIcon({
    className: "marcador-corredor",
    html: `<div class="marcador-corredor__anillo" style="border-color:${color}">${contenido}</div>`,
    iconSize: [DIAMETRO_PX, DIAMETRO_PX],
    iconAnchor: [DIAMETRO_PX / 2, DIAMETRO_PX / 2],
  });
}

/** Clave para saber si hay que reconstruir el icono (cambió foto o estado). */
export function claveIcono(posicion: PosicionPublica): string {
  return `${posicion.foto_url ?? ""}|${posicion.estado}|${posicion.dorsal}`;
}
