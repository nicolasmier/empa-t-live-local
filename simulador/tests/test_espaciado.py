from simulador.espaciado import generar_offsets_km


def test_sin_espaciado_todos_arrancan_en_cero() -> None:
    offsets = generar_offsets_km(10, 0.0, 0.0)
    assert offsets == [0.0] * 10


def test_primer_corredor_siempre_arranca_en_cero() -> None:
    offsets = generar_offsets_km(5, 2.0, 100.0)
    assert offsets[0] == 0.0


def test_offsets_son_crecientes_y_dentro_del_rango_acumulado() -> None:
    n = 10
    offsets = generar_offsets_km(n, 2.0, 100.0)
    assert len(offsets) == n
    for anterior, siguiente in zip(offsets, offsets[1:]):
        gap_m = (siguiente - anterior) * 1000
        assert 2.0 <= gap_m <= 100.0


def test_un_solo_corredor_no_necesita_espaciado() -> None:
    assert generar_offsets_km(1, 2.0, 100.0) == [0.0]
