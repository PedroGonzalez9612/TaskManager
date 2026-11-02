"""Pruebas de la pantalla Hoy del Administrador (alcance, Sección 6.2): personas y pendientes.
El reloj empieza el 2026-10-10 a las 08:00 UTC: las 03:00 en Bogotá."""
import pytest

from app.models.presencia import ESPACIO_MINIMO_MIN
from app.utils.errors import ProhibidoError

MADRUGADA = {"nombre": "Madrugada", "hora_inicio": "02:00", "hora_fin": "10:00", "descanso_min": 30}   # Capacidad: 450 min.


@pytest.fixture
def madrugada(servicios, empresa):
    """Ana y Luis en un turno que empezó hace una hora."""
    turno = servicios.turnos.crear_turno(MADRUGADA, empresa.admin)
    for operario in (empresa.ana, empresa.luis):
        servicios.turnos.asignar_turno(empresa.admin, operario["id"], turno["id"], "2026-10-10")
    return turno


def persona(servicios, empresa, operario):
    return next(p for p in servicios.hoy.personas(empresa.admin) if p["id"] == operario["id"])


# ---------- Personas ----------

def test_cada_persona_trae_su_presencia_lo_que_hace_y_su_carga(servicios, empresa, crear_actividad, madrugada):
    actividad = crear_actividad([empresa.ana], tiempo_estimado_min=60)
    servicios.asistencia.marcar_entrada(empresa.ana)
    servicios.ejecucion.iniciar(actividad["id"], empresa.ana)

    ana = persona(servicios, empresa, empresa.ana)
    assert ana["presencia"] == {"estado": "EN_TURNO", "minutos": 0}
    assert ana["actividad"]["tipo"] == "EN_CURSO"
    assert ana["actividad"]["id"] == actividad["id"]
    assert ana["carga"] == {"minutos": 60, "capacidad_min": 450, "porcentaje": 13, "estado": "CON_ESPACIO"}
    assert ana["turno"]["nombre"] == "Madrugada"

    luis = persona(servicios, empresa, empresa.luis)
    assert luis["presencia"] == {"estado": "LLEGADA_TARDE", "minutos": 60}
    assert luis["actividad"] == {"tipo": "NINGUNA"}


def test_sin_turno_la_presencia_lo_dice(servicios, empresa):
    assert persona(servicios, empresa, empresa.ana)["presencia"]["estado"] == "SIN_TURNO"


def test_la_carga_es_normal_si_le_queda_menos_de_una_hora(servicios, empresa, crear_actividad, madrugada):
    crear_actividad([empresa.ana], tiempo_estimado_min=450 - ESPACIO_MINIMO_MIN + 1)
    assert persona(servicios, empresa, empresa.ana)["carga"]["estado"] == "NORMAL"


def test_solo_el_administrador_ve_hoy(servicios, empresa):
    with pytest.raises(ProhibidoError):
        servicios.hoy.personas(empresa.ana)


# ---------- Pendientes ----------

def test_la_llegada_tarde_trae_lo_suyo_de_hoy_para_reasignar(servicios, empresa, crear_actividad, madrugada):
    suya = crear_actividad([empresa.luis], titulo="Revisar la báscula")
    crear_actividad([empresa.ana], titulo="De Ana")
    servicios.asistencia.marcar_entrada(empresa.ana)

    pendientes = servicios.hoy.pendientes(empresa.admin)

    [tarde] = pendientes["llegada_tarde"]
    assert tarde["id"] == empresa.luis["id"]
    assert tarde["presencia"]["minutos"] == 60
    assert [a["id"] for a in tarde["actividades"]] == [suya["id"]]


def test_la_de_hora_fija_detenida_por_emergencia_es_pendiente(servicios, empresa, crear_actividad, madrugada, reloj):
    fija = crear_actividad([empresa.ana], hora_programada="03:00")
    servicios.asistencia.marcar_entrada(empresa.ana)
    servicios.ejecucion.iniciar(fija["id"], empresa.ana)
    reloj.avanzar(5)
    servicios.ejecucion.pausar(fija["id"], empresa.ana, "Falla del equipo")

    [detenida] = servicios.hoy.pendientes(empresa.admin)["detenidas"]
    assert detenida["id"] == empresa.ana["id"]
    assert detenida["actividad"]["tipo"] == "DETENIDA"
    assert detenida["actividad"]["motivo"] == "Falla del equipo"


def test_una_pausa_normal_no_es_pendiente(servicios, empresa, crear_actividad, madrugada, reloj):
    actividad = crear_actividad([empresa.ana])
    servicios.asistencia.marcar_entrada(empresa.ana)
    servicios.ejecucion.iniciar(actividad["id"], empresa.ana)
    reloj.avanzar(5)
    servicios.ejecucion.pausar(actividad["id"], empresa.ana, "Otro", "Almuerzo")
    assert servicios.hoy.pendientes(empresa.admin)["detenidas"] == []


def test_lo_sin_dueno_los_reportes_y_los_sobrecargados(servicios, empresa, crear_actividad, madrugada):
    sin_nadie = crear_actividad([], titulo="Sin nadie")
    crear_actividad([empresa.ana], tiempo_estimado_min=500)
    servicios.reportes.reportar({"titulo": "Mover estibas", "pedido_por": "Despachos"}, empresa.luis)
    servicios.asistencia.marcar_entrada(empresa.ana)
    servicios.asistencia.marcar_entrada(empresa.luis)

    pendientes = servicios.hoy.pendientes(empresa.admin)

    assert [a["id"] for a in pendientes["sin_dueno"]] == [sin_nadie["id"]]
    assert [r["titulo"] for r in pendientes["reportes"]] == ["Mover estibas"]
    assert [p["id"] for p in pendientes["sobrecargados"]] == [empresa.ana["id"]]
    assert pendientes["llegada_tarde"] == []
    assert pendientes["total"] == 3


def test_sin_nada_que_decidir_el_total_es_cero(servicios, empresa):
    assert servicios.hoy.pendientes(empresa.admin)["total"] == 0


# ---------- Rutas ----------

def test_rutas_de_hoy(cliente_de, empresa):
    admin = cliente_de(empresa.admin)
    assert admin.get("/hoy/personas").status_code == 200
    assert admin.get("/hoy/pendientes").get_json()["total"] == 0
    assert cliente_de(empresa.ana).get("/hoy/personas").status_code == 403
