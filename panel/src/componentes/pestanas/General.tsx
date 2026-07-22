import { useState, type FormEvent } from "react";
import type { components } from "@empatelive/web-shared";
import { api, mensajeError } from "../../api";
import type { EstadoEvento } from "../../dominio/estadosEvento";
import { EstadoControl } from "./EstadoControl";
import { SalidaProgramada } from "./SalidaProgramada";

type Evento = components["schemas"]["EventoSalida"];

interface Props {
  evento: Evento;
  rolAdmin: boolean;
  onActualizado: () => void;
}

export function General({ evento, rolAdmin, onActualizado }: Props) {
  const [nombre, setNombre] = useState(evento.nombre);
  const [codigoAcceso, setCodigoAcceso] = useState(evento.codigo_acceso);
  const [fecha, setFecha] = useState(evento.fecha);
  const [guardando, setGuardando] = useState(false);
  const [duplicando, setDuplicando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [aviso, setAviso] = useState<string | null>(null);

  async function alGuardar(e: FormEvent) {
    e.preventDefault();
    setGuardando(true);
    setError(null);
    setAviso(null);
    const { error } = await api.PUT("/eventos/{evento_id}", {
      params: { path: { evento_id: evento.id } },
      body: { nombre, codigo_acceso: codigoAcceso, fecha },
    });
    setGuardando(false);
    if (error) {
      setError(mensajeError(error, "No se pudieron guardar los cambios."));
      return;
    }
    setAviso("Guardado.");
    onActualizado();
  }

  async function alDuplicar() {
    setDuplicando(true);
    setError(null);
    const { data, error } = await api.POST("/eventos/{evento_id}/duplicar", {
      params: { path: { evento_id: evento.id } },
    });
    setDuplicando(false);
    if (error) {
      setError(mensajeError(error, "No se pudo duplicar el evento."));
      return;
    }
    if (data) setAviso(`Creada la copia «${data.nombre}» en Borrador (código ${data.codigo_acceso}).`);
  }

  return (
    <div className="bloque-pestana">
      <form className="formulario-tarjeta" onSubmit={alGuardar}>
        <label>
          Nombre
          <input
            value={nombre}
            onChange={(e) => setNombre(e.target.value)}
            disabled={!rolAdmin}
            required
          />
        </label>
        <label>
          Código de acceso
          <input
            value={codigoAcceso}
            onChange={(e) => setCodigoAcceso(e.target.value.toUpperCase())}
            disabled={!rolAdmin}
            required
          />
        </label>
        {rolAdmin && codigoAcceso !== evento.codigo_acceso && (
          <p className="aviso-atencion">
            Al cambiarlo, los corredores que aún no se hayan unido necesitarán el código
            nuevo — avísales si ya se ha compartido el anterior.
          </p>
        )}
        <label>
          Fecha
          <input
            type="date"
            value={fecha}
            onChange={(e) => setFecha(e.target.value)}
            disabled={!rolAdmin}
            required
          />
        </label>
        {rolAdmin && (
          <div className="formulario-tarjeta__acciones">
            <button type="submit" disabled={guardando}>
              {guardando ? "Guardando…" : "Guardar cambios"}
            </button>
            <button type="button" onClick={alDuplicar} disabled={duplicando}>
              {duplicando ? "Duplicando…" : "Duplicar evento"}
            </button>
          </div>
        )}
        {error && <p className="error">{error}</p>}
        {aviso && <p className="aviso-ok">{aviso}</p>}
      </form>

      {rolAdmin ? (
        <>
          <EstadoControl
            eventoId={evento.id}
            estadoActual={evento.estado as EstadoEvento}
            onCambiado={onActualizado}
          />
          {(evento.estado === "preparacion" || evento.estado === "en_directo") && (
            <SalidaProgramada
              eventoId={evento.id}
              estado={evento.estado}
              horaProgramada={evento.hora_programada_directo}
              onCambiado={onActualizado}
            />
          )}
        </>
      ) : (
        <p className="texto-vacio">Solo un Administrador puede cambiar el estado del evento.</p>
      )}
    </div>
  );
}
