import { crearClienteAPI, resolverBaseUrlApi } from "@empatelive/web-shared";

export const BASE_URL = resolverBaseUrlApi(8000);

// La web pública nunca se autentica (Anexo B §6: lectura pública LAN).
export const api = crearClienteAPI(BASE_URL);

export function urlMedia(rutaRelativa: string): string {
  return `${BASE_URL}${rutaRelativa}`;
}
