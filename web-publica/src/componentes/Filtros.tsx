import { IconoBusqueda, IconoEstrella } from "./iconos";
import "./Filtros.css";

export type ModoFiltro = "todos" | "favoritos" | "dorsal";

interface Props {
  modo: ModoFiltro;
  textoDorsal: string;
  onCambiarModo: (modo: ModoFiltro) => void;
  onCambiarTextoDorsal: (texto: string) => void;
}

export function Filtros({ modo, textoDorsal, onCambiarModo, onCambiarTextoDorsal }: Props) {
  return (
    <div className="filtros">
      <label className="filtros__busqueda">
        <IconoBusqueda />
        <input
          type="search"
          placeholder="Buscar dorsal"
          value={textoDorsal}
          onChange={(evento) => {
            onCambiarTextoDorsal(evento.target.value);
            onCambiarModo(evento.target.value ? "dorsal" : "todos");
          }}
        />
      </label>

      <button
        type="button"
        className={`filtros__chip ${modo === "todos" ? "filtros__chip--activo" : ""}`}
        onClick={() => {
          onCambiarModo("todos");
          onCambiarTextoDorsal("");
        }}
      >
        Todos
      </button>

      <button
        type="button"
        className={`filtros__chip ${modo === "favoritos" ? "filtros__chip--activo" : ""}`}
        onClick={() => onCambiarModo("favoritos")}
      >
        <IconoEstrella relleno={modo === "favoritos"} />
        Favoritos
      </button>
    </div>
  );
}
