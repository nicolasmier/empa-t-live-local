import { crearClienteAPI, resolverBaseUrlApi } from "@empatelive/web-shared";

const CLAVE_TOKEN = "empatelive_panel_token";

export function obtenerToken(): string | null {
  return localStorage.getItem(CLAVE_TOKEN);
}

export function guardarToken(token: string): void {
  localStorage.setItem(CLAVE_TOKEN, token);
}

export function borrarToken(): void {
  localStorage.removeItem(CLAVE_TOKEN);
}

const BASE_URL = resolverBaseUrlApi(8000);

export const api = crearClienteAPI(BASE_URL, obtenerToken);

/** El backend siempre responde `{ error: { code, message } }` (Anexo B §1);
 * este mensaje ya está redactado para un Administrador sin conocimiento
 * técnico, así que se muestra tal cual en vez de un genérico. */
export function mensajeError(error: unknown, alternativa: string): string {
  if (
    error &&
    typeof error === "object" &&
    "error" in error &&
    error.error &&
    typeof error.error === "object" &&
    "message" in error.error &&
    typeof error.error.message === "string"
  ) {
    return error.error.message;
  }
  return alternativa;
}

export function urlMedia(url: string | null | undefined): string | null {
  if (!url) return null;
  return url.startsWith("http") ? url : `${BASE_URL}${url}`;
}
