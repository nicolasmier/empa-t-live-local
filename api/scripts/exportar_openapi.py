"""Regenera openapi.json a partir del código: `python -m scripts.exportar_openapi`.

Entregable de coordinación para los agentes Web y Android (plan S2): ejecutar
tras cualquier cambio de contrato en los routers.
"""

import json
from pathlib import Path

from app.main import app


def run() -> None:
    destino = Path(__file__).resolve().parent.parent / "openapi.json"
    with destino.open("w", encoding="utf-8") as f:
        json.dump(app.openapi(), f, indent=2, ensure_ascii=False)
    print(f"{destino} generado")


if __name__ == "__main__":
    run()
