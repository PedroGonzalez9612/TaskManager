"""Pruebas de la programación de varios días, para la vista Semana (observaciones 8 y 11 del
usuario). El reloj empieza el 2026-10-10 a las 08:00 UTC: las 03:00 en Bogotá."""
import pytest

from app.utils.errors import ValidationError
from app.utils.reloj import momento_local

from tests.conftest import HOY

MANANA = "2026-10-11"
ZONA = "America/Bogota"


def turno(servicios, empresa, operario, inicio, fin):
    creado = servicios.turnos.crear_turno(
        {"nombre": f"De {inicio} a {fin}", "hora_inicio": inicio, "hora_fin": fin, "descanso_min": 0}, empresa.admin)
    servicios.turnos.asignar_turno(empresa.admin, operario["id"], creado["id"], desde=HOY)


def dia(semana, fecha):
    return next(d for d in semana["dias"] if d["fecha"] == fecha)


def test_un_dia_futuro_se_proyecta_desde_el_inicio_de_su_turno(servicios, empresa, crear_actividad):
    turno(servicios, empresa, empresa.ana, "06:00", "14:00")
    crear_actividad([empresa.ana], titulo="Primera", fecha_programada=MANANA, prioridad="ALTA")
    crear_actividad([empresa.ana], titulo="Segunda", fecha_programada=MANANA, prioridad="BAJA")

    manana = dia(servicios.programacion.semana(empresa.ana, HOY, MANANA), MANANA)
    inicios = [tramo["inicio"] for tramo in manana["tramos"]]
    assert inicios[0] == momento_local(MANANA, "06:00", ZONA)
    assert inicios[1] == momento_local(MANANA, "07:00", ZONA)      # La primera estima 60 minutos.
    assert all(tramo["aproximada"] for tramo in manana["tramos"])


def test_la_hora_fija_de_un_dia_futuro_no_se_mueve(servicios, empresa, crear_actividad):
    turno(servicios, empresa, empresa.ana, "06:00", "14:00")
    crear_actividad([empresa.ana], titulo="Fija", fecha_programada=MANANA, hora_programada="10:30")
    tramo = dia(servicios.programacion.semana(empresa.ana, HOY, MANANA), MANANA)["tramos"][0]
    assert tramo["inicio"] == momento_local(MANANA, "10:30", ZONA)
    assert tramo["hora_fija"]


def test_un_dia_pasado_solo_muestra_lo_finalizado(servicios, empresa, crear_actividad, reloj):
    turno(servicios, empresa, empresa.ana, "02:00", "10:00")
    servicios.asistencia.marcar_entrada(empresa.ana)
    hecha = crear_actividad([empresa.ana], titulo="Hecha")
    servicios.ejecucion.iniciar(hecha["id"], empresa.ana)
    reloj.avanzar(30)
    servicios.ejecucion.finalizar(hecha["id"], empresa.ana)
    reloj.avanzar(24 * 60)                                         # Ya es el día siguiente.

    semana = servicios.programacion.semana(empresa.ana, HOY, MANANA)
    assert semana["jornada_vigente"] == MANANA
    assert [t["tipo"] for t in dia(semana, HOY)["tramos"]] == ["FINALIZADA"]


def test_la_jornada_vigente_es_la_misma_que_la_de_hoy(servicios, empresa, crear_actividad):
    crear_actividad([empresa.ana])
    semana = servicios.programacion.semana(empresa.ana, HOY, MANANA)
    hoy = servicios.programacion.consultar(empresa.ana)
    assert dia(semana, HOY)["es_vigente"]
    assert dia(semana, HOY)["tramos"] == hoy["tramos"]


def test_el_rango_se_valida(servicios, empresa):
    with pytest.raises(ValidationError):
        servicios.programacion.semana(empresa.ana, MANANA, HOY)
    with pytest.raises(ValidationError):
        servicios.programacion.semana(empresa.ana, HOY, "2026-10-30")


def test_la_ruta_de_la_semana(cliente_de, empresa):
    respuesta = cliente_de(empresa.ana).get(f"/programacion-de-la-semana?desde={HOY}&hasta={MANANA}")
    assert respuesta.status_code == 200
    assert [d["fecha"] for d in respuesta.get_json()["dias"]] == [HOY, MANANA]
