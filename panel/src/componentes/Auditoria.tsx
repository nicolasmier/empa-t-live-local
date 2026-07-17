import { useState } from "react";
import type { components } from "@empatelive/web-shared";
import { api } from "../api";

type Auditoria = components["schemas"]["AuditoriaSalida"];

const ACCIONES = [
  "evento_creado",
  "evento_actualizado",
  "evento_duplicado",
  "evento_cambio_estado",
  "distancia_creada",
  "distancia_actualizada",
  "gpx_subido",
  "corredores_importados",
  "cartel_subido",
  "patrocinador_creado",
  "patrocinador_actualizado",
  "noticia_creada",
  "noticia_actualizada",
  "incidencia_resuelta",
] as const;

function formatearFecha(iso: string): string {
  return new Date(iso).toLocaleString("es-ES");
}

export function Auditoria() {
  const [eventoId, setEventoId] = useState("");
  const [usuarioId, setUsuarioId] = useState("");
  const [accion, setAccion] = useState("");
  const [desde, setDesde] = useState("");
  const [hasta, setHasta] = useState("");
  const [resultados, setResultados] = useState<Auditoria[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [buscando, setBuscando] = useState(false);

  async function buscar() {
    setBuscando(true);
    setError(null);
    const { data, error } = await api.GET("/auditoria", {
      params: {
        query: {
          evento_id: eventoId ? Number(eventoId) : undefined,
          usuario_id: usuarioId ? Number(usuarioId) : undefined,
          accion: accion || undefined,
          desde: desde ? new Date(desde).toISOString() : undefined,
          hasta: hasta ? new Date(hasta).toISOString() : undefined,
        },
      },
    });
    setBuscando(false);
    if (error) {
      setError("No se pudo consultar la auditoría (¿tienes rol de Administrador?).");
      return;
    }
    setResultados(data);
  }

  return (
    <section className="panel-seccion">
      <h2>Auditoría</h2>

      <div className="formulario-tarjeta formulario-tarjeta--fila">
        <label>
          Evento (id)
          <input value={eventoId} onChange={(e) => setEventoId(e.target.value)} placeholder="p. ej. 1" />
        </label>
        <label>
          Usuario (id)
          <input value={usuarioId} onChange={(e) => setUsuarioId(e.target.value)} placeholder="p. ej. 1" />
        </label>
        <label>
          Acción
          <select value={accion} onChange={(e) => setAccion(e.target.value)}>
            <option value="">Todas</option>
            {ACCIONES.map((a) => (
              <option key={a} value={a}>
                {a}
              </option>
            ))}
          </select>
        </label>
        <label>
          Desde
          <input type="datetime-local" value={desde} onChange={(e) => setDesde(e.target.value)} />
        </label>
        <label>
          Hasta
          <input type="datetime-local" value={hasta} onChange={(e) => setHasta(e.target.value)} />
        </label>
        <button type="button" onClick={buscar} disabled={buscando}>
          {buscando ? "Buscando…" : "Buscar"}
        </button>
      </div>

      {error && <p className="error">{error}</p>}
      {resultados === null && !error && <p className="texto-vacio">Aplica un filtro y pulsa Buscar.</p>}
      {resultados && resultados.length === 0 && <p className="texto-vacio">Sin resultados.</p>}
      {resultados && resultados.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>Fecha</th>
              <th>Usuario</th>
              <th>Acción</th>
              <th>Entidad</th>
              <th>Detalle</th>
            </tr>
          </thead>
          <tbody>
            {resultados.map((fila) => (
              <tr key={fila.id}>
                <td>{formatearFecha(fila.creado_en)}</td>
                <td>{fila.usuario_id}</td>
                <td>{fila.accion}</td>
                <td>
                  {fila.entidad_tipo} #{fila.entidad_id}
                </td>
                <td>{fila.detalle ? JSON.stringify(fila.detalle) : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
