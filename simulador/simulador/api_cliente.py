"""Cliente HTTP asíncrono contra la API real (spec v10 Anexo B): sin atajos por BD."""

from __future__ import annotations

from typing import Any

import httpx


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


class ClienteAPI:
    def __init__(self, base_url: str, timeout: float = 15.0) -> None:
        self._cliente = httpx.AsyncClient(
            base_url=base_url,
            timeout=timeout,
            limits=httpx.Limits(max_connections=300, max_keepalive_connections=100),
        )

    async def cerrar(self) -> None:
        await self._cliente.aclose()

    async def login_admin(self, email: str, password: str) -> str:
        r = await self._cliente.post("/auth/login", json={"email": email, "password": password})
        r.raise_for_status()
        return r.json()["access_token"]

    async def crear_evento(
        self, token: str, nombre: str, codigo_acceso: str, fecha: str
    ) -> dict[str, Any]:
        r = await self._cliente.post(
            "/eventos",
            json={"nombre": nombre, "codigo_acceso": codigo_acceso, "fecha": fecha},
            headers=_auth(token),
        )
        r.raise_for_status()
        return r.json()

    async def crear_distancia(self, token: str, evento_id: int, nombre: str) -> dict[str, Any]:
        r = await self._cliente.post(
            f"/eventos/{evento_id}/distancias", json={"nombre": nombre}, headers=_auth(token)
        )
        r.raise_for_status()
        return r.json()

    async def subir_gpx(self, token: str, distancia_id: int, contenido: bytes) -> None:
        r = await self._cliente.post(
            f"/distancias/{distancia_id}/gpx",
            files={"archivo": ("ruta.gpx", contenido, "application/gpx+xml")},
            headers=_auth(token),
        )
        r.raise_for_status()

    async def importar_corredores(
        self, token: str, distancia_id: int, excel_bytes: bytes
    ) -> dict[str, Any]:
        r = await self._cliente.post(
            f"/distancias/{distancia_id}/corredores/importar",
            files={"archivo": ("corredores.xlsx", excel_bytes, "application/octet-stream")},
            headers=_auth(token),
        )
        r.raise_for_status()
        return r.json()

    async def cambiar_estado_evento(self, token: str, evento_id: int, estado: str) -> None:
        r = await self._cliente.post(
            f"/eventos/{evento_id}/estado", json={"estado": estado}, headers=_auth(token)
        )
        r.raise_for_status()

    async def registro_corredor(
        self, email: str, password: str, nombre: str, apellidos: str
    ) -> str:
        r = await self._cliente.post(
            "/auth/corredores/registro",
            json={"nombre": nombre, "apellidos": apellidos, "email": email, "password": password},
        )
        r.raise_for_status()
        return r.json()["access_token"]

    async def unirse(self, token_corredor: str, codigo_acceso: str) -> dict[str, Any]:
        r = await self._cliente.post(
            f"/eventos/codigo/{codigo_acceso}/unirse", headers=_auth(token_corredor)
        )
        r.raise_for_status()
        return r.json()

    async def enviar_posiciones(
        self, token_dispositivo: str, evento_id: int, puntos: list[dict[str, Any]]
    ) -> httpx.Response:
        return await self._cliente.post(
            f"/eventos/{evento_id}/posiciones", json=puntos, headers=_auth(token_dispositivo)
        )
