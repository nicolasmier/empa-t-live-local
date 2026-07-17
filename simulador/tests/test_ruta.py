from pathlib import Path

import pytest

from simulador.ruta import cargar_ruta

_GPX_EJEMPLO = (
    Path(__file__).resolve().parent.parent / "rutas_ejemplo" / "5k_ejemplo.gpx"
)


def test_cargar_ruta_calcula_distancia_total_positiva() -> None:
    ruta = cargar_ruta(str(_GPX_EJEMPLO))
    assert ruta.distancia_total_km > 0
    assert len(ruta.puntos) == len(ruta.distancias_acumuladas_km)


def test_punto_en_distancia_cero_es_el_primer_punto() -> None:
    ruta = cargar_ruta(str(_GPX_EJEMPLO))
    lat, lon = ruta.punto_en_distancia(0.0)
    assert (lat, lon) == ruta.puntos[0]


def test_punto_en_distancia_total_es_el_ultimo_punto() -> None:
    ruta = cargar_ruta(str(_GPX_EJEMPLO))
    lat, lon = ruta.punto_en_distancia(ruta.distancia_total_km)
    assert (lat, lon) == pytest.approx(ruta.puntos[-1])


def test_punto_en_distancia_intermedia_esta_entre_dos_puntos_del_gpx() -> None:
    ruta = cargar_ruta(str(_GPX_EJEMPLO))
    mitad = ruta.distancia_total_km / 2
    lat, lon = ruta.punto_en_distancia(mitad)
    lats = [p[0] for p in ruta.puntos]
    lons = [p[1] for p in ruta.puntos]
    assert min(lats) <= lat <= max(lats)
    assert min(lons) <= lon <= max(lons)


def test_punto_mas_alla_del_final_se_recorta_al_ultimo_punto() -> None:
    ruta = cargar_ruta(str(_GPX_EJEMPLO))
    lat, lon = ruta.punto_en_distancia(ruta.distancia_total_km + 100)
    assert (lat, lon) == pytest.approx(ruta.puntos[-1])
