import threading
import time


class LimitadorIntentos:
    """Límite de intentos fallidos de login (Anexo B §7): 5 fallos / 15 min → bloqueo 15 min."""

    def __init__(
        self, max_intentos: int = 5, ventana_seg: int = 900, bloqueo_seg: int = 900
    ) -> None:
        self._max_intentos = max_intentos
        self._ventana_seg = ventana_seg
        self._bloqueo_seg = bloqueo_seg
        self._lock = threading.Lock()
        self._fallos: dict[str, list[float]] = {}
        self._bloqueados_hasta: dict[str, float] = {}

    def bloqueado(self, clave: str) -> bool:
        with self._lock:
            hasta = self._bloqueados_hasta.get(clave)
            if hasta is None:
                return False
            if time.monotonic() >= hasta:
                del self._bloqueados_hasta[clave]
                self._fallos.pop(clave, None)
                return False
            return True

    def registrar_fallo(self, clave: str) -> None:
        with self._lock:
            ahora = time.monotonic()
            intentos = [t for t in self._fallos.get(clave, []) if ahora - t < self._ventana_seg]
            intentos.append(ahora)
            self._fallos[clave] = intentos
            if len(intentos) >= self._max_intentos:
                self._bloqueados_hasta[clave] = ahora + self._bloqueo_seg
                self._fallos.pop(clave, None)

    def registrar_exito(self, clave: str) -> None:
        with self._lock:
            self._fallos.pop(clave, None)


limitador_login = LimitadorIntentos()


class LimitadorFrecuencia:
    """Frecuencia mínima entre peticiones por clave (Anexo B §7: ingesta, 1 / 5 s por token)."""

    def __init__(self, intervalo_seg: float) -> None:
        self._intervalo_seg = intervalo_seg
        self._lock = threading.Lock()
        self._ultima: dict[str, float] = {}

    def permitir(self, clave: str) -> bool:
        with self._lock:
            ahora = time.monotonic()
            anterior = self._ultima.get(clave)
            if anterior is not None and (ahora - anterior) < self._intervalo_seg:
                return False
            self._ultima[clave] = ahora
            return True


limitador_ingesta = LimitadorFrecuencia(intervalo_seg=5.0)
