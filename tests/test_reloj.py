"""Pruebas del reloj: qué día es para una empresa y cuándo termina su jornada."""
from datetime import datetime, timezone

import pytest

from app.utils.errors import ValidationError
from app.utils.reloj import ZONA_POR_DEFECTO, fecha_local, fin_del_dia, validar_zona


def test_de_noche_en_bogota_todavia_es_el_mismo_dia():
    # Las 02:00 UTC del día 11 son las 21:00 del día 10 en Bogotá.
    momento = datetime(2026, 10, 11, 2, 0, tzinfo=timezone.utc)
    assert fecha_local(momento, "America/Bogota") == "2026-10-10"
    assert fecha_local(momento, "Europe/Madrid") == "2026-10-11"


def test_sin_zona_se_usa_la_de_bogota():
    assert ZONA_POR_DEFECTO == "America/Bogota"
    assert fecha_local(datetime(2026, 10, 11, 2, 0, tzinfo=timezone.utc)) == "2026-10-10"


def test_una_fecha_sin_zona_se_toma_como_utc():
    assert fecha_local(datetime(2026, 10, 11, 2, 0), "America/Bogota") == "2026-10-10"


def test_el_dia_termina_a_la_medianoche_de_la_empresa():
    # La medianoche de Bogotá (UTC-5) son las 05:00 UTC.
    assert fin_del_dia("2026-10-10", "America/Bogota") == datetime(2026, 10, 11, 5, 0, tzinfo=timezone.utc)
    assert fin_del_dia("2026-12-31", "America/Bogota") == datetime(2027, 1, 1, 5, 0, tzinfo=timezone.utc)


def test_validar_zona_acepta_las_que_existen():
    assert validar_zona(" America/Mexico_City ") == "America/Mexico_City"


@pytest.mark.parametrize("zona", ["", None, "Bogota", "America/Macondo"])
def test_validar_zona_rechaza_las_que_no_existen(zona):
    with pytest.raises(ValidationError):
        validar_zona(zona)
