import qrcode from "./vendor/qrcode.mjs";

const invoke = window.__TAURI__.core.invoke;

const INTERVALO_SONDEO_MS = 4000;

const textoEstado = document.getElementById("texto-estado");
const botonPrincipal = document.getElementById("boton-principal");
const mensajeError = document.getElementById("mensaje-error");

const semaforoTunel = document.getElementById("semaforo-tunel");
const textoTunel = document.getElementById("texto-tunel");
const semaforoTransmitiendo = document.getElementById("semaforo-transmitiendo");
const textoTransmitiendo = document.getElementById("texto-transmitiendo");
const semaforoIncidencias = document.getElementById("semaforo-incidencias");
const textoIncidencias = document.getElementById("texto-incidencias");

const urlPanel = document.getElementById("url-panel");
const urlWebPublica = document.getElementById("url-web-publica");
const qrPanel = document.getElementById("qr-panel");
const qrWebPublica = document.getElementById("qr-web-publica");

let estadoActual = "detenido";
let accionEnCurso = false;
let sondeando = false;

const ETIQUETAS_ESTADO = {
  detenido: "Servidor detenido",
  iniciando: "Servidor iniciando…",
  activo: "Servidor activo",
};

const ETIQUETAS_TUNEL = {
  no_configurado: "No configurado",
  conectado: "Conectado",
  caido: "Caído",
};

function pintarQR(contenedor, texto) {
  const qr = qrcode(0, "M");
  qr.addData(texto);
  qr.make();
  contenedor.innerHTML = qr.createImgTag(4, 4);
}

function actualizarBotonPrincipal() {
  if (accionEnCurso) {
    botonPrincipal.disabled = true;
    botonPrincipal.textContent = estadoActual === "activo" ? "Deteniendo…" : "Iniciando…";
    return;
  }
  botonPrincipal.disabled = false;
  if (estadoActual === "activo" || estadoActual === "iniciando") {
    botonPrincipal.textContent = "Detener servidor";
    botonPrincipal.classList.add("detener");
  } else {
    botonPrincipal.textContent = "Iniciar servidor";
    botonPrincipal.classList.remove("detener");
  }
}

async function refrescarEstadoServidor() {
  try {
    const estado = await invoke("estado_servidor");
    estadoActual = estado.estado;
    textoEstado.textContent = ETIQUETAS_ESTADO[estado.estado] ?? estado.estado;
    textoEstado.className = `valor ${estado.estado}`;

    textoTunel.textContent = ETIQUETAS_TUNEL[estado.tunel] ?? estado.tunel;
    semaforoTunel.className =
      "semaforo " + (estado.tunel === "conectado" ? "ok" : estado.tunel === "caido" ? "mal" : "");

    mensajeError.textContent = "";
  } catch (error) {
    mensajeError.textContent = String(error);
  }
  actualizarBotonPrincipal();
}

async function refrescarResumenOperativo() {
  try {
    const resumen = await invoke("resumen_operativo");
    textoTransmitiendo.textContent = String(resumen.corredores_transmitiendo);
    semaforoTransmitiendo.className =
      "semaforo " + (resumen.corredores_transmitiendo > 0 ? "ok" : "");

    textoIncidencias.textContent = String(resumen.incidencias_abiertas);
    semaforoIncidencias.className =
      "semaforo " + (resumen.incidencias_abiertas > 0 ? "alerta" : "ok");
  } catch {
    // El servidor puede estar detenido o aún arrancando: no es un error que
    // deba tapar el mensaje de estado principal.
    textoTransmitiendo.textContent = "—";
    textoIncidencias.textContent = "—";
    semaforoTransmitiendo.className = "semaforo";
    semaforoIncidencias.className = "semaforo";
  }
}

async function cargarDireccionesLan() {
  try {
    const direcciones = await invoke("direcciones_lan");
    urlPanel.textContent = direcciones.panel;
    urlWebPublica.textContent = direcciones.web_publica;
    pintarQR(qrPanel, direcciones.panel);
    pintarQR(qrWebPublica, direcciones.web_publica);
  } catch (error) {
    urlPanel.textContent = "No se pudo detectar la IP de la red";
    urlWebPublica.textContent = "No se pudo detectar la IP de la red";
    mensajeError.textContent = String(error);
  }
}

async function sondear() {
  // Sin esto, un sondeo lento (docker compose ps/up/down puede tardar
  // segundos, sobre todo justo tras pulsar Iniciar/Detener) se solapa con el
  // siguiente disparo del intervalo, acumulando invocaciones de `docker`
  // concurrentes contra el mismo proyecto — lo que hace que la ventana
  // parezca colgada hasta que Docker termina de despejar la cola. Mientras
  // hay una acción en curso tampoco hace falta sondear: en cuanto termine,
  // `alPulsarBotonPrincipal` ya refresca el estado directamente.
  if (sondeando || accionEnCurso) return;
  sondeando = true;
  try {
    await refrescarEstadoServidor();
    await refrescarResumenOperativo();
  } finally {
    sondeando = false;
  }
}

async function alPulsarBotonPrincipal() {
  accionEnCurso = true;
  actualizarBotonPrincipal();
  mensajeError.textContent = "";
  try {
    if (estadoActual === "activo" || estadoActual === "iniciando") {
      await invoke("detener_servidor");
    } else {
      await invoke("iniciar_servidor");
    }
  } catch (error) {
    mensajeError.textContent = String(error);
  }
  accionEnCurso = false;
  await sondear();
}

document.querySelectorAll("[data-copiar]").forEach((boton) => {
  boton.addEventListener("click", () => {
    const origen = document.getElementById(boton.dataset.copiar);
    navigator.clipboard.writeText(origen.textContent);
    const textoOriginal = boton.textContent;
    boton.textContent = "¡Copiado!";
    setTimeout(() => {
      boton.textContent = textoOriginal;
    }, 1500);
  });
});

botonPrincipal.addEventListener("click", alPulsarBotonPrincipal);

cargarDireccionesLan();
sondear();
setInterval(sondear, INTERVALO_SONDEO_MS);
