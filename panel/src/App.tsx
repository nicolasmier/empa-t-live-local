import { useState, type FormEvent } from "react";
import { api, borrarToken, guardarToken, obtenerToken } from "./api";
import { decodificarSesion, type SesionPanel } from "./auth";
import { Cabecera } from "./componentes/Cabecera";
import { EventosListado } from "./componentes/EventosListado";
import { EventoDetalle } from "./componentes/EventoDetalle";
import { Auditoria } from "./componentes/Auditoria";

type Vista = { tipo: "listado" } | { tipo: "evento"; id: number } | { tipo: "auditoria" };

function sesionInicial(): SesionPanel | null {
  const token = obtenerToken();
  return token ? decodificarSesion(token) : null;
}

function App() {
  const [sesion, setSesion] = useState<SesionPanel | null>(sesionInicial);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errorLogin, setErrorLogin] = useState<string | null>(null);
  const [cargandoLogin, setCargandoLogin] = useState(false);
  const [vista, setVista] = useState<Vista>({ tipo: "listado" });

  async function alEnviarLogin(evento: FormEvent) {
    evento.preventDefault();
    setCargandoLogin(true);
    setErrorLogin(null);
    const { data, error } = await api.POST("/auth/login", {
      body: { email, password },
    });
    setCargandoLogin(false);
    if (error || !data) {
      setErrorLogin("Email o contraseña incorrectos.");
      return;
    }
    guardarToken(data.access_token);
    setSesion(decodificarSesion(data.access_token));
  }

  function cerrarSesion() {
    borrarToken();
    setSesion(null);
    setVista({ tipo: "listado" });
  }

  if (!sesion) {
    return (
      <div className="pantalla-login">
        <img className="pantalla-login__logo" src="/cronoempate-logo.png" alt="CronoEmpate" />
        <h1>Panel de administración</h1>
        <form onSubmit={alEnviarLogin}>
          <p>
            <input
              type="email"
              placeholder="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </p>
          <p>
            <input
              type="password"
              placeholder="Contraseña"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </p>
          {errorLogin && <p className="error">{errorLogin}</p>}
          <button type="submit" disabled={cargandoLogin}>
            {cargandoLogin ? "Entrando…" : "Entrar"}
          </button>
        </form>
      </div>
    );
  }

  const rolAdmin = sesion.rol === "admin";

  return (
    <div className="app-panel">
      <Cabecera
        titulo={
          vista.tipo === "auditoria" ? "Auditoría" : vista.tipo === "evento" ? "Detalle del evento" : "Eventos"
        }
        rol={sesion.rol}
        vista={vista.tipo === "auditoria" ? "auditoria" : "listado"}
        onIrListado={() => setVista({ tipo: "listado" })}
        onIrAuditoria={() => setVista({ tipo: "auditoria" })}
        onCerrarSesion={cerrarSesion}
      />
      <main className="app-panel__contenido">
        {vista.tipo === "listado" && (
          <EventosListado
            rolAdmin={rolAdmin}
            onAbrirEvento={(id) => setVista({ tipo: "evento", id })}
          />
        )}
        {vista.tipo === "evento" && (
          <EventoDetalle
            eventoId={vista.id}
            rolAdmin={rolAdmin}
            onVolver={() => setVista({ tipo: "listado" })}
          />
        )}
        {vista.tipo === "auditoria" && <Auditoria />}
      </main>
    </div>
  );
}

export default App;
