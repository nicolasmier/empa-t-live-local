import { useEffect, useRef, useState } from "react";
import { api } from "../api";
import { siguienteEstadoMarcadores, type EstadoMarcador } from "./interpolacion";

const INTERVALO_SONDEO_MS = 4000; // spec v10 RF-015: cada 3-5 s

export function usePosicionesPolling(eventoId: number | null, distanciaId: number | null) {
  const [estado, setEstado] = useState<Map<number, EstadoMarcador>>(new Map());
  const [conectado, setConectado] = useState(true);
  const estadoRef = useRef(estado);
  estadoRef.current = estado;

  useEffect(() => {
    if (eventoId === null || distanciaId === null) return;
    const idEvento = eventoId;
    const idDistancia = distanciaId;
    let cancelado = false;

    async function sondear() {
      // Caso límite 3: fallo de sondeo — se conserva el último estado mostrado
      // tal cual, sin borrar ni resetear nada; al reconectar, el siguiente
      // sondeo con éxito decide animar o saltar con normalidad. El try/catch
      // es necesario además del chequeo de `error`: un corte real de conexión
      // (servidor caído, no solo un 4xx/5xx) hace que `api.GET` rechace la
      // promesa en vez de resolver con `{ error }` — sin esto, se escapaba
      // como una excepción no capturada (visto en el ensayo general al
      // reiniciar el contenedor de la API a mitad de una carrera simulada).
      try {
        const { data, error } = await api.GET(
          "/eventos/{evento_id}/distancias/{distancia_id}/posiciones",
          { params: { path: { evento_id: idEvento, distancia_id: idDistancia } } },
        );
        if (cancelado) return;

        if (error) {
          setConectado(false);
          return;
        }

        setConectado(true);
        setEstado((anterior) => siguienteEstadoMarcadores(anterior, data));
      } catch {
        if (!cancelado) setConectado(false);
      }
    }

    sondear();
    const id = setInterval(sondear, INTERVALO_SONDEO_MS);
    return () => {
      cancelado = true;
      clearInterval(id);
    };
  }, [eventoId, distanciaId]);

  return { estado, conectado };
}
