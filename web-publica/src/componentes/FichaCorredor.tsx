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
// ficha no tape el mapa (Anexo C). Se adapta a los datos disponibles del
// corredor: la foto solo aparece si la hay (el dorsal ya se muestra en grande,
// así que un círculo placeholder con el número sería redundante) y el nombre y
// el club solo si vienen rellenos.
export function FichaCorredor({ posicion, esFavorito, onCerrar, onAlternarFavorito }: Props) {
  const nombreCompleto = [posicion.nombre, posicion.apellidos].filter(Boolean).join(" ").trim();

  return (
    <div className="ficha">
      <button type="button" className="ficha__cerrar" onClick={onCerrar} aria-label="Cerrar">
        <IconoCerrar />
      </button>

      {posicion.foto_url && (
        <div className="ficha__foto">
          <img src={urlMedia(posicion.foto_url)} alt="" />
        </div>
      )}

      <div className="ficha__datos">
        <p className="ficha__dorsal">{posicion.dorsal}</p>
        {nombreCompleto && <h2 className="ficha__nombre">{nombreCompleto}</h2>}
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
