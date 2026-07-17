import { useEffect, useRef, useState, type FormEvent } from "react";
import type { components } from "@empatelive/web-shared";
import { api, mensajeError } from "../../api";

type Distancia = components["schemas"]["DistanciaSalida"];

interface Props {
  eventoId: number;
  rolAdmin: boolean;
}

export function Distancias({ eventoId, rolAdmin }: Props) {
  const [distancias, setDistancias] = useState<Distancia[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [nombreNueva, setNombreNueva] = useState("");
  const [creando, setCreando] = useState(false);
  const [subiendoId, setSubiendoId] = useState<number | null>(null);
  const [avisoPorDistancia, setAvisoPorDistancia] = useState<Record<number, string>>({});
  const [editandoId, setEditandoId] = useState<number | null>(null);
  const [nombreEdicion, setNombreEdicion] = useState("");
  const [guardandoId, setGuardandoId] = useState<number | null>(null);
  const [borrandoId, setBorrandoId] = useState<number | null>(null);
  const [confirmandoBorradoId, setConfirmandoBorradoId] = useState<number | null>(null);
  const inputsGpx = useRef<Record<number, HTMLInputElement | null>>({});

  useEffect(() => {
    cargar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [eventoId]);

  async function cargar() {
    setError(null);
    const { data, error } = await api.GET("/eventos/{evento_id}/distancias", {
      params: { path: { evento_id: eventoId } },
    });
    if (error) {
      setError("No se pudieron cargar las distancias.");
      return;
    }
    setDistancias(data);
  }

  async function alCrear(e: FormEvent) {
    e.preventDefault();
    setCreando(true);
    setError(null);
    const { error } = await api.POST("/eventos/{evento_id}/distancias", {
      params: { path: { evento_id: eventoId } },
      body: { nombre: nombreNueva },
    });
    setCreando(false);
    if (error) {
      setError(mensajeError(error, "No se pudo crear la distancia."));
      return;
    }
    setNombreNueva("");
    await cargar();
  }

  async function alSubirGpx(distanciaId: number, archivo: File) {
    setSubiendoId(distanciaId);
    setAvisoPorDistancia((prev) => ({ ...prev, [distanciaId]: "" }));
    const formData = new FormData();
    formData.append("archivo", archivo);
    const { error } = await api.POST("/distancias/{distancia_id}/gpx", {
      params: { path: { distancia_id: distanciaId } },
      // openapi-fetch pasa FormData directamente al fetch sin serializarlo a
      // JSON (detecta la instancia y deja que el navegador ponga el boundary).
      body: formData as unknown as { archivo: string },
    });
    setSubiendoId(null);
    const input = inputsGpx.current[distanciaId];
    if (input) input.value = "";
    if (error) {
      setAvisoPorDistancia((prev) => ({
        ...prev,
        [distanciaId]: mensajeError(error, "No se pudo subir el GPX."),
      }));
      return;
    }
    setAvisoPorDistancia((prev) => ({ ...prev, [distanciaId]: "GPX cargado correctamente." }));
    await cargar();
  }

  function alEmpezarEdicion(d: Distancia) {
    setEditandoId(d.id);
    setNombreEdicion(d.nombre);
  }

  async function alGuardarNombre(distanciaId: number) {
    setGuardandoId(distanciaId);
    const { error } = await api.PUT("/distancias/{distancia_id}", {
      params: { path: { distancia_id: distanciaId } },
      body: { nombre: nombreEdicion },
    });
    setGuardandoId(null);
    if (error) {
      setAvisoPorDistancia((prev) => ({
        ...prev,
        [distanciaId]: mensajeError(error, "No se pudo renombrar la distancia."),
      }));
      return;
    }
    setEditandoId(null);
    await cargar();
  }

  async function alBorrar(distanciaId: number) {
    setBorrandoId(distanciaId);
    const { error } = await api.DELETE("/distancias/{distancia_id}", {
      params: { path: { distancia_id: distanciaId } },
    });
    setBorrandoId(null);
    setConfirmandoBorradoId(null);
    if (error) {
      setAvisoPorDistancia((prev) => ({
        ...prev,
        [distanciaId]: mensajeError(error, "No se pudo borrar la distancia."),
      }));
      return;
    }
    await cargar();
  }

  return (
    <div className="bloque-pestana">
      {rolAdmin && (
        <form className="formulario-tarjeta formulario-tarjeta--fila" onSubmit={alCrear}>
          <label>
            Nueva distancia
            <input
              value={nombreNueva}
              onChange={(e) => setNombreNueva(e.target.value)}
              placeholder="p. ej. 10K"
              required
            />
          </label>
          <button type="submit" disabled={creando}>
            {creando ? "Creando…" : "Añadir distancia"}
          </button>
        </form>
      )}

      {error && <p className="error">{error}</p>}
      {distancias === null && !error && <p>Cargando…</p>}
      {distancias && distancias.length === 0 && (
        <p className="texto-vacio">Este evento todavía no tiene distancias.</p>
      )}

      {distancias && distancias.length > 0 && (
        <ul className="lista-tarjetas">
          {distancias.map((d) => (
            <li key={d.id} className="tarjeta">
              <div className="tarjeta__cabecera">
                {editandoId === d.id ? (
                  <div className="tarjeta__edicion-nombre">
                    <input
                      value={nombreEdicion}
                      onChange={(e) => setNombreEdicion(e.target.value)}
                      autoFocus
                    />
                    <button
                      type="button"
                      onClick={() => alGuardarNombre(d.id)}
                      disabled={guardandoId === d.id}
                    >
                      Guardar
                    </button>
                    <button type="button" onClick={() => setEditandoId(null)}>
                      Cancelar
                    </button>
                  </div>
                ) : (
                  <strong>{d.nombre}</strong>
                )}
                <span className={`insignia ${d.gpx_url ? "insignia--ok" : "insignia--pendiente"}`}>
                  {d.gpx_url ? "GPX cargado" : "Sin GPX"}
                </span>
              </div>
              {rolAdmin && (
                <div className="tarjeta__acciones">
                  <input
                    ref={(el) => {
                      inputsGpx.current[d.id] = el;
                    }}
                    type="file"
                    accept=".gpx"
                    disabled={subiendoId === d.id}
                    onChange={(e) => {
                      const archivo = e.target.files?.[0];
                      if (archivo) alSubirGpx(d.id, archivo);
                    }}
                  />
                  {subiendoId === d.id && <span>Subiendo…</span>}
                  {editandoId !== d.id && (
                    <button type="button" className="boton-enlace" onClick={() => alEmpezarEdicion(d)}>
                      Renombrar
                    </button>
                  )}
                  <button
                    type="button"
                    className="boton-enlace boton-enlace--peligro"
                    onClick={() => setConfirmandoBorradoId(d.id)}
                    disabled={borrandoId === d.id}
                  >
                    {borrandoId === d.id ? "Borrando…" : "Borrar"}
                  </button>
                </div>
              )}
              {avisoPorDistancia[d.id] && (
                <p
                  className={
                    avisoPorDistancia[d.id].includes("correctamente") ? "aviso-ok" : "error"
                  }
                >
                  {avisoPorDistancia[d.id]}
                </p>
              )}

              {confirmandoBorradoId === d.id && (
                <div className="modal-fondo" role="presentation" onClick={() => setConfirmandoBorradoId(null)}>
                  <div className="modal" role="dialog" aria-modal="true" onClick={(e) => e.stopPropagation()}>
                    <h3>Borrar «{d.nombre}»</h3>
                    <p>
                      Esta acción no se puede deshacer: si tiene corredores inscritos, se
                      borran junto con la distancia (dorsal, posiciones e historial). Las
                      cuentas de los corredores no se ven afectadas, solo su inscripción
                      en esta distancia.
                    </p>
                    <div className="modal__acciones">
                      <button type="button" onClick={() => setConfirmandoBorradoId(null)}>
                        Cancelar
                      </button>
                      <button type="button" className="boton-peligro" onClick={() => alBorrar(d.id)}>
                        Sí, borrar
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
