"""Pruebas de la clase Asignacion: una asignación se cierra, nunca se borra."""
from datetime import datetime, timezone

import pytest

from app.models.asignacion import Asignacion
from app.models.enums import EstadoAsignacion
from app.utils.errors import ValidationError

AHORA = datetime(2026, 10, 10, 9, 0, tzinfo=timezone.utc)


def test_nace_activa():
    asignacion = Asignacion("act1", "carlos", asignada_por_id="ana")
    assert asignacion.esta_activa
    assert asignacion.estado == EstadoAsignacion.ACTIVA


def test_devolver_exige_motivo_y_deja_constancia():
    asignacion = Asignacion("act1", "carlos")
    with pytest.raises(ValidationError):
        asignacion.devolver("", AHORA)
    assert asignacion.esta_activa

    asignacion.devolver("Falta información", AHORA)
    assert asignacion.estado == EstadoAsignacion.DEVUELTA
    assert asignacion.devolucion.motivo == "Falta información"
    assert asignacion.fecha_fin == AHORA


def test_retirar_guarda_quien_y_cuando():
    asignacion = Asignacion("act1", "carlos")
    asignacion.retirar("ana", AHORA)
    assert asignacion.estado == EstadoAsignacion.RETIRADA
    assert asignacion.retirada_por_id == "ana"
    assert asignacion.fecha_fin == AHORA


def test_una_asignacion_cerrada_no_cambia_mas():
    asignacion = Asignacion("act1", "carlos")
    asignacion.retirar("ana", AHORA)
    with pytest.raises(ValidationError):
        asignacion.devolver("Falta información", AHORA)
    with pytest.raises(ValidationError):
        asignacion.retirar("ana", AHORA)


def test_los_documentos_anteriores_sin_estado_son_activos():
    asignacion = Asignacion.desde_documento({"_id": "x1", "actividad_id": "act1", "usuario_id": "carlos"})
    assert asignacion.esta_activa


def test_se_guarda_y_se_reconstruye_igual():
    asignacion = Asignacion("act1", "carlos", fecha_asignacion=AHORA, asignada_por_id="ana")
    asignacion.devolver("El equipo no está disponible", AHORA)
    copia = Asignacion.desde_documento({"_id": "x1", **asignacion.to_dict()})
    assert copia.to_dict() == asignacion.to_dict()
