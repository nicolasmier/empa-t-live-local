import { useEffect, useState } from "react";
import { api, mensajeError } from "../../api";

interface Props {
  eventoId: number;
  horaProgramada: string | null;
  onCambiado: () => void;
}

const INTERVALO_SONDEO_MS = 5000;

// El input datetime-local trabaja en la hora local del navegador; como el
// panel se usa en el mismo PC que hace de servidor (spec: un único PC por
// evento), esa hora local ES la hora del PC — new Date(...).toISOString()
// ya la convierte al instante UTC correcto para guardar y comparar.
function aHoraLocalInput(iso: string): string {
  const fecha = new Date(iso);
  const desplazamiento = fecha.getTimezoneOffset() * 60000;
  return new Date(fecha.getTime() - desplazamiento).toISOString().slice(0, 16);
}

export function SalidaProgramada({ eventoId, horaProgramada, onCambiado }: Props) {
  const [horaElegida, setHoraElegida] = useState(
    horaProgramada ? aHoraLocalInput(horaProgramada) : "",
  );
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setHoraElegida(horaProgramada ? aHoraLocalInput(horaProgramada) : "");
  }, [horaProgramada]);

  // Sondeo ligero mientras hay una salida programada pendiente: el cambio a
  // En directo lo dispara el servidor en segundo plano, no un clic en el
  // panel, así que hay que refrescar sola para que se note sin recargar.
  useEffect(() => {
    if (!horaProgramada) return;
    const id = setInterval(onCambiado, INTERVALO_SONDEO_MS);
    return () => clearInterval(id);
  }, [horaProgramada, onCambiado]);

  async function alProgramar() {
    if (!horaElegida) return;
    setGuardando(true);
    setError(null);
    const { error } = await api.PUT("/eventos/{evento_id}", {
      params: { path: { evento_id: eventoId } },
      body: { hora_programada_directo: new Date(horaElegida).toISOString() },
    });
    setGuardando(false);
    if (error) {
      setError(mensajeError(error, "No se pudo programar la salida."));
      return;
    }
    onCambiado();
  }

  async function alCancelar() {
    setGuardando(true);
    setError(null);
    const { error } = await api.PUT("/eventos/{evento_id}", {
      params: { path: { evento_id: eventoId } },
      body: { hora_programada_directo: null },
    });
    setGuardando(false);
    if (error) {
      setError(mensajeError(error, "No se pudo cancelar la salida programada."));
      return;
    }
    onCambiado();
  }

  return (
    <div className="salida-programada">
      <p className="salida-programada__titulo">Salida programada</p>
      <p className="texto-vacio">
        Pasa el evento de Preparación a En directo automáticamente a la hora que elijas
        (hora de este PC) — útil para no depender de estar pendiente del reloj en el
        momento de la salida.
      </p>

      {horaProgramada && (
        <p className="aviso-ok">
          Programada para el {new Date(horaProgramada).toLocaleString("es-ES")}.
        </p>
      )}

      <div className="salida-programada__controles">
        <input
          type="datetime-local"
          value={horaElegida}
          onChange={(e) => setHoraElegida(e.target.value)}
          disabled={guardando}
        />
        <button type="button" onClick={alProgramar} disabled={guardando || !horaElegida}>
          {guardando ? "Guardando…" : horaProgramada ? "Actualizar" : "Programar"}
        </button>
        {horaProgramada && (
          <button type="button" onClick={alCancelar} disabled={guardando} className="boton-enlace">
            Cancelar programación
          </button>
        )}
      </div>
      {error && <p className="error">{error}</p>}
    </div>
  );
}
