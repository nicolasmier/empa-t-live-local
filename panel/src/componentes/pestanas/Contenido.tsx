import { useEffect, useRef, useState, type FormEvent } from "react";
import { normalizarUrlExterna, type components } from "@empatelive/web-shared";
import { api, mensajeError, urlMedia } from "../../api";

type Evento = components["schemas"]["EventoSalida"];
type Patrocinador = components["schemas"]["PatrocinadorSalida"];
type Noticia = components["schemas"]["NoticiaSalida"];

interface Props {
  evento: Evento;
  rolAdmin: boolean;
  onActualizado: () => void;
}

export function Contenido({ evento, rolAdmin, onActualizado }: Props) {
  return (
    <div className="bloque-pestana">
      <BloqueCartel evento={evento} rolAdmin={rolAdmin} onActualizado={onActualizado} />
      <BloquePatrocinadores eventoId={evento.id} rolAdmin={rolAdmin} />
      <BloqueNoticias eventoId={evento.id} rolAdmin={rolAdmin} />
    </div>
  );
}

function BloqueCartel({ evento, rolAdmin, onActualizado }: Props) {
  const [subiendo, setSubiendo] = useState(false);
  const [borrando, setBorrando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);

  async function alSubir(archivo: File) {
    setSubiendo(true);
    setError(null);
    const formData = new FormData();
    formData.append("archivo", archivo);
    const { error } = await api.POST("/eventos/{evento_id}/cartel", {
      params: { path: { evento_id: evento.id } },
      body: formData as unknown as { archivo: string },
    });
    setSubiendo(false);
    if (inputRef.current) inputRef.current.value = "";
    if (error) {
      setError(mensajeError(error, "No se pudo subir el cartel."));
      return;
    }
    onActualizado();
  }

  async function alQuitar() {
    setBorrando(true);
    setError(null);
    const { error } = await api.DELETE("/eventos/{evento_id}/cartel", {
      params: { path: { evento_id: evento.id } },
    });
    setBorrando(false);
    if (error) {
      setError(mensajeError(error, "No se pudo quitar el cartel."));
      return;
    }
    onActualizado();
  }

  const url = urlMedia(evento.cartel_url);

  return (
    <fieldset className="tarjeta">
      <legend>Cartel</legend>
      {url && <img src={url} alt="Cartel del evento" className="vista-previa-cartel" />}
      {rolAdmin && (
        <>
          <input
            ref={inputRef}
            type="file"
            accept=".jpg,.jpeg,.png"
            disabled={subiendo}
            onChange={(e) => {
              const archivo = e.target.files?.[0];
              if (archivo) alSubir(archivo);
            }}
          />
          {subiendo && <span> Subiendo…</span>}
          {url && (
            <button
              type="button"
              className="boton-enlace boton-enlace--peligro"
              onClick={alQuitar}
              disabled={borrando}
            >
              {borrando ? "Quitando…" : "Quitar cartel"}
            </button>
          )}
        </>
      )}
      {error && <p className="error">{error}</p>}
    </fieldset>
  );
}

function BloquePatrocinadores({ eventoId, rolAdmin }: { eventoId: number; rolAdmin: boolean }) {
  const [lista, setLista] = useState<Patrocinador[] | null>(null);
  const [nombre, setNombre] = useState("");
  const [enlace, setEnlace] = useState("");
  const [creando, setCreando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editandoId, setEditandoId] = useState<number | null>(null);
  const [borrandoId, setBorrandoId] = useState<number | null>(null);

  useEffect(() => {
    cargar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [eventoId]);

  async function cargar() {
    const { data, error } = await api.GET("/eventos/{evento_id}/patrocinadores", {
      params: { path: { evento_id: eventoId } },
    });
    if (error) {
      setError("No se pudieron cargar los patrocinadores.");
      return;
    }
    setLista(data);
  }

  async function alCrear(e: FormEvent) {
    e.preventDefault();
    setCreando(true);
    setError(null);
    const { error } = await api.POST("/eventos/{evento_id}/patrocinadores", {
      params: { path: { evento_id: eventoId } },
      body: { nombre, enlace_url: enlace || undefined, orden: 0 },
    });
    setCreando(false);
    if (error) {
      setError(mensajeError(error, "No se pudo crear el patrocinador."));
      return;
    }
    setNombre("");
    setEnlace("");
    await cargar();
  }

  async function alBorrar(id: number) {
    setBorrandoId(id);
    await api.DELETE("/patrocinadores/{patrocinador_id}", {
      params: { path: { patrocinador_id: id } },
    });
    setBorrandoId(null);
    await cargar();
  }

  return (
    <fieldset className="tarjeta">
      <legend>Patrocinadores</legend>
      {rolAdmin && (
        <form className="formulario-tarjeta formulario-tarjeta--fila" onSubmit={alCrear}>
          <input value={nombre} onChange={(e) => setNombre(e.target.value)} placeholder="Nombre" required />
          <input
            value={enlace}
            onChange={(e) => setEnlace(e.target.value)}
            placeholder="Enlace (opcional, p. ej. empresa.com)"
          />
          <button type="submit" disabled={creando}>
            {creando ? "Añadiendo…" : "Añadir"}
          </button>
        </form>
      )}
      {error && <p className="error">{error}</p>}
      {lista && lista.length === 0 && <p className="texto-vacio">Sin patrocinadores todavía.</p>}
      {lista && lista.length > 0 && (
        <ul className="lista-simple">
          {lista.map((p) =>
            editandoId === p.id ? (
              <EdicionPatrocinador
                key={p.id}
                patrocinador={p}
                onCancelar={() => setEditandoId(null)}
                onGuardado={async () => {
                  setEditandoId(null);
                  await cargar();
                }}
              />
            ) : (
              <li key={p.id}>
                <span>{p.nombre}</span>
                {p.enlace_url && (
                  <a href={normalizarUrlExterna(p.enlace_url)} target="_blank" rel="noreferrer">
                    {p.enlace_url}
                  </a>
                )}
                {rolAdmin && (
                  <>
                    <button type="button" className="boton-enlace" onClick={() => setEditandoId(p.id)}>
                      Editar
                    </button>
                    <button
                      type="button"
                      className="boton-enlace boton-enlace--peligro"
                      disabled={borrandoId === p.id}
                      onClick={() => alBorrar(p.id)}
                    >
                      {borrandoId === p.id ? "Borrando…" : "Borrar"}
                    </button>
                  </>
                )}
              </li>
            ),
          )}
        </ul>
      )}
    </fieldset>
  );
}

function EdicionPatrocinador({
  patrocinador,
  onCancelar,
  onGuardado,
}: {
  patrocinador: Patrocinador;
  onCancelar: () => void;
  onGuardado: () => void;
}) {
  const [nombre, setNombre] = useState(patrocinador.nombre);
  const [enlace, setEnlace] = useState(patrocinador.enlace_url ?? "");
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function alGuardar() {
    setGuardando(true);
    setError(null);
    const { error } = await api.PUT("/patrocinadores/{patrocinador_id}", {
      params: { path: { patrocinador_id: patrocinador.id } },
      body: { nombre, enlace_url: enlace || null },
    });
    setGuardando(false);
    if (error) {
      setError(mensajeError(error, "No se pudo guardar."));
      return;
    }
    onGuardado();
  }

  return (
    <li className="lista-simple__edicion">
      <input value={nombre} onChange={(e) => setNombre(e.target.value)} />
      <input value={enlace} onChange={(e) => setEnlace(e.target.value)} placeholder="Enlace" />
      <button type="button" onClick={alGuardar} disabled={guardando}>
        Guardar
      </button>
      <button type="button" onClick={onCancelar} disabled={guardando}>
        Cancelar
      </button>
      {error && <p className="error">{error}</p>}
    </li>
  );
}

function BloqueNoticias({ eventoId, rolAdmin }: { eventoId: number; rolAdmin: boolean }) {
  const [lista, setLista] = useState<Noticia[] | null>(null);
  const [titulo, setTitulo] = useState("");
  const [contenido, setContenido] = useState("");
  const [creando, setCreando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editandoId, setEditandoId] = useState<number | null>(null);
  const [borrandoId, setBorrandoId] = useState<number | null>(null);

  useEffect(() => {
    cargar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [eventoId]);

  async function cargar() {
    const { data, error } = await api.GET("/eventos/{evento_id}/noticias", {
      params: { path: { evento_id: eventoId } },
    });
    if (error) {
      setError("No se pudieron cargar las noticias.");
      return;
    }
    setLista(data);
  }

  async function alCrear(e: FormEvent) {
    e.preventDefault();
    setCreando(true);
    setError(null);
    const { error } = await api.POST("/eventos/{evento_id}/noticias", {
      params: { path: { evento_id: eventoId } },
      body: { titulo, contenido },
    });
    setCreando(false);
    if (error) {
      setError(mensajeError(error, "No se pudo crear la noticia."));
      return;
    }
    setTitulo("");
    setContenido("");
    await cargar();
  }

  async function alBorrar(id: number) {
    setBorrandoId(id);
    await api.DELETE("/noticias/{noticia_id}", { params: { path: { noticia_id: id } } });
    setBorrandoId(null);
    await cargar();
  }

  return (
    <fieldset className="tarjeta">
      <legend>Noticias</legend>
      {rolAdmin && (
        <form className="formulario-tarjeta" onSubmit={alCrear}>
          <input value={titulo} onChange={(e) => setTitulo(e.target.value)} placeholder="Título" required />
          <textarea
            value={contenido}
            onChange={(e) => setContenido(e.target.value)}
            placeholder="Contenido"
            required
          />
          <button type="submit" disabled={creando}>
            {creando ? "Publicando…" : "Publicar noticia"}
          </button>
        </form>
      )}
      {error && <p className="error">{error}</p>}
      {lista && lista.length === 0 && <p className="texto-vacio">Sin noticias todavía.</p>}
      {lista && lista.length > 0 && (
        <ul className="lista-simple">
          {lista.map((n) =>
            editandoId === n.id ? (
              <EdicionNoticia
                key={n.id}
                noticia={n}
                onCancelar={() => setEditandoId(null)}
                onGuardado={async () => {
                  setEditandoId(null);
                  await cargar();
                }}
              />
            ) : (
              <li key={n.id}>
                <strong>{n.titulo}</strong>
                <p>{n.contenido}</p>
                {rolAdmin && (
                  <>
                    <button type="button" className="boton-enlace" onClick={() => setEditandoId(n.id)}>
                      Editar
                    </button>
                    <button
                      type="button"
                      className="boton-enlace boton-enlace--peligro"
                      disabled={borrandoId === n.id}
                      onClick={() => alBorrar(n.id)}
                    >
                      {borrandoId === n.id ? "Borrando…" : "Borrar"}
                    </button>
                  </>
                )}
              </li>
            ),
          )}
        </ul>
      )}
    </fieldset>
  );
}

function EdicionNoticia({
  noticia,
  onCancelar,
  onGuardado,
}: {
  noticia: Noticia;
  onCancelar: () => void;
  onGuardado: () => void;
}) {
  const [titulo, setTitulo] = useState(noticia.titulo);
  const [contenido, setContenido] = useState(noticia.contenido);
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function alGuardar() {
    setGuardando(true);
    setError(null);
    const { error } = await api.PUT("/noticias/{noticia_id}", {
      params: { path: { noticia_id: noticia.id } },
      body: { titulo, contenido },
    });
    setGuardando(false);
    if (error) {
      setError(mensajeError(error, "No se pudo guardar."));
      return;
    }
    onGuardado();
  }

  return (
    <li className="lista-simple__edicion">
      <input value={titulo} onChange={(e) => setTitulo(e.target.value)} />
      <textarea value={contenido} onChange={(e) => setContenido(e.target.value)} />
      <button type="button" onClick={alGuardar} disabled={guardando}>
        Guardar
      </button>
      <button type="button" onClick={onCancelar} disabled={guardando}>
        Cancelar
      </button>
      {error && <p className="error">{error}</p>}
    </li>
  );
}
