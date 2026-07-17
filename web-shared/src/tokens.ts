// Semántica de color (spec v10 Anexo C): verde = transmitiendo, ámbar/gris =
// sin señal. El rojo queda reservado para el futuro botón SOS (v1.1) — no
// reutilizar para otro significado aunque parezca conveniente.
export const COLOR_TRANSMITIENDO = "#1a9b52";
export const COLOR_SIN_SENAL = "#c78500";
export const COLOR_RESERVADO_SOS = "#c72f2f";

export type EstadoTransmision = "transmitiendo" | "sin_senal";

/** `colores_config` del evento (Anexo A, JSON libre) puede sobrescribir la
 * paleta, pero la asociación semántica (verde=transmitiendo) se conserva. */
export interface ColoresConfig {
  transmitiendo?: string;
  sin_senal?: string;
}

export function resolverColorEstado(
  estado: EstadoTransmision,
  coloresConfig?: ColoresConfig | null,
): string {
  if (estado === "transmitiendo") {
    return coloresConfig?.transmitiendo ?? COLOR_TRANSMITIENDO;
  }
  return coloresConfig?.sin_senal ?? COLOR_SIN_SENAL;
}

// Legibilidad de la web pública (spec v10 Anexo C): dorsales ≥24px sobre el
// mapa, cabecera ≥32px, tipografía estándar para launcher/panel.
export const TIPOGRAFIA = {
  familia: "Inter, Avenir, Helvetica, Arial, sans-serif",
  tamanoCabeceraMinPx: 32,
  tamanoDorsalMinPx: 24,
} as const;

// Paleta de marca (muestreada de cabeceralogo.jpg): azul oscuro, look moderno
// y minimalista — superficies claras y sin bordes/sombras marcados, el azul
// se reserva para cabecera, acentos y estados interactivos.
export const MARCA = {
  azulOscuro: "#0A1240",
  azul: "#0F2472",
  azulAcento: "#3D6BF0",
  texto: "#161A2B",
  textoSuave: "#6B7280",
  superficie: "#FFFFFF",
  fondo: "#F5F6FA",
  borde: "#E6E8EF",
} as const;
