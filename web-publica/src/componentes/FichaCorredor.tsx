import { urlMedia } from "../api";
import type { PosicionPublica } from "../mapa/interpolacion";
import { IconoCerrar, IconoEstrella } from "./iconos";
import "./FichaCorredor.css";

interface Props {
  posicion: PosicionPublica;
  esFavorito: boolean;
  onCerrar: () => void;
  onAlternarFavorito: () => void;
}

// Tarjeta flotante, no un overlay a pantalla completa: la spec pide que la
// ficha no tape el mapa (Anexo C).
export function FichaCorredor({ posicion, esFavorito, onCerrar, onAlternarFavorito }: Props) {
  return (
    <div className="ficha">
      <button type="button" className="ficha__cerrar" onClick={onCerrar} aria-label="Cerrar">
        <IconoCerrar />
      </button>

      <div className="ficha__foto">
        {posicion.foto_url ? (
          <img src={urlMedia(posicion.foto_url)} alt="" />
        ) : (
          <span>{posicion.dorsal}</span>
        )}
      </div>

      <div className="ficha__datos">
        <p className="ficha__dorsal">{posicion.dorsal}</p>
        <h2 className="ficha__nombre">
          {posicion.nombre} {posicion.apellidos}
        </h2>
        {posicion.club && <p className="ficha__club">{posicion.club}</p>}
      </div>

      <button
        type="button"
        className={`ficha__favorito ${esFavorito ? "ficha__favorito--activo" : ""}`}
        onClick={onAlternarFavorito}
      >
        <IconoEstrella relleno={esFavorito} />
        {esFavorito ? "En favoritos" : "Añadir a favoritos"}
      </button>
    </div>
  );
}
