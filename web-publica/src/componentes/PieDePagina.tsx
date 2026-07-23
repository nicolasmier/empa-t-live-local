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
        <span className="pie__autor-texto">un servicio diseñado por:</span>
        <a
          className="pie__autor-enlace"
          href="https://github.com/nicolasmier"
          target="_blank"
          rel="noreferrer"
        >
          <svg
            className="pie__github-icono"
            viewBox="0 0 16 16"
            width="22"
            height="22"
            fill="currentColor"
            aria-hidden="true"
          >
            <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z" />
          </svg>
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
