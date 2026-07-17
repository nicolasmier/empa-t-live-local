import { useEffect, useState } from "react";

interface Props {
  eventoId: number;
  enDirecto: boolean;
}

function claveInicio(eventoId: number): string {
  return `empatelive_inicio_${eventoId}`;
}

/**
 * Tiempo transcurrido desde que este navegador vio el evento En directo por
 * primera vez (persistido en localStorage: sobrevive a un refresco de página).
 * La spec no define una "hora de inicio" en el modelo de datos — es la
 * interpretación más razonable disponible sin ese dato del servidor.
 */
export function Cronometro({ eventoId, enDirecto }: Props) {
  const [ahora, setAhora] = useState(() => Date.now());

  useEffect(() => {
    const id = setInterval(() => setAhora(Date.now()), 1000);
    return () => clearInterval(id);
  }, []);

  if (!enDirecto) return null;

  const clave = claveInicio(eventoId);
  let inicio = Number(localStorage.getItem(clave));
  if (!inicio) {
    inicio = Date.now();
    localStorage.setItem(clave, String(inicio));
  }

  const transcurridoSeg = Math.max(0, Math.floor((ahora - inicio) / 1000));
  const horas = Math.floor(transcurridoSeg / 3600);
  const minutos = Math.floor((transcurridoSeg % 3600) / 60);
  const segundos = transcurridoSeg % 60;
  const texto = [horas, minutos, segundos].map((n) => String(n).padStart(2, "0")).join(":");

  return (
    <span className="cronometro" aria-label="Tiempo transcurrido">
      {texto}
    </span>
  );
}
