import createClient from "openapi-fetch";
import type { paths } from "./api-tipos";

/** Cliente HTTP tipado desde `api/openapi.json` (evita divergencias silenciosas
 * de contrato entre el frontend y la API — plan W1). */
export function crearClienteAPI(baseUrl: string, obtenerToken?: () => string | null) {
  const cliente = createClient<paths>({ baseUrl });

  cliente.use({
    onRequest({ request }) {
      const token = obtenerToken?.();
      if (token) {
        request.headers.set("Authorization", `Bearer ${token}`);
      }
      return request;
    },
  });

  return cliente;
}

export type ClienteAPI = ReturnType<typeof crearClienteAPI>;
