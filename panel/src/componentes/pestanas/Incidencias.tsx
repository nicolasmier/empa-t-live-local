import { useEffect, useRef, useState } from "react";
import type { components } from "@empatelive/web-shared";
import { api } from "../../api";

type Incidencia = components["schemas"]["IncidenciaSalida"];
type Filtro = "todas" | "no_resueltas" | "resueltas";

const INTERVALO_SONDEO_MS = 8000;

function formatearFecha(iso: string): string {
  return new Date(iso).toLocaleString("es-ES");
}

export function Incidencias({ eventoId }: { eventoId: number }) {
  const [incidencias, setIncidencias] = useState<Incidencia[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [filtro, setFiltro] = useState<Filtro>("no_resueltas");
  const [nuevas, setNuevas] = useState(0);
  const [resolviendoId, setResolviendoId] = useState<number | null>(null);
  const vistasRef = useRef<Set<number> | null>(null);

  useEffect(() => {
    vistasRef.current = null;
    setNuevas(0);
    cargar(filtro);
    const id = setInterval(() => cargar(filtro), INTERVALO_SONDEO_MS);
    return () => clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [eventoId, filtro]);

  async function cargar(filtroActual: Filtro) {
    const resuelta = filtroActual === "todas" ? undefined : filtroActual === "resueltas";
    const { data, error } = await api.GET("/eventos/{evento_id}/incidencias", {
      params: { path: { evento_id: eventoId }, query: { resuelta } },
    });
    if (error) {
      setError("No se pudieron cargar las incidencias.");
      return;
    }
    setError(null);

    if (vistasRef.current === null) {
      vistasRef.current = new Set(data.map((i) => i.id));
    } else {
      const idsNuevas = data.filter((i) => !vistasRef.current!.has(i.id));
      if (idsNuevas.length > 0) {
        setNuevas((n) => n + idsNuevas.length);
        idsNuevas.forEach((i) => vistasRef.current!.add(i.id));
      }
    }
    setIncidencias(data);
  }

  async function alResolver(id: number) {
    setResolviendoId(id);
    await api.PUT("/incidencias/{incidencia_id}/resolver", {
      params: { path: { incidencia_id: id } },
    });
    setResolviendoId(null);
    await cargar(filtro);
  }

  return (
    <div className="bloque-pestana">
      {nuevas > 0 && (
        <div className="aviso-nuevas" onClick={() => setNuevas(0)} role="status">
          {nuevas} incidencia{nuevas > 1 ? "s" : ""} nueva{nuevas > 1 ? "s" : ""} desde que abriste esta vista.
        </div>
      )}

      <div className="filtros-linea">
        {(["no_resueltas", "resueltas", "todas"] as const).map((f) => (
          <button
            key={f}
            type="button"
            className={`enlace-nav ${filtro === f ? "enlace-nav--activo" : ""}`}
            onClick={() => setFiltro(f)}
          >
            {f === "no_resueltas" ? "No resueltas" : f === "resueltas" ? "Resueltas" : "Todas"}
          </button>
        ))}
      </div>

      {error && <p className="error">{error}</p>}
      {incidencias === null && !error && <p>Cargando…</p>}
      {incidencias && incidencias.length === 0 && (
        <p className="texto-vacio">No hay incidencias {filtro === "resueltas" ? "resueltas" : filtro === "no_resueltas" ? "abiertas" : ""} para este evento.</p>
      )}
      {incidencias && incidencias.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>Tipo</th>
              <th>Dorsal</th>
              <th>Descripción</th>
              <th>Creada</th>
              <th>Estado</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {incidencias.map((i) => (
              <tr key={i.id}>
                <td>{i.tipo === "sin_senal" ? "Sin señal" : i.tipo}</td>
                <td>{i.dorsal ?? "— (sistémica)"}</td>
                <td>{i.descripcion ?? "—"}</td>
                <td>{formatearFecha(i.creado_en)}</td>
                <td>
                  {i.resuelto_en ? (
                    <span className="insignia insignia--ok">Resuelta</span>
                  ) : (
                    <span className="insignia insignia--pendiente">Abierta</span>
                  )}
                </td>
                <td>
                  {!i.resuelto_en && (
                    <button type="button" onClick={() => alResolver(i.id)} disabled={resolviendoId === i.id}>
                      {resolviendoId === i.id ? "Resolviendo…" : "Marcar resuelta"}
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
