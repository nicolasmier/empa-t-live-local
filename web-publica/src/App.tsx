import { useEffect, useMemo, useState } from "react";
import type { components } from "@empatelive/web-shared";
import { api } from "./api";
import { BloqueInferior } from "./componentes/BloqueInferior";
import { Cabecera } from "./componentes/Cabecera";
import { Filtros, type ModoFiltro } from "./componentes/Filtros";
import { FichaCorredor } from "./componentes/FichaCorredor";
import { Mapa, type BBox } from "./mapa/Mapa";
import type { PosicionPublica } from "./mapa/interpolacion";
import { usePosicionesPolling } from "./mapa/usePosicionesPolling";

type Evento = components["schemas"]["EventoSalida"];
type Distancia = components["schemas"]["DistanciaSalida"];

function claveFavoritos(eventoId: number): string {
  return `empatelive_favoritos_${eventoId}`;
}

function cargarFavoritos(eventoId: number): Set<number> {
  try {
    const bruto = localStorage.getItem(claveFavoritos(eventoId));
    return new Set(bruto ? (JSON.parse(bruto) as number[]) : []);
  } catch {
    return new Set();
  }
}

function App() {
  const [evento, setEvento] = useState<Evento | null>(null);
  const [errorEvento, setErrorEvento] = useState<string | null>(null);
  const [distancias, setDistancias] = useState<Distancia[]>([]);
  const [distanciaId, setDistanciaId] = useState<number | null>(null);

  const [modoFiltro, setModoFiltro] = useState<ModoFiltro>("todos");
  const [textoDorsal, setTextoDorsal] = useState("");
  const [favoritos, setFavoritos] = useState<Set<number>>(new Set());
  const [seleccionado, setSeleccionado] = useState<PosicionPublica | null>(null);

  useEffect(() => {
    async function cargarEvento() {
      const { data, error } = await api.GET("/eventos/activo");
      if (error) {
        setErrorEvento("No hay ningún evento publicado en este momento.");
        return;
      }
      setEvento(data);
      setFavoritos(cargarFavoritos(data.id));

      const distanciasResp = await api.GET("/eventos/{evento_id}/distancias", {
        params: { path: { evento_id: data.id } },
      });
      if (distanciasResp.data && distanciasResp.data.length > 0) {
        setDistancias(distanciasResp.data);
        setDistanciaId(distanciasResp.data[0].id);
      }
    }
    cargarEvento();
  }, []);

  const distanciaActual = distancias.find((d) => d.id === distanciaId) ?? null;
  const bbox = (distanciaActual?.mapa_config as { bbox?: BBox } | null)?.bbox ?? null;

  const { estado, conectado } = usePosicionesPolling(evento?.id ?? null, distanciaId);

  const mostrarCorredor = useMemo(() => {
    const dorsalBuscado = textoDorsal.trim();
    return (posicion: PosicionPublica) => {
      if (modoFiltro === "favoritos") return favoritos.has(posicion.inscripcion_id);
      if (modoFiltro === "dorsal" && dorsalBuscado) return posicion.dorsal.includes(dorsalBuscado);
      return true;
    };
  }, [modoFiltro, textoDorsal, favoritos]);

  function alternarFavorito(inscripcionId: number) {
    if (!evento) return;
    setFavoritos((anterior) => {
      const siguiente = new Set(anterior);
      if (siguiente.has(inscripcionId)) siguiente.delete(inscripcionId);
      else siguiente.add(inscripcionId);
      localStorage.setItem(claveFavoritos(evento.id), JSON.stringify([...siguiente]));
      return siguiente;
    });
  }

  if (errorEvento) {
    return (
      <div className="estado-vacio">
        <p>{errorEvento}</p>
      </div>
    );
  }

  if (!evento || distanciaId === null) {
    return (
      <div className="estado-vacio">
        <p>Cargando…</p>
      </div>
    );
  }

  return (
    <>
      <Cabecera
        eventoId={evento.id}
        nombreEvento={evento.nombre}
        enDirecto={evento.estado === "en_directo"}
        conectado={conectado}
      />

      <Filtros
        modo={modoFiltro}
        textoDorsal={textoDorsal}
        onCambiarModo={setModoFiltro}
        onCambiarTextoDorsal={setTextoDorsal}
      />

      {distancias.length > 1 && (
        <nav className="pestanas">
          {distancias.map((d) => (
            <button
              key={d.id}
              type="button"
              className={`pestanas__item ${d.id === distanciaId ? "pestanas__item--activo" : ""}`}
              onClick={() => setDistanciaId(d.id)}
            >
              {d.nombre}
            </button>
          ))}
        </nav>
      )}

      <Mapa
        key={distanciaId}
        estado={estado}
        gpxUrl={distanciaActual?.gpx_url ?? null}
        bbox={bbox}
        mostrarCorredor={mostrarCorredor}
        onSeleccionarCorredor={setSeleccionado}
      />

      {seleccionado && (
        <FichaCorredor
          posicion={seleccionado}
          esFavorito={favoritos.has(seleccionado.inscripcion_id)}
          onCerrar={() => setSeleccionado(null)}
          onAlternarFavorito={() => alternarFavorito(seleccionado.inscripcion_id)}
        />
      )}

      <BloqueInferior eventoId={evento.id} cartelUrl={evento.cartel_url} estado={estado} />
    </>
  );
}

export default App;
