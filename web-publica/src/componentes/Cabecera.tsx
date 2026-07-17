import { Cronometro } from "./Cronometro";
import "./Cabecera.css";

interface Props {
  eventoId: number;
  nombreEvento: string;
  enDirecto: boolean;
  conectado: boolean;
}

export function Cabecera({ eventoId, nombreEvento, enDirecto, conectado }: Props) {
  return (
    <>
      <div className="cabecera-banner-envoltorio">
        <div className="cabecera-banner" role="presentation" />
      </div>
      <div className="cabecera-info">
        <p className="cabecera-info__prueba">{nombreEvento}</p>
        {enDirecto && (
          <p className="cabecera-info__crono-envoltorio">
            <span className="cabecera-info__punto-en-directo" />
            <Cronometro eventoId={eventoId} enDirecto={enDirecto} />
          </p>
        )}
        {!conectado && (
          <p className="cabecera-info__aviso-conexion" role="status">
            Sin conexión con el servidor — mostrando la última posición conocida
          </p>
        )}
      </div>
    </>
  );
}
