interface Props {
  titulo: string;
  rol: "admin" | "operador" | null;
  vista: "listado" | "auditoria";
  onIrListado: () => void;
  onIrAuditoria: () => void;
  onCerrarSesion: () => void;
}

export function Cabecera({ titulo, rol, vista, onIrListado, onIrAuditoria, onCerrarSesion }: Props) {
  return (
    <header className="cabecera-panel">
      <div className="cabecera-panel__marca" onClick={onIrListado} role="button" tabIndex={0}>
        EmpateLive <span>Panel</span>
      </div>
      <h1>{titulo}</h1>
      <nav className="cabecera-panel__nav">
        <button
          type="button"
          className={`enlace-nav ${vista === "listado" ? "enlace-nav--activo" : ""}`}
          onClick={onIrListado}
        >
          Eventos
        </button>
        <button
          type="button"
          className={`enlace-nav ${vista === "auditoria" ? "enlace-nav--activo" : ""}`}
          onClick={onIrAuditoria}
        >
          Auditoría
        </button>
        <button
          type="button"
          className="enlace-nav"
          onClick={() =>
            window.open(`${window.location.protocol}//${window.location.hostname}:8081`, "_blank")
          }
          title="Abrir la web pública de seguimiento en una pestaña nueva"
        >
          Ver web pública ↗
        </button>
        {rol && <span className="cabecera-panel__rol">{rol === "admin" ? "Administrador" : "Operador"}</span>}
        <button type="button" onClick={onCerrarSesion}>
          Cerrar sesión
        </button>
      </nav>
    </header>
  );
}
