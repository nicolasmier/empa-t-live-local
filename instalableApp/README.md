# Instalable EmpateLive — prueba en condiciones reales

Esta carpeta contiene el APK del corredor listo para instalar en un móvil
Android real (no el emulador) y los pasos para levantar el servidor y
probar el sistema completo — servidor, web y app — en tu propia red WiFi.

## Qué hay aquí

- **`EmpateLive-Corredor.apk`** — la app del corredor, compilada apuntando
  directamente a `http://192.168.1.218:8000` (la IP LAN de este PC en el
  momento de generarla). **Si la IP de este PC cambia** (otra red WiFi,
  reinicio del router...), el APK deja de encontrar el servidor y hay que
  regenerarlo — instrucciones al final de este documento.
- **Este README**.

## 0. Requisitos antes de empezar

- El **móvil y este PC deben estar en la misma red WiFi**. El túnel de
  Cloudflare no hace falta para esta prueba: la app habla directo por LAN.
- En el móvil: **Ajustes → Seguridad → permitir instalar apps de fuentes
  desconocidas** para la app que uses para abrir el APK (Archivos, Gmail,
  lo que sea) — Android lo pide automáticamente la primera vez si no está
  ya permitido.
- Comprueba que no hay un firewall bloqueando los puertos 8000 (API/app),
  8080 (panel) y 8081 (web pública) en este PC. Si tienes `firewalld`
  activo y no ves el panel desde el móvil, ese es el primer sospechoso.

## 1. Levantar el servidor

Doble clic en el icono **EmpateLive Launcher** del escritorio (o
`~/.local/bin/empatelive-launcher` desde terminal) → **Iniciar servidor**.
Espera a que el estado pase a "en marcha" (verde).

Comprueba que responde desde el propio PC:
- Panel: http://localhost:8080
- Web pública: http://localhost:8081

## 2. Pasar el APK al móvil

Cualquier vía sirve — elige la que tengas más a mano:
- **Cable USB**: copia `EmpateLive-Corredor.apk` a la carpeta de Descargas
  del móvil y ábrelo desde el gestor de archivos del teléfono.
- **Google Drive / WhatsApp / Telegram / email**: súbelo o envíatelo y
  ábrelo desde el móvil.
- **ADB** (si tienes el móvil en modo depuración USB y `adb` instalado):
  ```
  adb install EmpateLive-Corredor.apk
  ```

Instala normalmente, aceptando el aviso de "fuente desconocida" si aparece.

## 3. Datos de la prueba ya preparados

Para que puedas empezar a probar sin tener que montar nada desde cero, ya
hay un evento real en marcha y un corredor de prueba cargado:

| Dato | Valor |
|---|---|
| Panel de administración | http://192.168.1.218:8080 |
| Usuario admin del panel | `admin@cronoempate.com` |
| Contraseña admin | `EmpateLive2026` |
| Evento | Villacabra 2026 (código `DEMO-VILLACABRA`), ya en estado **En directo** |
| Corredor de prueba (email) | `prueba.campo@cronoempate.com` |
| Dorsal del corredor de prueba | `9001` |

Ese corredor está **pre-cargado pero sin contraseña todavía** (así es como
llega un corredor importado por Excel antes de que se registre él mismo en
la app) — el primer paso en el móvil es completar su registro con ese
mismo email.

## 4. Paso a paso en el móvil

1. Abre **EmpateLive — Corredor**.
2. **¿No tienes cuenta? Regístrate.**
   - Nombre/Apellidos: lo que quieras (no pisa lo que ya cargó el
     organizador).
   - Email: `prueba.campo@cronoempate.com` (exacto, es el que activa la
     cuenta pre-cargada).
   - Contraseña: la que quieras, mínimo 8 caracteres — apúntatela.
   - Teléfono: déjalo vacío, no hace falta aquí.
3. En **Tu perfil**, rellena lo que quieras (o nada) y pulsa **Continuar**
   — prueba también a **Elegir foto** para comprobar la subida real.
4. En **Unirte a la carrera**:
   - Código de la carrera: `DEMO-VILLACABRA`
   - Tu dorsal: `9001`
   - **Unirme**.
5. Verás la pantalla de estado con el dorsal `9001` en grande. Pulsa
   **Activar GPS para el evento** y concede el permiso de ubicación
   ("mientras se usa la app" es lo correcto, no hace falta "todo el
   tiempo"). Si el móvil ofrece desactivar el ahorro de batería para la
   app, acéptalo también — si no, Android puede cortar la transmisión al
   rato.
6. Sal a caminar/andar en bici/moverte con el móvil en el bolsillo. La
   pantalla de estado debe pasar a "Transmitiendo" / "Enviando" / "Te ve
   transmitiendo" en verde.

## 5. Comprobar que se ve de verdad

- Abre **http://192.168.1.218:8081** (web pública) desde cualquier
  ordenador o móvil de la misma red — deberías ver el dorsal `9001`
  moviéndose sobre el mapa de "La corta 14k" en tiempo casi real (la web
  sondea cada 3-5 s).
- Abre **http://192.168.1.218:8080** (panel) con las credenciales de
  arriba → evento Villacabra 2026 → pestaña Corredores, para ver el
  dorsal `9001` con su estado de transmisión.
- Si quieres cargar corredores reales de verdad (no solo el de prueba),
  usa la pestaña **Corredores → Importar Excel** del panel: columnas
  `nombre`, `apellidos`, `dorsal` obligatorias, y `email` **o** `telefono`
  (basta con una de las dos), `club` opcional.

## 6. Qué mirar durante la prueba (checklist de campo)

- [ ] El GPS sigue transmitiendo con la pantalla del móvil apagada.
- [ ] Al meter el móvil en modo avión un rato y volver a activar los
      datos, los puntos perdidos se recuperan solos (mira el contador
      "Encolando sin conexión (N)" mientras está sin red, y que baje a 0
      al reconectar).
- [ ] La posición en la web pública no da saltos raros ni retrocede.
- [ ] Consumo de batería aproximado tras un rato de prueba (Ajustes →
      Batería → uso por app) — el objetivo orientativo de la spec es
      **menos de ~10%/hora** transmitiendo.
- [ ] Cerrar la app deslizándola desde recientes **debe parar** la
      transmisión (no debe resucitar sola) — es el comportamiento
      esperado, no un fallo.

## 7. Si la IP del servidor cambia (regenerar el APK)

Este PC ya no tiene por qué seguir siendo `192.168.1.218` en otra red.
Para comprobar la IP actual:

```bash
ip -4 addr show | grep -oP '(?<=inet )\d+(\.\d+){3}' | grep -v '^127\.'
```

Y para reconstruir el APK con la IP correcta (desde la raíz del repo):

```bash
cd app-android
./gradlew assembleDebug -PurlServidor=http://<IP-NUEVA>:8000
cp app/build/outputs/apk/debug/app-debug.apk ../instalableApp/EmpateLive-Corredor.apk
```

Sin el parámetro `-PurlServidor`, el build vuelve a apuntar al alias del
emulador (`10.0.2.2`) — solo sirve para pruebas en el emulador, no en un
móvil real.

## Notas

- Es un build de **debug** (firmado con la clave de depuración de
  Android), no de release — normal y esperado para pruebas de campo, no
  para publicar en ninguna tienda.
- Esta prueba usa la LAN directa, no el túnel de Cloudflare. La spec
  contempla ambos caminos para la app del corredor; el túnel entra en
  juego cuando el corredor no está en la misma red que el servidor (caso
  real del día de carrera con cientos de móviles por datos móviles).
