"""Pruebas de las clases Turno, AsignacionTurno y Asistencia. No usan base de datos."""
from datetime import datetime, timezone

import pytest

from app.models.asistencia import Asistencia, EstadoAsistencia
from app.models.turno import AsignacionTurno, Turno, turno_vigente
from app.utils.errors import ValidationError

ZONA = "America/Bogota"


def utc(dia, hora, minuto=0):
    return datetime(2026, 10, dia, hora, minuto, tzinfo=timezone.utc)


# ---------- Turno ----------

def test_capacidad_es_la_duracion_menos_el_descanso():
    turno = Turno("Mañana", "06:00", "14:00", 60, "emp1")
    assert turno.duracion_min == 480
    assert turno.capacidad_min == 420


def test_un_turno_de_noche_termina_al_dia_siguiente():
    turno = Turno("Noche", "22:00", "06:00", 30, "emp1")
    assert turno.duracion_min == 480
    # 22:00 de Bogotá del día 10 = 03:00 UTC del 11; termina 8 horas después.
    assert turno.inicio_en("2026-10-10", ZONA) == utc(11, 3)
    assert turno.fin_en("2026-10-10", ZONA) == utc(11, 11)


@pytest.mark.parametrize("datos", [
    {"nombre": " "},
    {"hora_inicio": "25:00"},
    {"hora_fin": "06:00"},             # Igual a la de inicio.
    {"descanso_min": -5},
    {"descanso_min": 480},             # Ocupa todo el turno.
    {"descanso_min": "media hora"},
])
def test_el_turno_valida_sus_datos(datos):
    campos = {"nombre": "Mañana", "hora_inicio": "06:00", "hora_fin": "14:00", "descanso_min": 60, **datos}
    with pytest.raises(ValidationError):
        Turno(empresa_id="emp1", **campos)


def test_el_turno_se_guarda_y_se_reconstruye_igual():
    turno = Turno("Mañana", "6:00", "14:00", 60, "emp1")
    copia = Turno.desde_documento({"_id": "t1", **turno.to_dict()})
    assert copia.to_dict() == turno.to_dict()
    assert copia.presentar()["capacidad_min"] == 420


# ---------- Turno vigente ----------

def test_rige_el_turno_mas_reciente_que_ya_empezo():
    asignaciones = [
        AsignacionTurno("carlos", "manana", "2026-10-01"),
        AsignacionTurno("carlos", "tarde", "2026-10-08"),
        AsignacionTurno("carlos", "noche", "2026-10-20"),
    ]
    assert turno_vigente(asignaciones, "2026-10-05").turno_id == "manana"
    assert turno_vigente(asignaciones, "2026-10-10").turno_id == "tarde"
    assert turno_vigente(asignaciones, "2026-09-30") is None


def test_dos_cambios_el_mismo_dia_rige_el_ultimo():
    asignaciones = [
        AsignacionTurno("carlos", "manana", "2026-10-10", fecha_registro=utc(10, 8)),
        AsignacionTurno("carlos", "tarde", "2026-10-10", fecha_registro=utc(10, 9)),
    ]
    assert turno_vigente(asignaciones, "2026-10-10").turno_id == "tarde"


# ---------- Asistencia ----------

def nueva_asistencia():
    return Asistencia("carlos", "emp1", "2026-10-10", entrada=utc(10, 11))


def test_marcar_salida_y_tiempo_presente():
    asistencia = nueva_asistencia()
    assert asistencia.minutos_presente(utc(10, 12)) == 60
    asistencia.marcar_salida(utc(10, 19, 30))
    assert asistencia.esta_abierta is False
    assert asistencia.minutos_presente(utc(10, 23)) == 510


def test_no_se_marca_salida_dos_veces_ni_antes_de_la_entrada():
    asistencia, antes, despues = nueva_asistencia(), utc(10, 10), utc(10, 19)
    with pytest.raises(ValidationError):
        asistencia.marcar_salida(antes)
    asistencia.marcar_salida(despues)
    with pytest.raises(ValidationError):
        asistencia.marcar_salida(despues)


def test_validar_exige_entrada_y_salida():
    asistencia, momento = nueva_asistencia(), utc(10, 20)
    with pytest.raises(ValidationError):
        asistencia.validar("ana", momento)
    asistencia.marcar_salida(utc(10, 19))
    asistencia.validar("ana", utc(10, 20))
    assert asistencia.estado == EstadoAsistencia.VALIDADA
    assert asistencia.revision == {"autor_id": "ana", "fecha": utc(10, 20)}


def test_corregir_exige_motivo_y_conserva_las_marcas_originales():
    asistencia = nueva_asistencia()
    entrada, salida, momento = utc(10, 10, 55), utc(10, 19), utc(10, 20)
    with pytest.raises(ValidationError):
        asistencia.corregir(entrada, salida, " ", "ana", momento)
    asistencia.corregir(entrada, salida, "Olvidó marcar la salida", "ana", utc(10, 20))
    assert asistencia.estado == EstadoAsistencia.CORREGIDA
    assert (asistencia.entrada, asistencia.salida) == (entrada, salida)
    assert asistencia.revision["entrada_original"] == utc(10, 11)
    assert asistencia.revision["salida_original"] is None


def test_una_correccion_no_deja_la_salida_antes_de_la_entrada():
    asistencia, entrada, salida, momento = nueva_asistencia(), utc(10, 12), utc(10, 11), utc(10, 20)
    with pytest.raises(ValidationError):
        asistencia.corregir(entrada, salida, "Error", "ana", momento)


def test_la_asistencia_se_guarda_y_se_reconstruye_igual():
    asistencia = nueva_asistencia()
    asistencia.marcar_salida(utc(10, 19))
    copia = Asistencia.desde_documento({"_id": "a1", **asistencia.to_dict()})
    assert copia.to_dict() == asistencia.to_dict()
