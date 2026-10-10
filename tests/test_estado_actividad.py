"""Pruebas de la regla del estado de una actividad (funciones puras, sin base de datos)."""
import pytest

from app.models.enums import EstadoActividad
from app.services.estado_actividad import calcular_estado_actividad, estado_para_operario


@pytest.mark.parametrize("ejecuciones, esperado", [
    ([], "PENDIENTE"),                              # Sin asignaciones activas.
    ([None, None], "ASIGNADA"),                     # Nadie ha iniciado.
    (["EN_PROGRESO", None], "EN_EJECUCION"),
    (["EN_PROGRESO", "PAUSADA"], "EN_EJECUCION"),
    (["PAUSADA", None], "PAUSADA"),
    (["PAUSADA", "FINALIZADA"], "PAUSADA"),
    (["FINALIZADA", None], "ASIGNADA"),             # Uno terminó y el otro no ha iniciado.
    (["FINALIZADA", "FINALIZADA"], "COMPLETADA"),
])
def test_estado_segun_las_ejecuciones(ejecuciones, esperado):
    assert calcular_estado_actividad("ASIGNADA", ejecuciones) == EstadoActividad(esperado)


@pytest.mark.parametrize("estado", ["COMPLETADA", "NO_REALIZADA", "CANCELADA"])
def test_un_estado_final_no_se_recalcula(estado):
    assert calcular_estado_actividad(estado, ["EN_PROGRESO"]) == EstadoActividad(estado)
    assert calcular_estado_actividad(estado, []) == EstadoActividad(estado)
    assert calcular_estado_actividad(estado, [], por_devolucion=True) == EstadoActividad(estado)


def test_queda_devuelta_cuando_el_ultimo_operario_la_devuelve():
    assert calcular_estado_actividad("ASIGNADA", [], por_devolucion=True) == EstadoActividad.DEVUELTA
    # Si todavía queda alguien asignado, la devolución no cambia la regla normal.
    assert calcular_estado_actividad("ASIGNADA", [None], por_devolucion=True) == EstadoActividad.ASIGNADA
    assert calcular_estado_actividad("EN_EJECUCION", ["EN_PROGRESO"], por_devolucion=True)         == EstadoActividad.EN_EJECUCION


def test_una_devuelta_sigue_devuelta_hasta_que_se_le_asigna_alguien():
    assert calcular_estado_actividad("DEVUELTA", []) == EstadoActividad.DEVUELTA
    assert calcular_estado_actividad("DEVUELTA", [None]) == EstadoActividad.ASIGNADA


@pytest.mark.parametrize("general, ejecucion, esperado", [
    ("EN_EJECUCION", None, "ASIGNADA"),             # El compañero la tiene en curso; él no ha iniciado.
    ("EN_EJECUCION", "EN_PROGRESO", "EN_EJECUCION"),
    ("EN_EJECUCION", "PAUSADA", "PAUSADA"),
    ("ASIGNADA", "FINALIZADA", "COMPLETADA"),       # Él ya terminó aunque la actividad siga abierta.
    ("COMPLETADA", "FINALIZADA", "COMPLETADA"),
    ("CANCELADA", "CERRADA", "CANCELADA"),
    ("NO_REALIZADA", None, "NO_REALIZADA"),
    ("DEVUELTA", None, "DEVUELTA"),
])
def test_estado_que_ve_cada_operario(general, ejecucion, esperado):
    assert estado_para_operario(general, ejecucion) == EstadoActividad(esperado)
