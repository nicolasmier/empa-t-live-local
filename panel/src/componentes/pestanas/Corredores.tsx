import { useEffect, useRef, useState } from "react";
import { resolverColorEstado, type components } from "@empatelive/web-shared";
import { api, mensajeError } from "../../api";

type Distancia = components["schemas"]["DistanciaSalida"];
type ImportacionResultado = components["schemas"]["ImportacionResultado"];
type PosicionPublica = components["schemas"]["PosicionPublica"];

interface Props {
  eventoId: number;
  rolAdmin: boolean;
}

export function Corredores({ eventoId, rolAdmin }: Props) {
  const [distancias, setDistancias] = useState<Distancia[]>([]);
  const [distanciaId, setDistanciaId] = useState<number | null>(null);
  const [corredores, setCorredores] = useState<PosicionPublica[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [importando, setImportando] = useState(false);
  const [errorImportacion, setErrorImportacion] = useState<string | null>(null);
  const [informe, setInforme] = useState<ImportacionResultado | null>(null);
  const inputArchivo = useRef<HTMLInputElement | null>(null);

  const [seleccionados, setSeleccionados] = useState<Set<number>>(new Set());
  const [editandoId, setEditandoId] = useState<number | null>(null);
  const [borrandoId, setBorrandoId] = useState<number | null>(null);
  const [confirmando, setConfirmando] = useState<"uno" | "bloque" | null>(null);
  const [objetivoBorrado, setObjetivoBorrado] = useState<number | null>(null);
  const [borrandoBloque, setBorrandoBloque] = useState(false);

  useEffect(() => {
    async function cargarDistancias() {
      const { data, error } = await api.GET("/eventos/{evento_id}/distancias", {
        params: { path: { evento_id: eventoId } },
      });
      if (error || !data) return;
      setDistancias(data);
      if (data.length > 0) setDistanciaId(data[0].id);
    }
    cargarDistancias();
  }, [eventoId]);

  useEffect(() => {
    setSeleccionados(new Set());
    setEditandoId(null);
    if (distanciaId !== null) cargarCorredores(distanciaId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [distanciaId]);

  async function cargarCorredores(id: number) {
    setError(null);
    const { data, error } = await api.GET(
      "/eventos/{evento_id}/distancias/{distancia_id}/posiciones",
      { params: { path: { evento_id: eventoId, distancia_id: id } } },
    );
    if (error) {
      setError("No se pudo cargar la tabla de corredores.");
      return;
    }
    setCorredores(data);
  }

  async function alImportar(archivo: File) {
    if (distanciaId === null) return;
    setImportando(true);
    setErrorImportacion(null);
    setInforme(null);
    const formData = new FormData();
    formData.append("archivo", archivo);
    const { data, error } = await api.POST("/distancias/{distancia_id}/corredores/importar", {
      params: { path: { distancia_id: distanciaId } },
      body: formData as unknown as { archivo: string },
    });
    setImportando(false);
    if (inputArchivo.current) inputArchivo.current.value = "";
    if (error) {
      setErrorImportacion(mensajeError(error, "No se pudo importar el fichero."));
      return;
    }
    setInforme(data ?? null);
    await cargarCorredores(distanciaId);
  }

  async function alGuardarEdicion(
    inscripcionId: number,
    datos: { dorsal: string; nombre: string; apellidos: string; club: string },
  ) {
    if (distanciaId === null) return;
    const { error } = await api.PUT("/distancias/{distancia_id}/corredores/{inscripcion_id}", {
      params: { path: { distancia_id: distanciaId, inscripcion_id: inscripcionId } },
      body: {
        dorsal: datos.dorsal,
        nombre: datos.nombre,
        apellidos: datos.apellidos,
        club: datos.club || null,
      },
    });
    if (error) {
      return mensajeError(error, "No se pudo guardar el corredor.");
    }
    setEditandoId(null);
    await cargarCorredores(distanciaId);
    return null;
  }

  async function alBorrarUno(inscripcionId: number) {
    if (distanciaId === null) return;
    setBorrandoId(inscripcionId);
    await api.DELETE("/distancias/{distancia_id}/corredores/{inscripcion_id}", {
      params: { path: { distancia_id: distanciaId, inscripcion_id: inscripcionId } },
    });
    setBorrandoId(null);
    setConfirmando(null);
    setObjetivoBorrado(null);
    await cargarCorredores(distanciaId);
  }

  async function alBorrarSeleccionados() {
    if (distanciaId === null || seleccionados.size === 0) return;
    setBorrandoBloque(true);
    await api.POST("/distancias/{distancia_id}/corredores/eliminar", {
      params: { path: { distancia_id: distanciaId } },
      body: { inscripcion_ids: [...seleccionados] },
    });
    setBorrandoBloque(false);
    setConfirmando(null);
    setSeleccionados(new Set());
    await cargarCorredores(distanciaId);
  }

  function alternarSeleccion(id: number) {
    setSeleccionados((prev) => {
      const siguiente = new Set(prev);
      if (siguiente.has(id)) siguiente.delete(id);
      else siguiente.add(id);
      return siguiente;
    });
  }

  function alternarSeleccionTodos() {
    if (!corredores) return;
    setSeleccionados((prev) =>
      prev.size === corredores.length ? new Set() : new Set(corredores.map((c) => c.inscripcion_id)),
    );
  }

  if (distancias.length === 0) {
    return <p className="texto-vacio">Crea antes al menos una distancia en la pestaña Distancias.</p>;
  }

  return (
    <div className="bloque-pestana">
      <label className="selector-distancia">
        Distancia
        <select
          value={distanciaId ?? ""}
          onChange={(e) => setDistanciaId(Number(e.target.value))}
        >
          {distancias.map((d) => (
            <option key={d.id} value={d.id}>
              {d.nombre}
            </option>
          ))}
        </select>
      </label>

      {rolAdmin && distanciaId !== null && (
        <div className="formulario-tarjeta">
          <label>
            Importar Excel (email, nombre, apellidos, dorsal; club opcional)
            <input
              ref={inputArchivo}
              type="file"
              accept=".xlsx"
              disabled={importando}
              onChange={(e) => {
                const archivo = e.target.files?.[0];
                if (archivo) alImportar(archivo);
              }}
            />
          </label>
          {importando && <p>Importando…</p>}
          {errorImportacion && <p className="error">{errorImportacion}</p>}
        </div>
      )}

      {informe && (
        <div className="informe-importacion">
          <p>
            {informe.total_filas} filas · <span className="aviso-ok">{informe.creados} creados</span> ·{" "}
            <span className="aviso-ok">{informe.actualizados} actualizados</span> ·{" "}
            {informe.sin_cambios} sin cambios ·{" "}
            <span className={informe.errores > 0 ? "error" : undefined}>{informe.errores} errores</span>
          </p>
          {informe.filas.some((f) => f.estado === "error") && (
            <table className="tabla-compacta">
              <thead>
                <tr>
                  <th>Fila</th>
                  <th>Email</th>
                  <th>Dorsal</th>
                  <th>Motivo</th>
                </tr>
              </thead>
              <tbody>
                {informe.filas
                  .filter((f) => f.estado === "error")
                  .map((f) => (
                    <tr key={f.fila}>
                      <td>{f.fila}</td>
                      <td>{f.email ?? "—"}</td>
                      <td>{f.dorsal ?? "—"}</td>
                      <td className="error">{f.motivo}</td>
                    </tr>
                  ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {error && <p className="error">{error}</p>}
      {corredores === null && !error && <p>Cargando…</p>}
      {corredores && corredores.length === 0 && (
        <p className="texto-vacio">Todavía no hay corredores inscritos en esta distancia.</p>
      )}
      {corredores && corredores.length > 0 && (
        <>
          {rolAdmin && seleccionados.size > 0 && (
            <div className="barra-seleccion">
              <span>{seleccionados.size} seleccionado(s)</span>
              <button type="button" className="boton-peligro" onClick={() => setConfirmando("bloque")}>
                Borrar seleccionados
              </button>
            </div>
          )}
          <table>
            <thead>
              <tr>
                {rolAdmin && (
                  <th>
                    <input
                      type="checkbox"
                      checked={seleccionados.size === corredores.length}
                      onChange={alternarSeleccionTodos}
                      aria-label="Seleccionar todos"
                    />
                  </th>
                )}
                <th>Dorsal</th>
                <th>Nombre</th>
                <th>Club</th>
                <th>Estado</th>
                {rolAdmin && <th></th>}
              </tr>
            </thead>
            <tbody>
              {corredores.map((c) =>
                editandoId === c.inscripcion_id ? (
                  <FilaEdicion
                    key={c.inscripcion_id}
                    corredor={c}
                    onCancelar={() => setEditandoId(null)}
                    onGuardar={(datos) => alGuardarEdicion(c.inscripcion_id, datos)}
                  />
                ) : (
                  <tr key={c.inscripcion_id}>
                    {rolAdmin && (
                      <td>
                        <input
                          type="checkbox"
                          checked={seleccionados.has(c.inscripcion_id)}
                          onChange={() => alternarSeleccion(c.inscripcion_id)}
                        />
                      </td>
                    )}
                    <td>{c.dorsal}</td>
                    <td>
                      {c.nombre} {c.apellidos}
                    </td>
                    <td>{c.club ?? "—"}</td>
                    <td>
                      <span
                        className="insignia-estado"
                        style={{
                          backgroundColor: resolverColorEstado(
                            c.estado as "transmitiendo" | "sin_senal",
                          ),
                        }}
                      >
                        {c.estado === "transmitiendo" ? "Transmitiendo" : "Sin señal"}
                      </span>
                    </td>
                    {rolAdmin && (
                      <td className="tabla__acciones-fila">
                        <button
                          type="button"
                          className="boton-enlace"
                          onClick={() => setEditandoId(c.inscripcion_id)}
                        >
                          Editar
                        </button>
                        <button
                          type="button"
                          className="boton-enlace boton-enlace--peligro"
                          disabled={borrandoId === c.inscripcion_id}
                          onClick={() => {
                            setObjetivoBorrado(c.inscripcion_id);
                            setConfirmando("uno");
                          }}
                        >
                          Borrar
                        </button>
                      </td>
                    )}
                  </tr>
                ),
              )}
            </tbody>
          </table>
        </>
      )}

      {confirmando && (
        <div className="modal-fondo" role="presentation" onClick={() => setConfirmando(null)}>
          <div className="modal" role="dialog" aria-modal="true" onClick={(e) => e.stopPropagation()}>
            <h3>
              {confirmando === "bloque"
                ? `Borrar ${seleccionados.size} corredor(es)`
                : "Borrar corredor"}
            </h3>
            <p>Esta acción no se puede deshacer: se pierde su historial de posiciones.</p>
            <div className="modal__acciones">
              <button type="button" onClick={() => setConfirmando(null)}>
                Cancelar
              </button>
              <button
                type="button"
                className="boton-peligro"
                disabled={borrandoBloque}
                onClick={() =>
                  confirmando === "bloque"
                    ? alBorrarSeleccionados()
                    : objetivoBorrado !== null && alBorrarUno(objetivoBorrado)
                }
              >
                {borrandoBloque ? "Borrando…" : "Sí, borrar"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function FilaEdicion({
  corredor,
  onCancelar,
  onGuardar,
}: {
  corredor: PosicionPublica;
  onCancelar: () => void;
  onGuardar: (datos: {
    dorsal: string;
    nombre: string;
    apellidos: string;
    club: string;
  }) => Promise<string | null | undefined>;
}) {
  const [dorsal, setDorsal] = useState(corredor.dorsal);
  const [nombre, setNombre] = useState(corredor.nombre);
  const [apellidos, setApellidos] = useState(corredor.apellidos);
  const [club, setClub] = useState(corredor.club ?? "");
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function alGuardar() {
    setGuardando(true);
    setError(null);
    const mensaje = await onGuardar({ dorsal, nombre, apellidos, club });
    setGuardando(false);
    if (mensaje) setError(mensaje);
  }

  return (
    <tr>
      <td></td>
      <td>
        <input value={dorsal} onChange={(e) => setDorsal(e.target.value)} className="input-compacto" />
      </td>
      <td className="fila-edicion__nombre">
        <input value={nombre} onChange={(e) => setNombre(e.target.value)} className="input-compacto" />
        <input
          value={apellidos}
          onChange={(e) => setApellidos(e.target.value)}
          className="input-compacto"
        />
      </td>
      <td>
        <input value={club} onChange={(e) => setClub(e.target.value)} className="input-compacto" />
      </td>
      <td colSpan={2}>
        <div className="tabla__acciones-fila">
          <button type="button" onClick={alGuardar} disabled={guardando}>
            {guardando ? "Guardando…" : "Guardar"}
          </button>
          <button type="button" onClick={onCancelar} disabled={guardando}>
            Cancelar
          </button>
        </div>
        {error && <p className="error">{error}</p>}
      </td>
    </tr>
  );
}
