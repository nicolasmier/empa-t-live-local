import { useEffect, useState, type FormEvent } from "react";
import type { components } from "@empatelive/web-shared";
import { api, mensajeError } from "../api";
import { ETIQUETAS_ESTADO } from "../dominio/estadosEvento";

type Evento = components["schemas"]["EventoSalida"];

interface Props {
  rolAdmin: boolean;
  onAbrirEvento: (id: number) => void;
}

export function EventosListado({ rolAdmin, onAbrirEvento }: Props) {
  const [eventos, setEventos] = useState<Evento[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [mostrarForm, setMostrarForm] = useState(false);
  const [nombre, setNombre] = useState("");
  const [codigoAcceso, setCodigoAcceso] = useState("");
  const [fecha, setFecha] = useState("");
  const [errorForm, setErrorForm] = useState<string | null>(null);
  const [creando, setCreando] = useState(false);

  useEffect(() => {
    cargar();
  }, []);

  async function cargar() {
    setError(null);
    const { data, error } = await api.GET("/eventos");
    if (error) {
      setError("No se pudieron cargar los eventos.");
      return;
    }
    setEventos(data);
  }

  async function alCrear(e: FormEvent) {
    e.preventDefault();
    setCreando(true);
    setErrorForm(null);
    const { data, error } = await api.POST("/eventos", {
      body: { nombre, codigo_acceso: codigoAcceso, fecha },
    });
    setCreando(false);
    if (error) {
      setErrorForm(mensajeError(error, "No se pudo crear el evento."));
      return;
    }
    setMostrarForm(false);
    setNombre("");
    setCodigoAcceso("");
    setFecha("");
    await cargar();
    if (data) onAbrirEvento(data.id);
  }

  return (
    <section className="panel-seccion">
      <div className="panel-seccion__cabecera">
        <h2>Eventos</h2>
        {rolAdmin && (
          <button type="button" onClick={() => setMostrarForm((v) => !v)}>
            {mostrarForm ? "Cancelar" : "Crear evento"}
          </button>
        )}
      </div>

      {mostrarForm && (
        <form className="formulario-tarjeta" onSubmit={alCrear}>
          <label>
            Nombre
            <input value={nombre} onChange={(e) => setNombre(e.target.value)} required />
          </label>
          <label>
            Código de acceso
            <input
              value={codigoAcceso}
              onChange={(e) => setCodigoAcceso(e.target.value.toUpperCase())}
              placeholder="p. ej. MADRID2026"
              required
            />
          </label>
          <label>
            Fecha
            <input type="date" value={fecha} onChange={(e) => setFecha(e.target.value)} required />
          </label>
          {errorForm && <p className="error">{errorForm}</p>}
          <button type="submit" disabled={creando}>
            {creando ? "Creando…" : "Crear en Borrador"}
          </button>
        </form>
      )}

      {error && <p className="error">{error}</p>}
      {eventos === null && !error && <p>Cargando…</p>}
      {eventos && eventos.length === 0 && <p className="texto-vacio">No hay eventos todavía.</p>}
      {eventos && eventos.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>Nombre</th>
              <th>Código</th>
              <th>Fecha</th>
              <th>Estado</th>
            </tr>
          </thead>
          <tbody>
            {eventos.map((evento) => (
              <tr key={evento.id} className="fila-clicable" onClick={() => onAbrirEvento(evento.id)}>
                <td>{evento.nombre}</td>
                <td>{evento.codigo_acceso}</td>
                <td>{evento.fecha}</td>
                <td>
                  <span className={`insignia insignia--${evento.estado}`}>
                    {ETIQUETAS_ESTADO[evento.estado as keyof typeof ETIQUETAS_ESTADO] ?? evento.estado}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
