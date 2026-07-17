import { useState } from "react";
import { api, mensajeError } from "../../api";
import {
  ETIQUETAS_ESTADO,
  transicionSensible,
  transicionesValidas,
  type EstadoEvento,
} from "../../dominio/estadosEvento";

interface Props {
  eventoId: number;
  estadoActual: EstadoEvento;
  onCambiado: () => void;
}

const AVISOS_SENSIBLES: Partial<Record<EstadoEvento, string>> = {
  en_directo: "El evento pasará a En directo: los corredores podrán empezar a transmitir su posición.",
  finalizado:
    "El evento pasará a Finalizado: se revocarán todos los tokens de dispositivo (los corredores dejarán de poder transmitir) y se disparará una copia de seguridad automática. Esta acción no se puede deshacer con un simple retroceso.",
};

export function EstadoControl({ eventoId, estadoActual, onCambiado }: Props) {
  const [pendiente, setPendiente] = useState<EstadoEvento | null>(null);
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const destinos = transicionesValidas(estadoActual);

  async function ejecutar(destino: EstadoEvento) {
    setEnviando(true);
    setError(null);
    const { error } = await api.POST("/eventos/{evento_id}/estado", {
      params: { path: { evento_id: eventoId } },
      body: { estado: destino },
    });
    setEnviando(false);
    if (error) {
      setError(mensajeError(error, "No se pudo cambiar el estado del evento."));
      return;
    }
    setPendiente(null);
    onCambiado();
  }

  function alPulsar(destino: EstadoEvento) {
    if (transicionSensible(destino)) {
      setPendiente(destino);
      return;
    }
    ejecutar(destino);
  }

  return (
    <div className="control-estado">
      <p>
        Estado actual: <strong>{ETIQUETAS_ESTADO[estadoActual]}</strong>
      </p>
      {destinos.length === 0 ? (
        <p className="texto-vacio">Este evento está archivado; no admite más cambios de estado.</p>
      ) : (
        <div className="control-estado__botones">
          {destinos.map((destino) => (
            <button
              key={destino}
              type="button"
              disabled={enviando}
              onClick={() => alPulsar(destino)}
            >
              Pasar a {ETIQUETAS_ESTADO[destino]}
            </button>
          ))}
        </div>
      )}
      {error && <p className="error">{error}</p>}

      {pendiente && (
        <div className="modal-fondo" role="presentation" onClick={() => setPendiente(null)}>
          <div className="modal" role="dialog" aria-modal="true" onClick={(e) => e.stopPropagation()}>
            <h3>Confirmar cambio a «{ETIQUETAS_ESTADO[pendiente]}»</h3>
            <p>{AVISOS_SENSIBLES[pendiente]}</p>
            <div className="modal__acciones">
              <button type="button" onClick={() => setPendiente(null)} disabled={enviando}>
                Cancelar
              </button>
              <button type="button" className="boton-peligro" onClick={() => ejecutar(pendiente)} disabled={enviando}>
                {enviando ? "Aplicando…" : `Sí, pasar a ${ETIQUETAS_ESTADO[pendiente]}`}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
