# ComoLleganLosDatosDelMovil

**Pregunta:** Los corredores no están en la LAN del recinto; llevan un móvil que
transmite con su propia conexión a internet. ¿Cómo llega eso al servidor montado
en el PC?

## Respuesta

A través de un **túnel de Cloudflare** (`cloudflared`) que corre en el PC del
recinto. No hace falta IP pública, DNS dinámico ni abrir puertos en el router.

```
Móvil corredor (su 4G/5G)
        │  HTTPS a https://api.tu-dominio.com
        ▼
   Cloudflare (borde)
        ▲  conexión SALIENTE que abre el PC
        │
  cloudflared en el PC ──► API local :8000
```

- `cloudflared` abre **él** una conexión saliente hacia Cloudflare.
- Cloudflare publica un hostname (`api.tu-dominio.com`) que enruta hasta la API
  local del PC.
- El móvil manda `POST /eventos/{id}/posiciones` a ese hostname; el PC "rescata"
  los datos igual que en LAN, solo cambia la puerta de entrada.

## Qué cambia respecto a una prueba en la misma WiFi

En una prueba local (móvil y PC en la misma red) la app puede apuntar directa a
la IP LAN del PC (`http://192.168.1.218:8000`). En **campo real** eso no sirve
—el móvil está en otra red— y es **imprescindible** el túnel. Lo único que cambia
en la app es la URL con la que se compila el APK:

```
./gradlew assembleDebug -PurlServidor=https://api.tu-dominio.com
```

## Requisitos (configuración única)

Cuenta gratuita de Cloudflare + un dominio propio. Pasos completos en
`docs/guia_tunel_cloudflare.md`. Referencia en spec v10 (tabla §138, §376,
Anexo D).

Ver también: [QueSeExponePorInternet](QueSeExponePorInternet.md).
