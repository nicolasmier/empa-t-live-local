import { useEffect, useState } from "react";

interface Props {
  enDirecto: boolean;
  /** Instante (ISO, del servidor) en que el evento entró En directo por última
   * vez. Se refresca en cada entrada a En directo, así que al restablecer la
   * salida y volver a lanzarla el cronómetro parte de cero. */
  inicioDirecto: string | null;
}

/**
 * Tiempo transcurrido desde que el evento entró En directo, según la marca
 * `inicio_directo` del servidor (no el reloj local ni localStorage): así todos
 * los navegadores muestran lo mismo y una reprogramación de la salida resetea
 * el contador en todas las pantallas.
 */
export function Cronometro({ enDirecto, inicioDirecto }: Props) {
  const [ahora, setAhora] = useState(() => Date.now());

  useEffect(() => {
    const id = setInterval(() => setAhora(Date.now()), 1000);
    return () => clearInterval(id);
  }, []);

  if (!enDirecto || !inicioDirecto) return null;

  const inicio = new Date(inicioDirecto).getTime();
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
