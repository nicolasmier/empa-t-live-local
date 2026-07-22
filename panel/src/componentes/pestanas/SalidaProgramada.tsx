import { useEffect, useState } from "react";
import { api, mensajeError } from "../../api";

interface Props {
  eventoId: number;
  estado: string;
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

export function SalidaProgramada({ eventoId, estado, horaProgramada, onCambiado }: Props) {
  const [horaElegida, setHoraElegida] = useState(
    horaProgramada ? aHoraLocalInput(horaProgramada) : "",
  );
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [confirmandoReset, setConfirmandoReset] = useState(false);

  // Con el evento ya En directo: "restablecer la salida" lo devuelve a
  // Preparación (retroceso de un paso, spec §11). Los corredores dejan de
  // poder transmitir hasta la nueva salida; el histórico de posiciones NO se
  // borra. Al volver a Preparación reaparece el control de hora de abajo.
  async function alRestablecer() {
    setGuardando(true);
    setError(null);
    const { error } = await api.POST("/eventos/{evento_id}/estado", {
      params: { path: { evento_id: eventoId } },
      body: { estado: "preparacion" },
    });
    setGuardando(false);
    if (error) {
      setError(mensajeError(error, "No se pudo restablecer la salida."));
      return;
    }
    setConfirmandoReset(false);
    onCambiado();
  }

  if (estado === "en_directo") {
    return (
      <div className="salida-programada">
        <p className="salida-programada__titulo">Salida</p>
        <p className="texto-vacio">
          El evento está En directo. Si diste la salida por error o necesitas
          repetirla, restablécela: el evento vuelve a Preparación (los corredores
          dejan de transmitir hasta la nueva salida) y podrás fijar de nuevo la hora
          o lanzarla a mano. No se borran las posiciones ya recibidas.
        </p>
        <button type="button" className="boton-peligro" onClick={() => setConfirmandoReset(true)}>
          Restablecer salida
        </button>
        {error && <p className="error">{error}</p>}

        {confirmandoReset && (
          <div className="modal-fondo" role="presentation" onClick={() => setConfirmandoReset(false)}>
            <div className="modal" role="dialog" aria-modal="true" onClick={(e) => e.stopPropagation()}>
              <h3>Restablecer la salida</h3>
              <p>
                El evento volverá a Preparación. Los corredores dejarán de poder
                transmitir hasta que vuelvas a darle salida. El historial de
                posiciones se conserva.
              </p>
              <div className="modal__acciones">
                <button type="button" onClick={() => setConfirmandoReset(false)} disabled={guardando}>
                  Cancelar
                </button>
                <button type="button" className="boton-peligro" onClick={alRestablecer} disabled={guardando}>
                  {guardando ? "Restableciendo…" : "Sí, restablecer salida"}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

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
