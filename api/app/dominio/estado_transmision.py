"""Estado de transmisión calculado a partir de timestamps (spec v10 §6, RF-011).

`estado_transmision` NO se guarda en BD (corrección v9, Anexo A): se deriva siempre
del timestamp de la última posición conocida frente a `umbral_sin_senal_seg`.
"""

from datetime import UTC, datetime, timedelta

TRANSMITIENDO = "transmitiendo"
SIN_SENAL = "sin_senal"


def calcular_estado_transmision(
    timestamp_dispositivo: datetime | None, umbral_sin_senal_seg: int
) -> str:
    if timestamp_dispositivo is None:
        return SIN_SENAL
    ts = timestamp_dispositivo
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=UTC)
    ahora = datetime.now(UTC)
    if (ahora - ts) > timedelta(seconds=umbral_sin_senal_seg):
        return SIN_SENAL
    return TRANSMITIENDO
