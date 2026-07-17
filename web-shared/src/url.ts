/** Los enlaces de patrocinadores se escriben a mano en el panel y es habitual
 * que falte el esquema (p. ej. "mayador.com" en vez de "https://mayador.com")
 * — sin esto, el navegador lo trata como una ruta relativa del propio sitio
 * en vez de una URL externa y el enlace no lleva a ningún sitio real. */
export function normalizarUrlExterna(url: string): string {
  const limpia = url.trim();
  return /^https?:\/\//i.test(limpia) ? limpia : `https://${limpia}`;
}

/** Resuelve la URL de la API en tiempo de ejecución a partir del host desde el
 * que se ha cargado la página, en vez de fijarla en el build (`VITE_API_URL`
 * sigue disponible como override). Panel y web pública son LAN (spec v10 §9):
 * se abren desde dispositivos distintos al PC servidor, así que un
 * "http://localhost:8000" fijado en el build apuntaría al propio dispositivo
 * del espectador/Administrador, no al servidor. */
export function resolverBaseUrlApi(puertoPorDefecto: number): string {
  const override = import.meta.env.VITE_API_URL as string | undefined;
  if (override) return override;
  if (typeof window === "undefined") return `http://localhost:${puertoPorDefecto}`;
  return `${window.location.protocol}//${window.location.hostname}:${puertoPorDefecto}`;
}
