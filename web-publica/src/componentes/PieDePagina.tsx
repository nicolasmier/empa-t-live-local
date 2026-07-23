import { useState } from "react";
import "./PieDePagina.css";

/**
 * Pie de página de la web pública: marca CronoEmpate + enlace a empa-t.com, aviso
 * legal / protección de datos (modal, porque la web expone datos personales de
 * los corredores en directo) y, abajo a la derecha, el contacto del autor.
 */
export function PieDePagina() {
  const [legalAbierto, setLegalAbierto] = useState(false);

  return (
    <footer className="pie">
      <div className="pie__contenido">
        <div className="pie__marca">
          <img className="pie__logo" src="/logo-horizontal.png" alt="CronoEmpate" />
          <span className="pie__lema">Cronometraje deportivo</span>
        </div>

        <div className="pie__enlaces">
          <span>© {new Date().getFullYear()} CronoEmpate</span>
          <span className="pie__separador">·</span>
          <a href="https://empa-t.com" target="_blank" rel="noreferrer">
            empa-t.com
          </a>
          <span className="pie__separador">·</span>
          <button type="button" className="pie__legal" onClick={() => setLegalAbierto(true)}>
            Aviso legal · Protección de datos
          </button>
        </div>
      </div>

      <div className="pie__autor">
        <a href="https://github.com/nicolasmier" target="_blank" rel="noreferrer">
          github.com/nicolasmier
        </a>
      </div>

      {legalAbierto && (
        <div className="pie-modal__fondo" role="presentation" onClick={() => setLegalAbierto(false)}>
          <div
            className="pie-modal"
            role="dialog"
            aria-modal="true"
            aria-label="Aviso legal y protección de datos"
            onClick={(e) => e.stopPropagation()}
          >
            <h2>Aviso legal y protección de datos</h2>
            <p>
              Esta web muestra en tiempo real el dorsal, nombre, apellidos, club, foto y
              posición GPS de los corredores inscritos en el evento, con la única finalidad
              del seguimiento deportivo público de la carrera.
            </p>
            <p>
              Los datos proceden de la inscripción facilitada por el organizador y dejan de
              mostrarse al finalizar el evento. Para ejercer tus derechos de acceso,
              rectificación o supresión, contacta con el organizador de la prueba o con
              CronoEmpate a través de{" "}
              <a href="https://empa-t.com" target="_blank" rel="noreferrer">
                empa-t.com
              </a>
              .
            </p>
            <button type="button" className="pie-modal__cerrar" onClick={() => setLegalAbierto(false)}>
              Entendido
            </button>
          </div>
        </div>
      )}
    </footer>
  );
}
