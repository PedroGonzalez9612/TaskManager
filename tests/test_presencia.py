"""Pruebas de la presencia de una persona en su jornada (alcance, Sección 5.1): un caso por estado."""
from datetime import datetime, timedelta, timezone

import pytest

from app.models.asistencia import Asistencia
from app.models.enums import EstadoPresencia
from app.models.presencia import TOLERANCIA_ENTRADA_MIN, presencia_en_jornada

INICIO = datetime(2026, 10, 10, 19, 0, tzinfo=timezone.utc)     # Turno de 14:00 a 22:00 en Bogotá.
FIN = INICIO + timedelta(hours=8)
TURNO = (INICIO, FIN)


def a_las(minutos_desde_el_inicio):
    return INICIO + timedelta(minutes=minutos_desde_el_inicio)


def asistencia(entrada, salida=None):
    return Asistencia("ana", "empresa", "2026-10-10", entrada, salida)


def estado(turno, registro, ahora, vigente=True):
    resultado = presencia_en_jornada(turno, registro, ahora, es_jornada_vigente=vigente)
    return resultado["estado"], resultado["minutos"]


def test_sin_turno_y_sin_entrada():
    assert estado(None, None, a_las(0)) == (EstadoPresencia.SIN_TURNO, 0)


@pytest.mark.parametrize("ahora", [a_las(-60), a_las(0), a_las(TOLERANCIA_ENTRADA_MIN)])
def test_por_llegar_hasta_que_pasa_la_tolerancia(ahora):
    assert estado(TURNO, None, ahora) == (EstadoPresencia.POR_LLEGAR, 0)


def test_llegada_tarde_con_los_minutos_que_lleva():
    assert estado(TURNO, None, a_las(25)) == (EstadoPresencia.LLEGADA_TARDE, 25)


def test_no_vino_cuando_su_turno_termina_sin_entrada():
    assert estado(TURNO, None, a_las(8 * 60)) == (EstadoPresencia.NO_VINO, 0)


def test_no_vino_en_una_jornada_que_ya_paso():
    assert estado(TURNO, None, a_las(60), vigente=False) == (EstadoPresencia.NO_VINO, 0)


def test_en_turno_con_la_entrada_marcada_aunque_llegue_antes_o_tarde():
    assert estado(TURNO, asistencia(a_las(-15)), a_las(30)) == (EstadoPresencia.EN_TURNO, 0)
    assert estado(TURNO, asistencia(a_las(40)), a_las(60)) == (EstadoPresencia.EN_TURNO, 0)


def test_en_turno_sin_turno_si_marco_la_entrada():
    assert estado(None, asistencia(a_las(0)), a_las(30)) == (EstadoPresencia.EN_TURNO, 0)


def test_tiempo_adicional_despues_del_fin_del_turno():
    assert estado(TURNO, asistencia(a_las(0)), a_las(8 * 60 + 40)) == (EstadoPresencia.TIEMPO_ADICIONAL, 40)


def test_jornada_terminada_con_la_salida_anticipada():
    assert estado(TURNO, asistencia(a_las(0), a_las(7 * 60 + 10)), a_las(9 * 60)) == (EstadoPresencia.JORNADA_TERMINADA, 50)
    assert estado(TURNO, asistencia(a_las(0), a_las(8 * 60 + 5)), a_las(9 * 60)) == (EstadoPresencia.JORNADA_TERMINADA, 0)


def test_sin_salida_en_una_jornada_anterior_abierta():
    assert estado(TURNO, asistencia(a_las(0)), a_las(30 * 60), vigente=False) == (EstadoPresencia.SIN_SALIDA, 0)
