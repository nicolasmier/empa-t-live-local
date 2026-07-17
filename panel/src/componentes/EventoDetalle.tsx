import { useCallback, useEffect, useState } from "react";
import type { components } from "@empatelive/web-shared";
import { api } from "../api";
import { General } from "./pestanas/General";
import { Distancias } from "./pestanas/Distancias";
import { Corredores } from "./pestanas/Corredores";
import { Contenido } from "./pestanas/Contenido";
import { Configuracion } from "./pestanas/Configuracion";
import { Incidencias } from "./pestanas/Incidencias";

type Evento = components["schemas"]["EventoSalida"];

const PESTANAS = [
  { clave: "general", etiqueta: "General" },
  { clave: "distancias", etiqueta: "Distancias" },
  { clave: "corredores", etiqueta: "Corredores" },
  { clave: "contenido", etiqueta: "Contenido" },
  { clave: "configuracion", etiqueta: "Configuración" },
  { clave: "incidencias", etiqueta: "Incidencias" },
] as const;

type Pestana = (typeof PESTANAS)[number]["clave"];

interface Props {
  eventoId: number;
  rolAdmin: boolean;
  onVolver: () => void;
}

export function EventoDetalle({ eventoId, rolAdmin, onVolver }: Props) {
  const [evento, setEvento] = useState<Evento | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pestana, setPestana] = useState<Pestana>("general");

  const cargarEvento = useCallback(async () => {
    const { data, error } = await api.GET("/eventos/{evento_id}", {
      params: { path: { evento_id: eventoId } },
    });
    if (error) {
      setError("No se pudo cargar el evento.");
      return;
    }
    setEvento(data);
  }, [eventoId]);

  useEffect(() => {
    setEvento(null);
    setError(null);
    cargarEvento();
  }, [cargarEvento]);

  if (error) {
    return (
      <section className="panel-seccion">
        <p className="error">{error}</p>
        <button type="button" onClick={onVolver}>
          Volver al listado
        </button>
      </section>
    );
  }

  if (!evento) return <p>Cargando…</p>;

  return (
    <section className="panel-seccion">
      <div className="panel-seccion__cabecera">
        <button type="button" className="boton-enlace" onClick={onVolver}>
          ← Eventos
        </button>
        <h2>{evento.nombre}</h2>
      </div>

      <nav className="pestanas-panel">
        {PESTANAS.map((p) => (
          <button
            key={p.clave}
            type="button"
            className={`pestanas-panel__item ${pestana === p.clave ? "pestanas-panel__item--activo" : ""}`}
            onClick={() => setPestana(p.clave)}
          >
            {p.etiqueta}
          </button>
        ))}
      </nav>

      <div className="pestanas-panel__contenido">
        {pestana === "general" && (
          <General evento={evento} rolAdmin={rolAdmin} onActualizado={cargarEvento} />
        )}
        {pestana === "distancias" && <Distancias eventoId={eventoId} rolAdmin={rolAdmin} />}
        {pestana === "corredores" && <Corredores eventoId={eventoId} rolAdmin={rolAdmin} />}
        {pestana === "contenido" && (
          <Contenido evento={evento} rolAdmin={rolAdmin} onActualizado={cargarEvento} />
        )}
        {pestana === "configuracion" && (
          <Configuracion evento={evento} rolAdmin={rolAdmin} onActualizado={cargarEvento} />
        )}
        {pestana === "incidencias" && <Incidencias eventoId={eventoId} />}
      </div>
    </section>
  );
}
