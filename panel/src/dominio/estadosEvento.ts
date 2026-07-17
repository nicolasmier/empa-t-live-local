// Espejo en TS de api/app/dominio/estados_evento.py (spec v10 §11): avance en
// orden a cualquier estado posterior; retroceso permitido solo de un paso;
// "archivado" es terminal.
export const ORDEN_ESTADOS = [
  "borrador",
  "publicado",
  "preparacion",
  "en_directo",
  "finalizado",
  "archivado",
] as const;

export type EstadoEvento = (typeof ORDEN_ESTADOS)[number];

export const ETIQUETAS_ESTADO: Record<EstadoEvento, string> = {
  borrador: "Borrador",
  publicado: "Publicado",
  preparacion: "Preparación",
  en_directo: "En directo",
  finalizado: "Finalizado",
  archivado: "Archivado",
};

// Transiciones que requieren confirmación explícita (plan W3 §3): tienen
// efectos difíciles de deshacer (revocan tokens, disparan backup, publican
// el evento a corredores/web pública).
const _TRANSICIONES_SENSIBLES = new Set(["en_directo", "finalizado"]);

export function transicionSensible(destino: EstadoEvento): boolean {
  return _TRANSICIONES_SENSIBLES.has(destino);
}

export function transicionesValidas(origen: EstadoEvento): EstadoEvento[] {
  const i = ORDEN_ESTADOS.indexOf(origen);
  if (i === -1 || origen === "archivado") return [];
  const destinos: EstadoEvento[] = ORDEN_ESTADOS.slice(i + 1);
  if (i > 0) destinos.unshift(ORDEN_ESTADOS[i - 1]);
  return destinos;
}
