import { useState, type FormEvent } from "react";
import {
  COLOR_SIN_SENAL,
  COLOR_TRANSMITIENDO,
  type ColoresConfig,
  type components,
} from "@empatelive/web-shared";
import { api, mensajeError } from "../../api";

type Evento = components["schemas"]["EventoSalida"];

interface InfoVisibleConfig {
  mostrar_club?: boolean;
  mostrar_patrocinadores?: boolean;
  mostrar_noticias?: boolean;
}

interface Props {
  evento: Evento;
  rolAdmin: boolean;
  onActualizado: () => void;
}

export function Configuracion({ evento, rolAdmin, onActualizado }: Props) {
  const [parado, setParado] = useState(evento.intervalo_gps_parado_seg);
  const [movimiento, setMovimiento] = useState(evento.intervalo_gps_movimiento_seg);
  const [umbral, setUmbral] = useState(evento.umbral_sin_senal_seg);

  const colores = (evento.colores_config as ColoresConfig | null) ?? {};
  const [colorTransmitiendo, setColorTransmitiendo] = useState(colores.transmitiendo ?? COLOR_TRANSMITIENDO);
  const [colorSinSenal, setColorSinSenal] = useState(colores.sin_senal ?? COLOR_SIN_SENAL);

  const infoVisible = (evento.info_visible_config as InfoVisibleConfig | null) ?? {};
  const [mostrarClub, setMostrarClub] = useState(infoVisible.mostrar_club ?? true);
  const [mostrarPatrocinadores, setMostrarPatrocinadores] = useState(
    infoVisible.mostrar_patrocinadores ?? true,
  );
  const [mostrarNoticias, setMostrarNoticias] = useState(infoVisible.mostrar_noticias ?? true);

  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [aviso, setAviso] = useState<string | null>(null);

  async function alGuardar(e: FormEvent) {
    e.preventDefault();
    setGuardando(true);
    setError(null);
    setAviso(null);
    const { error } = await api.PUT("/eventos/{evento_id}", {
      params: { path: { evento_id: evento.id } },
      body: {
        intervalo_gps_parado_seg: parado,
        intervalo_gps_movimiento_seg: movimiento,
        umbral_sin_senal_seg: umbral,
        colores_config: { transmitiendo: colorTransmitiendo, sin_senal: colorSinSenal },
        info_visible_config: {
          mostrar_club: mostrarClub,
          mostrar_patrocinadores: mostrarPatrocinadores,
          mostrar_noticias: mostrarNoticias,
        },
      },
    });
    setGuardando(false);
    if (error) {
      setError(mensajeError(error, "No se pudieron guardar los cambios."));
      return;
    }
    setAviso("Configuración guardada.");
    onActualizado();
  }

  return (
    <form className="formulario-tarjeta" onSubmit={alGuardar}>
      <fieldset disabled={!rolAdmin}>
        <legend>Intervalos GPS</legend>
        <label>
          Corredor parado (segundos)
          <input
            type="number"
            min={1}
            value={parado}
            onChange={(e) => setParado(Number(e.target.value))}
          />
        </label>
        <label>
          Corredor en movimiento (segundos)
          <input
            type="number"
            min={1}
            value={movimiento}
            onChange={(e) => setMovimiento(Number(e.target.value))}
          />
        </label>
        <label>
          Umbral «sin señal» (segundos)
          <input
            type="number"
            min={1}
            value={umbral}
            onChange={(e) => setUmbral(Number(e.target.value))}
          />
        </label>
      </fieldset>

      <fieldset disabled={!rolAdmin}>
        <legend>Colores (la asociación verde=transmitiendo / ámbar=sin señal se conserva)</legend>
        <label>
          Transmitiendo
          <input type="color" value={colorTransmitiendo} onChange={(e) => setColorTransmitiendo(e.target.value)} />
        </label>
        <label>
          Sin señal
          <input type="color" value={colorSinSenal} onChange={(e) => setColorSinSenal(e.target.value)} />
        </label>
      </fieldset>

      <fieldset disabled={!rolAdmin}>
        <legend>Información visible en la web pública</legend>
        <label className="casilla">
          <input type="checkbox" checked={mostrarClub} onChange={(e) => setMostrarClub(e.target.checked)} />
          Mostrar club del corredor
        </label>
        <label className="casilla">
          <input
            type="checkbox"
            checked={mostrarPatrocinadores}
            onChange={(e) => setMostrarPatrocinadores(e.target.checked)}
          />
          Mostrar patrocinadores
        </label>
        <label className="casilla">
          <input
            type="checkbox"
            checked={mostrarNoticias}
            onChange={(e) => setMostrarNoticias(e.target.checked)}
          />
          Mostrar noticias
        </label>
      </fieldset>

      {rolAdmin && (
        <button type="submit" disabled={guardando}>
          {guardando ? "Guardando…" : "Guardar configuración"}
        </button>
      )}
      {error && <p className="error">{error}</p>}
      {aviso && <p className="aviso-ok">{aviso}</p>}
    </form>
  );
}
