"""Pruebas de las reglas que unen la asistencia con la ejecución (alcance, Sección 5.1): para iniciar
o reanudar una actividad hay que tener la entrada marcada, y no se marca la salida con una
actividad en curso. Aquí nadie ha marcado entrada al empezar: cada prueba la marca cuando toca."""
import pytest

from app.services.asistencia_service import SALIDA_CON_ACTIVIDAD_EN_CURSO, SIN_ENTRADA, YA_MARCO_SALIDA
from app.utils.errors import ValidationError

UN_DIA = 24 * 60


# ---------- Iniciar y reanudar exigen la entrada ----------

def test_no_se_inicia_una_actividad_sin_marcar_la_entrada(servicios, empresa, crear_actividad):
    actividad = crear_actividad([empresa.ana])

    with pytest.raises(ValidationError, match=SIN_ENTRADA):
        servicios.ejecucion.iniciar(actividad["id"], empresa.ana)

    assert servicios.actividades.obtener_actividad(actividad["id"], empresa.ana)["estado"] == "ASIGNADA"


def test_con_la_entrada_marcada_se_inicia(servicios, empresa, crear_actividad):
    actividad = crear_actividad([empresa.ana])
    servicios.asistencia.marcar_entrada(empresa.ana)

    assert servicios.ejecucion.iniciar(actividad["id"], empresa.ana)["estado"] == "EN_EJECUCION"


def test_la_entrada_de_un_operario_no_le_sirve_a_otro(servicios, empresa, crear_actividad):
    actividad = crear_actividad([empresa.ana, empresa.luis])
    servicios.asistencia.marcar_entrada(empresa.ana)

    with pytest.raises(ValidationError, match=SIN_ENTRADA):
        servicios.ejecucion.iniciar(actividad["id"], empresa.luis)


def test_despues_de_la_salida_no_se_inicia_otra(servicios, empresa, crear_actividad, reloj):
    actividad = crear_actividad([empresa.ana])
    servicios.asistencia.marcar_entrada(empresa.ana)
    reloj.avanzar(60)
    servicios.asistencia.marcar_salida(empresa.ana)

    with pytest.raises(ValidationError, match=YA_MARCO_SALIDA):
        servicios.ejecucion.iniciar(actividad["id"], empresa.ana)


def test_despues_de_la_salida_no_se_reanuda_una_pausada(servicios, empresa, crear_actividad, reloj):
    actividad = crear_actividad([empresa.ana])
    servicios.asistencia.marcar_entrada(empresa.ana)
    servicios.ejecucion.iniciar(actividad["id"], empresa.ana)
    reloj.avanzar(30)
    servicios.ejecucion.pausar(actividad["id"], empresa.ana, "Fin de jornada")
    servicios.asistencia.marcar_salida(empresa.ana)

    with pytest.raises(ValidationError, match=YA_MARCO_SALIDA):
        servicios.ejecucion.reanudar(actividad["id"], empresa.ana)

    assert servicios.actividades.obtener_actividad(actividad["id"], empresa.ana)["estado"] == "PAUSADA"


def test_el_turno_no_limita_la_entrada(servicios, empresa, crear_actividad, reloj):
    """El turno de Ana va de 06:00 a 14:00 de Bogotá y la prueba corre a las 03:00: puede marcar
    la entrada antes de la hora de inicio y empezar a trabajar."""
    turno = servicios.turnos.crear_turno(
        {"nombre": "Mañana", "hora_inicio": "06:00", "hora_fin": "14:00", "descanso_min": 60}, empresa.admin)
    servicios.turnos.asignar_turno(empresa.admin, empresa.ana["id"], turno["id"], "2026-10-10")
    actividad = crear_actividad([empresa.ana])

    servicios.asistencia.marcar_entrada(empresa.ana)

    assert servicios.ejecucion.iniciar(actividad["id"], empresa.ana)["estado"] == "EN_EJECUCION"


# ---------- La salida exige no tener nada en curso ----------

def test_no_se_marca_la_salida_con_una_actividad_en_curso(servicios, empresa, crear_actividad, reloj):
    actividad = crear_actividad([empresa.ana])
    servicios.asistencia.marcar_entrada(empresa.ana)
    servicios.ejecucion.iniciar(actividad["id"], empresa.ana)
    reloj.avanzar(30)

    with pytest.raises(ValidationError, match=SALIDA_CON_ACTIVIDAD_EN_CURSO):
        servicios.asistencia.marcar_salida(empresa.ana)

    assert servicios.asistencia.consultar_hoy(empresa.ana)["salida"] is None


def test_con_la_actividad_pausada_si_se_marca_la_salida(servicios, empresa, crear_actividad, reloj):
    actividad = crear_actividad([empresa.ana])
    servicios.asistencia.marcar_entrada(empresa.ana)
    servicios.ejecucion.iniciar(actividad["id"], empresa.ana)
    reloj.avanzar(30)
    servicios.ejecucion.pausar(actividad["id"], empresa.ana, "Fin de jornada")

    assert servicios.asistencia.marcar_salida(empresa.ana)["salida"] is not None


def test_con_la_actividad_finalizada_si_se_marca_la_salida(servicios, empresa, crear_actividad, reloj):
    actividad = crear_actividad([empresa.ana], hora_programada="03:00")    # De hora fija: no se pausa.
    servicios.asistencia.marcar_entrada(empresa.ana)
    servicios.ejecucion.iniciar(actividad["id"], empresa.ana)
    reloj.avanzar(30)
    with pytest.raises(ValidationError, match=SALIDA_CON_ACTIVIDAD_EN_CURSO):
        servicios.asistencia.marcar_salida(empresa.ana)

    servicios.ejecucion.finalizar(actividad["id"], empresa.ana)

    assert servicios.asistencia.marcar_salida(empresa.ana)["salida"] is not None


def test_lo_que_tiene_en_curso_un_companero_no_impide_la_salida(servicios, empresa, crear_actividad, reloj):
    actividad = crear_actividad([empresa.ana, empresa.luis])
    for operario in (empresa.ana, empresa.luis):
        servicios.asistencia.marcar_entrada(operario)
    servicios.ejecucion.iniciar(actividad["id"], empresa.luis)
    reloj.avanzar(30)

    assert servicios.asistencia.marcar_salida(empresa.ana)["salida"] is not None


# ---------- Por la API ----------

def test_la_api_explica_que_falta_la_entrada(cliente_de, empresa, crear_actividad):
    actividad = crear_actividad([empresa.ana])
    ana = cliente_de(empresa.ana)

    sin_entrada = ana.post(f"/actividades/{actividad['id']}/iniciar")
    assert sin_entrada.status_code == 400
    assert sin_entrada.get_json()["error"] == SIN_ENTRADA

    assert ana.post("/asistencia/entrada").status_code == 201
    assert ana.post(f"/actividades/{actividad['id']}/iniciar").status_code == 200

    con_algo_en_curso = ana.post("/asistencia/salida")
    assert con_algo_en_curso.status_code == 400
    assert con_algo_en_curso.get_json()["error"] == SALIDA_CON_ACTIVIDAD_EN_CURSO
