import { Cronometro } from "./Cronometro";
import "./Cabecera.css";

interface Props {
  nombreEvento: string;
  enDirecto: boolean;
  inicioDirecto: string | null;
  conectado: boolean;
}

export function Cabecera({ nombreEvento, enDirecto, inicioDirecto, conectado }: Props) {
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
            <Cronometro enDirecto={enDirecto} inicioDirecto={inicioDirecto} />
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
