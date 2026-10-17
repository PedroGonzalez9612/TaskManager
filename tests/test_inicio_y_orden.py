"""Pruebas de lo que la programación del día le dice al Operario al llegar y mientras ordena su día
(alcance, Sección 5.1): la llegada tarde, el tiempo que queda fuera del turno y la vista previa del
orden. El reloj empieza el 2026-10-10 a las 08:00 UTC: las 03:00 en Bogotá."""
import pytest

from app.services.programacion_service import TOLERANCIA_ENTRADA_MIN
from app.utils.errors import ProhibidoError, ValidationError

from tests.conftest import HOY

PROPIA = {"X-Requested-With": "GestLab"}


def turno(servicios, empresa, operario, inicio, fin):
    creado = servicios.turnos.crear_turno(
        {"nombre": f"De {inicio} a {fin}", "hora_inicio": inicio, "hora_fin": fin, "descanso_min": 0}, empresa.admin)
    servicios.turnos.asignar_turno(empresa.admin, operario["id"], creado["id"], desde=HOY)
    return creado


def programacion(servicios, operario):
    return servicios.programacion.consultar(operario)


# ---------- Llegada tarde ----------

def test_sin_entrada_despues_de_la_tolerancia_es_llegada_tarde(servicios, empresa):
    turno(servicios, empresa, empresa.ana, "02:00", "10:00")     # Empezó hace 60 minutos.
    datos = programacion(servicios, empresa.ana)
    assert datos["retraso_entrada_min"] == 60
    assert datos["tolerancia_entrada_min"] == TOLERANCIA_ENTRADA_MIN


def test_dentro_de_la_tolerancia_no_es_llegada_tarde(servicios, empresa, reloj):
    turno(servicios, empresa, empresa.ana, "02:55", "10:00")     # Empezó hace 5 minutos.
    assert programacion(servicios, empresa.ana)["retraso_entrada_min"] == 0
    reloj.avanzar(TOLERANCIA_ENTRADA_MIN)                        # 15 minutos: ya pasó la tolerancia.
    assert programacion(servicios, empresa.ana)["retraso_entrada_min"] == 15


def test_con_la_entrada_marcada_no_hay_retraso(servicios, empresa):
    turno(servicios, empresa, empresa.ana, "02:00", "10:00")
    servicios.asistencia.marcar_entrada(empresa.ana)
    assert programacion(servicios, empresa.ana)["retraso_entrada_min"] == 0


def test_sin_turno_o_antes_del_turno_no_hay_retraso(servicios, empresa):
    assert programacion(servicios, empresa.ana)["retraso_entrada_min"] == 0
    turno(servicios, empresa, empresa.luis, "06:00", "14:00")    # Empieza dentro de tres horas.
    assert programacion(servicios, empresa.luis)["retraso_entrada_min"] == 0


# ---------- Tiempo fuera del turno ----------

def test_lo_que_pasa_del_fin_del_turno_dice_cuanto_tiempo_implica(servicios, empresa, crear_actividad):
    turno(servicios, empresa, empresa.ana, "02:00", "04:00")     # Termina en una hora.
    servicios.asistencia.marcar_entrada(empresa.ana)
    for prioridad in ("ALTA", "MEDIA", "BAJA"):
        crear_actividad([empresa.ana], titulo=prioridad, prioridad=prioridad)    # 60 minutos cada una.

    datos = programacion(servicios, empresa.ana)
    assert [tramo["fuera_del_turno_min"] for tramo in datos["tramos"]] == [0, 60, 60]
    assert datos["resumen"]["fuera_del_turno_min"] == 120


def test_una_actividad_que_cruza_el_fin_del_turno_cuenta_solo_lo_que_pasa(servicios, empresa, crear_actividad):
    turno(servicios, empresa, empresa.ana, "02:00", "03:30")     # Termina en media hora.
    servicios.asistencia.marcar_entrada(empresa.ana)
    crear_actividad([empresa.ana])                               # De 03:00 a 04:00.
    assert programacion(servicios, empresa.ana)["tramos"][0]["fuera_del_turno_min"] == 30


def test_sin_turno_nada_queda_fuera_del_turno(servicios, empresa, crear_actividad):
    crear_actividad([empresa.ana])
    datos = programacion(servicios, empresa.ana)
    assert datos["tramos"][0]["fuera_del_turno_min"] == 0
    assert datos["resumen"]["fuera_del_turno_min"] == 0


# ---------- Vista previa del orden ----------

@pytest.fixture
def tres(empresa, crear_actividad):
    return [crear_actividad([empresa.ana], titulo=p, prioridad=p) for p in ("ALTA", "MEDIA", "BAJA")]


def test_la_vista_previa_muestra_las_horas_con_el_orden_nuevo_sin_guardarlo(servicios, empresa, tres):
    alta, media, baja = tres
    previa = servicios.programacion.vista_previa_orden(empresa.ana, [baja["id"], alta["id"], media["id"]])
    assert [tramo["actividad_id"] for tramo in previa["tramos"]] == [baja["id"], alta["id"], media["id"]]

    guardada = programacion(servicios, empresa.ana)
    assert [tramo["actividad_id"] for tramo in guardada["tramos"]] == [alta["id"], media["id"], baja["id"]]
    assert guardada["orden_personalizado"] is False


def test_la_vista_previa_tiene_las_mismas_reglas_que_guardar(servicios, empresa, crear_actividad, tres):
    fija = crear_actividad([empresa.ana], titulo="Fija", hora_programada="06:00")
    with pytest.raises(ValidationError, match="horario flexible"):
        servicios.programacion.vista_previa_orden(empresa.ana, [fija["id"], tres[0]["id"]])
    with pytest.raises(ProhibidoError):
        servicios.programacion.vista_previa_orden(empresa.admin, [tres[0]["id"]])


def test_vista_previa_por_la_api(cliente_de, empresa, tres):
    ids = [tres[2]["id"], tres[1]["id"], tres[0]["id"]]
    respuesta = cliente_de(empresa.ana).post("/orden-del-dia/vista-previa", json={"actividad_ids": ids}, headers=PROPIA)
    assert respuesta.status_code == 200
    assert [tramo["actividad_id"] for tramo in respuesta.get_json()["tramos"]] == ids
    assert cliente_de(empresa.admin).post("/orden-del-dia/vista-previa", json={"actividad_ids": ids},
                                          headers=PROPIA).status_code == 403
