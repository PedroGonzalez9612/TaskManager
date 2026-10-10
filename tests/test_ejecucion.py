"""Pruebas de las clases Ejecucion y Pausa. No necesitan base de datos ni Flask.
Ejecutar desde la raíz del proyecto: python -m pytest"""
from datetime import datetime, timedelta, timezone

import pytest

from app.models.ejecucion import Ejecucion
from app.models.enums import EstadoEjecucion
from app.utils.errors import ValidationError

INICIO = datetime(2026, 10, 10, 8, 0, tzinfo=timezone.utc)


def a_los(minutos):
    return INICIO + timedelta(minutes=minutos)


def nueva_ejecucion():
    return Ejecucion(actividad_id="act1", asignacion_id="asig1", usuario_id="carlos", fecha_inicio=INICIO)


def test_nace_en_progreso_y_cuenta_el_tiempo():
    ejecucion = nueva_ejecucion()
    assert ejecucion.estado == EstadoEjecucion.EN_PROGRESO
    assert ejecucion.tiempo_real_min(a_los(30)) == 30


def test_pausar_exige_motivo():
    ejecucion = nueva_ejecucion()
    momento = a_los(10)
    with pytest.raises(ValidationError):
        ejecucion.pausar("   ", momento)
    assert ejecucion.estado == EstadoEjecucion.EN_PROGRESO
    assert ejecucion.pausas == []


def test_cada_pausa_guarda_su_motivo():
    ejecucion = nueva_ejecucion()
    ejecucion.pausar("Actividad urgente", a_los(10))
    ejecucion.reanudar(a_los(25))
    ejecucion.pausar("Falta material", a_los(40))
    assert [pausa.motivo for pausa in ejecucion.pausas] == ["Actividad urgente", "Falta material"]


def test_no_hay_dos_pausas_abiertas():
    ejecucion = nueva_ejecucion()
    ejecucion.pausar("Actividad urgente", a_los(10))
    momento = a_los(12)
    with pytest.raises(ValidationError):
        ejecucion.pausar("Otra", momento)
    assert len(ejecucion.pausas) == 1


def test_reanudar_cierra_la_pausa_abierta():
    ejecucion = nueva_ejecucion()
    ejecucion.pausar("Actividad urgente", a_los(10))
    ejecucion.reanudar(a_los(25))
    assert ejecucion.estado == EstadoEjecucion.EN_PROGRESO
    assert ejecucion.pausa_abierta() is None
    assert ejecucion.pausas[0].fin == a_los(25)


def test_no_se_reanuda_lo_que_no_esta_pausado():
    ejecucion, momento = nueva_ejecucion(), a_los(5)
    with pytest.raises(ValidationError):
        ejecucion.reanudar(momento)


def test_el_tiempo_real_descuenta_las_pausas():
    ejecucion = nueva_ejecucion()
    ejecucion.pausar("Actividad urgente", a_los(10))    # 15 minutos de pausa
    ejecucion.reanudar(a_los(25))
    ejecucion.pausar("Falta material", a_los(40))       # 5 minutos de pausa
    ejecucion.reanudar(a_los(45))
    ejecucion.finalizar(a_los(60))
    assert ejecucion.tiempo_real_min(a_los(500)) == 40  # 60 minutos menos 20 de pausas


def test_mientras_esta_pausada_el_tiempo_no_corre():
    ejecucion = nueva_ejecucion()
    ejecucion.pausar("Fin de jornada", a_los(20))
    assert ejecucion.tiempo_real_min(a_los(20)) == 20
    assert ejecucion.tiempo_real_min(a_los(900)) == 20


def test_no_se_finaliza_estando_pausada():
    ejecucion = nueva_ejecucion()
    ejecucion.pausar("Actividad urgente", a_los(10))
    momento = a_los(20)
    with pytest.raises(ValidationError):
        ejecucion.finalizar(momento)


def test_finalizar_guarda_la_observacion_y_no_se_repite():
    ejecucion = nueva_ejecucion()
    ejecucion.finalizar(a_los(30), observacion="  Quedó calibrado.  ")
    assert ejecucion.estado == EstadoEjecucion.FINALIZADA
    assert ejecucion.observacion == "Quedó calibrado."
    assert ejecucion.fecha_fin == a_los(30)
    momento = a_los(40)
    with pytest.raises(ValidationError):
        ejecucion.finalizar(momento)


def test_cerrar_conserva_el_tiempo_y_cierra_la_pausa():
    ejecucion = nueva_ejecucion()
    ejecucion.pausar("Actividad urgente", a_los(10))
    ejecucion.cerrar(a_los(50))
    assert ejecucion.estado == EstadoEjecucion.CERRADA
    assert ejecucion.pausa_abierta() is None
    assert ejecucion.tiempo_real_min(a_los(999)) == 10
    momento = a_los(60)
    with pytest.raises(ValidationError):
        ejecucion.cerrar(momento)


def test_se_guarda_y_se_reconstruye_igual():
    ejecucion = nueva_ejecucion()
    ejecucion.pausar("Actividad urgente", a_los(10))
    ejecucion.reanudar(a_los(25))
    documento = {"_id": "abc", **ejecucion.to_dict()}
    copia = Ejecucion.desde_documento(documento)
    assert copia.to_dict() == ejecucion.to_dict()
    assert copia.id == "abc"


def test_acepta_las_fechas_sin_zona_que_devuelve_mongo():
    ejecucion = Ejecucion(actividad_id="act1", fecha_inicio=INICIO.replace(tzinfo=None))
    assert ejecucion.tiempo_real_min(a_los(30)) == 30
