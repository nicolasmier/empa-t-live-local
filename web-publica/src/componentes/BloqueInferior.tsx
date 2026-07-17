import { useEffect, useState } from "react";
import {
  normalizarUrlExterna,
  resolverColorEstado,
  type components,
  type EstadoTransmision,
} from "@empatelive/web-shared";
import { api, urlMedia } from "../api";
import type { EstadoMarcador } from "../mapa/interpolacion";
import "./BloqueInferior.css";

type Patrocinador = components["schemas"]["PatrocinadorSalida"];
type Noticia = components["schemas"]["NoticiaSalida"];

interface Props {
  eventoId: number;
  cartelUrl: string | null;
  estado: ReadonlyMap<number, EstadoMarcador>;
}

export function BloqueInferior({ eventoId, cartelUrl, estado }: Props) {
  const [patrocinadores, setPatrocinadores] = useState<Patrocinador[]>([]);
  const [noticias, setNoticias] = useState<Noticia[]>([]);

  useEffect(() => {
    api
      .GET("/eventos/{evento_id}/patrocinadores", { params: { path: { evento_id: eventoId } } })
      .then(({ data }) => setPatrocinadores(data ?? []));
    api
      .GET("/eventos/{evento_id}/noticias", { params: { path: { evento_id: eventoId } } })
      .then(({ data }) => setNoticias(data ?? []));
  }, [eventoId]);

  const corredores = Array.from(estado.values()).sort((a, b) =>
    a.datos.dorsal.localeCompare(b.datos.dorsal, undefined, { numeric: true }),
  );

  const hayLateral = patrocinadores.length > 0 || noticias.length > 0;

  return (
    <section className="bloque-inferior">
      {(cartelUrl || hayLateral) && (
        <div className="bloque-inferior__superior">
          {cartelUrl && (
            <div className="bloque-inferior__cartel">
              <img src={urlMedia(cartelUrl)} alt="Cartel de la carrera" />
            </div>
          )}

          {hayLateral && (
            <div className="bloque-inferior__lateral">
              {patrocinadores.length > 0 && (
                <div className="bloque-inferior__seccion">
                  <h3>Patrocinadores</h3>
                  <div className="patrocinadores">
                    {patrocinadores.map((p) => (
                      <a
                        key={p.id}
                        href={p.enlace_url ? normalizarUrlExterna(p.enlace_url) : undefined}
                        target="_blank"
                        rel="noreferrer"
                        className="patrocinadores__item"
                      >
                        {p.logo_url ? <img src={urlMedia(p.logo_url)} alt={p.nombre} /> : p.nombre}
                      </a>
                    ))}
                  </div>
                </div>
              )}

              {noticias.length > 0 && (
                <div className="bloque-inferior__seccion">
                  <h3>Noticias</h3>
                  <ul className="noticias">
                    {noticias.map((n) => (
                      <li key={n.id}>
                        <strong>{n.titulo}</strong>
                        <p>{n.contenido}</p>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      <div className="bloque-inferior__seccion">
        <h3>Corredores ({corredores.length})</h3>
        <table className="listado">
          <thead>
            <tr>
              <th>Dorsal</th>
              <th>Nombre</th>
              <th>Club</th>
              <th>Estado</th>
            </tr>
          </thead>
          <tbody>
            {corredores.map(({ datos }) => (
              <tr key={datos.inscripcion_id}>
                <td className="listado__dorsal">{datos.dorsal}</td>
                <td>
                  {datos.nombre} {datos.apellidos}
                </td>
                <td>{datos.club ?? "—"}</td>
                <td>
                  <span
                    className="listado__estado"
                    style={{
                      color: resolverColorEstado(datos.estado as EstadoTransmision),
                    }}
                  >
                    ● {datos.estado === "transmitiendo" ? "Transmitiendo" : "Sin señal"}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
