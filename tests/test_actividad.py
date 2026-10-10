"""Pruebas de las clases Actividad y Proyecto: cancelar, reprogramar, No realizada y avance en horas."""
from datetime import datetime, timezone

import pytest

from app.models.actividad import Actividad
from app.models.enums import EstadoActividad
from app.models.proyecto import Proyecto
from app.utils.errors import ValidationError

AHORA = datetime(2026, 10, 11, 5, 0, tzinfo=timezone.utc)


def actividad(hora=None, estado=EstadoActividad.ASIGNADA):
    return Actividad(codigo="OT-0001", titulo="Calibrar sensor", descripcion="", empresa_id="emp1",
                     categoria="MANTENIMIENTO", ubicacion="Línea 1", tiempo_estimado_min=60,
                     fecha_programada="2026-10-10", hora_programada=hora, estado=estado)


def test_cancelar_exige_motivo_y_deja_constancia():
    a = actividad()
    with pytest.raises(ValidationError):
        a.cancelar("  ", "ana", AHORA)
    assert a.estado == EstadoActividad.ASIGNADA

    a.cancelar("Ya no se necesita", "ana", AHORA)
    assert a.estado == EstadoActividad.CANCELADA
    assert (a.cancelacion.motivo, a.cancelacion.autor_id, a.cancelacion.fecha) == ("Ya no se necesita", "ana", AHORA)


def test_no_se_cancela_lo_que_alguien_tiene_en_curso():
    en_curso = actividad(estado=EstadoActividad.EN_EJECUCION)
    with pytest.raises(ValidationError):
        en_curso.cancelar("Otro", "ana", AHORA)


def test_si_se_cancela_una_pausada():
    a = actividad(estado=EstadoActividad.PAUSADA)
    a.cancelar("Falta de recursos", "ana", AHORA)
    assert a.estado == EstadoActividad.CANCELADA


@pytest.mark.parametrize("final", [EstadoActividad.COMPLETADA, EstadoActividad.NO_REALIZADA, EstadoActividad.CANCELADA])
def test_un_estado_final_no_cambia(final):
    a = actividad(estado=final)
    with pytest.raises(ValidationError):
        a.cancelar("Otro", "ana", AHORA)
    with pytest.raises(ValidationError):
        a.reprogramar("2026-10-11", AHORA)


def test_reprogramar_conserva_la_fecha_original_y_el_estado():
    a = actividad(estado=EstadoActividad.PAUSADA)
    a.reprogramar("2026-10-11", AHORA)
    a.reprogramar("2026-10-13", AHORA)
    assert a.fecha_programada == "2026-10-13"
    assert a.fecha_original == "2026-10-10"
    assert a.fue_reprogramada
    assert a.estado == EstadoActividad.PAUSADA
    assert [(x.jornada_origen, x.jornada_destino) for x in a.reprogramaciones] == [
        ("2026-10-10", "2026-10-11"), ("2026-10-11", "2026-10-13")]


def test_no_se_reprograma_hacia_atras_ni_una_de_hora_fija():
    flexible, fija = actividad(), actividad(hora="10:00")
    with pytest.raises(ValidationError):
        flexible.reprogramar("2026-10-10", AHORA)
    with pytest.raises(ValidationError):
        fija.reprogramar("2026-10-11", AHORA)


def test_solo_la_de_hora_fija_queda_no_realizada():
    fija = actividad(hora="10:00")
    fija.marcar_no_realizada(AHORA)
    assert fija.estado == EstadoActividad.NO_REALIZADA
    assert fija.fecha_no_realizada == AHORA
    flexible = actividad()
    with pytest.raises(ValidationError):
        flexible.marcar_no_realizada(AHORA)


def test_se_guarda_y_se_reconstruye_igual():
    a = actividad()
    a.reprogramar("2026-10-11", AHORA)
    a.cancelar("Duplicada", "ana", AHORA)
    copia = Actividad.desde_documento({"_id": "x1", **a.to_dict()})
    assert copia.to_dict() == a.to_dict()


def test_un_documento_anterior_no_esta_reprogramado():
    doc = {"_id": "x1", "titulo": "Vieja", "requerimiento_id": "r1", "fecha_programada": "2026-10-01"}
    presentada = Actividad.from_doc(doc)
    assert presentada["fecha_original"] == "2026-10-01"
    assert presentada["reprogramada"] is False
    assert presentada["proyecto_id"] is None


def test_el_proyecto_exige_nombre():
    with pytest.raises(ValidationError):
        Proyecto("  ", "emp1")


def test_avance_del_proyecto_en_horas():
    actividades = [
        {"estado": "COMPLETADA", "tiempo_estimado_min": 120},
        {"estado": "ASIGNADA", "tiempo_estimado_min": 60},
        {"estado": "NO_REALIZADA", "tiempo_estimado_min": 60},     # Se queda en el total.
        {"estado": "CANCELADA", "tiempo_estimado_min": 600},       # Sale del total.
    ]
    assert Proyecto.calcular_avance(actividades) == {
        "minutos_finalizados": 120, "minutos_totales": 240, "porcentaje": 50, "actividades": 3}
    assert Proyecto.calcular_avance([])["porcentaje"] == 0
