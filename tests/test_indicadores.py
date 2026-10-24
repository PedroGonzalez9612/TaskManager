"""Pruebas de los indicadores de jornada y cumplimiento (alcance, Sección 5.2; criterio 8 del MVP).

Primero los cálculos puros, con horas fijas; después el servicio completo, con el reloj de prueba
(empieza el 2026-10-10 a las 08:00 UTC, las 03:00 en Bogotá)."""
from datetime import datetime, timedelta, timezone

import pytest

from app.services.indicador_service import (
    CumplimientoDeActividades, TiemposDeJornada, cumplimiento_de_asignacion, tiempos_de_jornada,
)
from app.utils.errors import ValidationError

from tests.conftest import HOY


def hora(h, m=0):
    return datetime(2026, 10, 10, h, m, tzinfo=timezone.utc)


def ejecucion(inicio, fin, pausas=(), estado="FINALIZADA"):
    return {"fecha_inicio": inicio, "fecha_fin": fin, "estado": estado,
            "pausas": [{"inicio": a, "fin": b} for a, b in pausas]}


JORNADA = (hora(0), hora(23, 59))
TURNO = (hora(8), hora(16))


# ---------- Tiempos de una jornada ----------

def test_lo_trabajado_fuera_del_turno_es_tiempo_adicional():
    # De 15:00 a 17:30: 60 minutos dentro del turno y 90 después de su fin.
    tiempos = tiempos_de_jornada(480, JORNADA, TURNO, None, [ejecucion(hora(15), hora(17, 30))], hora(20))
    assert tiempos.actividades_min == 150
    assert tiempos.adicional_min == 90


def test_las_pausas_no_cuentan_como_tiempo_en_actividades():
    trabajo = ejecucion(hora(9), hora(11), pausas=[(hora(9, 30), hora(10))])
    assert tiempos_de_jornada(480, JORNADA, TURNO, None, [trabajo], hora(20)).actividades_min == 90


def test_el_aprovechamiento_solo_usa_la_asistencia_revisada():
    trabajo = [ejecucion(hora(9), hora(10, 30))]
    validada = {"entrada": hora(8), "salida": hora(10), "estado": "VALIDADA"}
    sin_revisar = {"entrada": hora(8), "salida": hora(10), "estado": "REGISTRADA"}

    con_validada = tiempos_de_jornada(480, JORNADA, TURNO, validada, trabajo, hora(20)).presentar()
    assert con_validada["presente_min"] == 120
    assert con_validada["aprovechamiento"] == 75            # 90 de 120 minutos presentes.
    assert con_validada["cumplimiento_jornada"] == 19       # 90 de 480 programados.

    sin_validar = tiempos_de_jornada(480, JORNADA, TURNO, sin_revisar, trabajo, hora(20)).presentar()
    assert sin_validar["presente_min"] == 0
    assert sin_validar["aprovechamiento"] is None
    assert sin_validar["jornadas_sin_validar"] == 1


def test_los_agregados_suman_tiempos_y_no_promedian_porcentajes():
    # Una jornada de 60 de 120 minutos (50 %) y otra de 420 de 480 (88 %). El promedio de los
    # porcentajes daría 69 %; sumando tiempos, 480 de 600 minutos, es 80 %.
    corta = TiemposDeJornada(jornadas=1, programado_min=120, actividades_min=60)
    larga = TiemposDeJornada(jornadas=1, programado_min=480, actividades_min=420)
    total = TiemposDeJornada()
    total.sumar(corta)
    total.sumar(larga)
    assert total.presentar()["cumplimiento_jornada"] == 80     # 480 de 600; el promedio daría 69.


# ---------- Cumplimiento de una asignación ----------

CIERRE = hora(23, 59)


def test_finalizada_en_su_jornada_es_cumplida_y_mide_la_estimacion():
    actividad = {"estado": "COMPLETADA", "tiempo_estimado_min": 60}
    resultado = cumplimiento_de_asignacion(actividad, ejecucion(hora(9), hora(9, 45)), CIERRE, hora(20)).presentar()
    assert (resultado["cumplidas"], resultado["con_retraso"]) == (1, 0)
    assert (resultado["real_min"], resultado["estimado_min"], resultado["real_sobre_estimado"]) == (45, 60, 75)


def test_finalizada_despues_de_su_jornada_es_con_retraso():
    actividad = {"estado": "COMPLETADA", "tiempo_estimado_min": 60}
    tarde = ejecucion(hora(23), hora(23, 59) + timedelta(minutes=30))
    assert cumplimiento_de_asignacion(actividad, tarde, CIERRE, hora(23, 59) + timedelta(hours=2)).con_retraso == 1


def test_no_realizada_es_incumplida_y_reprogramada_es_con_retraso():
    assert cumplimiento_de_asignacion({"estado": "NO_REALIZADA"}, None, CIERRE, hora(20)).incumplidas == 1
    reprogramada = {"estado": "ASIGNADA", "reprogramaciones": [{"jornada_origen": HOY}]}
    assert cumplimiento_de_asignacion(reprogramada, None, CIERRE, hora(20)).con_retraso == 1


def test_lo_de_una_jornada_que_no_ha_terminado_todavia_no_cuenta():
    resultado = cumplimiento_de_asignacion({"estado": "ASIGNADA"}, None, CIERRE, hora(20)).presentar()
    assert resultado["pendientes"] == 1
    assert resultado["cumplimiento_actividades"] is None


def test_el_cumplimiento_de_actividades_cuenta_las_evaluadas():
    total = CumplimientoDeActividades(cumplidas=3, incumplidas=1, con_retraso=1, pendientes=5)
    assert total.presentar()["cumplimiento_actividades"] == 60     # 3 de 5; las pendientes no cuentan.


# ---------- El servicio completo ----------

def turno(servicios, empresa, operario, inicio, fin):
    creado = servicios.turnos.crear_turno(
        {"nombre": f"De {inicio} a {fin}", "hora_inicio": inicio, "hora_fin": fin, "descanso_min": 0}, empresa.admin)
    servicios.turnos.asignar_turno(empresa.admin, operario["id"], creado["id"], desde=HOY)


def jornada_de_ana(servicios, empresa, crear_actividad, reloj, validar=True):
    """Ana tiene turno de 02:00 a 10:00 (480 min). Entra a las 03:00, hace una actividad de 60 min
    estimados en 45 y sale a las 04:00."""
    turno(servicios, empresa, empresa.ana, "02:00", "10:00")
    servicios.asistencia.marcar_entrada(empresa.ana)
    actividad = crear_actividad([empresa.ana])
    servicios.ejecucion.iniciar(actividad["id"], empresa.ana)
    reloj.avanzar(45)
    servicios.ejecucion.finalizar(actividad["id"], empresa.ana)
    reloj.avanzar(15)
    asistencia = servicios.asistencia.marcar_salida(empresa.ana)
    if validar:
        servicios.asistencia.validar(empresa.admin, asistencia["id"])
    return actividad


def de(resultado, operario):
    return next(o for o in resultado["operarios"] if o["id"] == operario["id"])


def test_indicadores_de_un_operario_en_su_jornada(servicios, empresa, crear_actividad, reloj):
    jornada_de_ana(servicios, empresa, crear_actividad, reloj)
    ana = de(servicios.indicadores.consultar(HOY, HOY, empresa.admin), empresa.ana)

    assert ana["jornada"]["programado_min"] == 480
    assert ana["jornada"]["actividades_min"] == 45
    assert ana["jornada"]["presente_min"] == 60
    assert ana["jornada"]["cumplimiento_jornada"] == 9           # 45 de 480.
    assert ana["jornada"]["aprovechamiento"] == 75               # 45 de 60.
    assert ana["actividades"]["cumplidas"] == 1
    assert ana["actividades"]["real_sobre_estimado"] == 75       # 45 reales de 60 estimados.


def test_la_jornada_de_hoy_no_cuenta_hasta_marcar_la_salida(servicios, empresa, crear_actividad):
    turno(servicios, empresa, empresa.ana, "02:00", "10:00")
    servicios.asistencia.marcar_entrada(empresa.ana)
    crear_actividad([empresa.ana])
    ana = de(servicios.indicadores.consultar(HOY, HOY, empresa.admin), empresa.ana)
    assert ana["jornada"]["jornadas"] == 0
    assert ana["actividades"]["pendientes"] == 1


def test_la_empresa_suma_a_sus_operarios(servicios, empresa, crear_actividad, reloj):
    jornada_de_ana(servicios, empresa, crear_actividad, reloj)
    empresa_ = servicios.indicadores.consultar(HOY, HOY, empresa.admin)["empresa"]
    # Luis no trabajó ese día: sin asistencia ni actividades, no suma una jornada.
    assert empresa_["jornada"]["jornadas"] == 1
    assert empresa_["actividades"]["cumplidas"] == 1


def test_canceladas_y_devoluciones_se_agrupan_por_motivo(servicios, empresa, crear_actividad):
    devuelta = crear_actividad([empresa.luis], titulo="Devuelta")
    servicios.ejecucion.devolver(devuelta["id"], empresa.luis, "Falta información")
    cancelada = crear_actividad([empresa.ana], titulo="Cancelada")
    servicios.actividades.cancelar(cancelada["id"], empresa.admin, "Otro", "Duplicada")

    pendientes = servicios.indicadores.consultar(HOY, HOY, empresa.admin)["empresa"]["pendientes"]
    assert pendientes["devoluciones_por_motivo"] == [{"motivo": "Falta información", "cantidad": 1}]
    assert pendientes["canceladas_por_motivo"] == [{"motivo": "Duplicada", "cantidad": 1}]


def test_el_operario_solo_ve_sus_indicadores(servicios, empresa, crear_actividad, reloj):
    jornada_de_ana(servicios, empresa, crear_actividad, reloj)
    propios = servicios.indicadores.consultar(HOY, HOY, empresa.luis)
    assert [o["id"] for o in propios["operarios"]] == [empresa.luis["id"]]


def test_las_fechas_se_validan(servicios, empresa):
    with pytest.raises(ValidationError):
        servicios.indicadores.consultar("2026-10-10", "2026-10-01", empresa.admin)
    with pytest.raises(ValidationError):
        servicios.indicadores.consultar("2026-01-01", "2026-12-31", empresa.admin)


def test_la_ruta_de_indicadores(cliente_de, empresa):
    respuesta = cliente_de(empresa.admin).get(f"/analisis/indicadores?desde={HOY}&hasta={HOY}")
    assert respuesta.status_code == 200
    assert "empresa" in respuesta.get_json()
