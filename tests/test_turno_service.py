"""Pruebas del catálogo de turnos, del turno de cada operario y de la capacidad que sale de él
(alcance, Secciones 5.1 y 5.2), por el servicio y por la API.
El reloj empieza el 2026-10-10 a las 08:00 UTC: las 03:00 en Bogotá."""
from datetime import datetime, timezone

import pytest

from app.repositories.turno_repository import AsignacionTurnoRepository
from app.utils.errors import NotFoundError, ProhibidoError, ValidationError

from tests.conftest import HOY

PROPIA = {"X-Requested-With": "GestLab"}
MANANA = {"nombre": "Mañana", "hora_inicio": "06:00", "hora_fin": "14:00", "descanso_min": 60}
TARDE = {"nombre": "Tarde", "hora_inicio": "14:00", "hora_fin": "22:00", "descanso_min": 30}


@pytest.fixture
def turnos(servicios):
    return servicios.turnos


@pytest.fixture
def manana(turnos, empresa):
    return turnos.crear_turno(MANANA, empresa.admin)


@pytest.fixture
def tarde(turnos, empresa):
    return turnos.crear_turno(TARDE, empresa.admin)


# ---------- Catálogo de turnos ----------

def test_crear_un_turno_valido(manana, empresa):
    assert manana["nombre"] == "Mañana"
    assert manana["empresa_id"] == empresa.id
    assert manana["duracion_min"] == 480
    assert manana["capacidad_min"] == 420
    assert manana["id"]


@pytest.mark.parametrize("cambios", [
    {"nombre": ""}, {"hora_inicio": "6 am"}, {"hora_fin": "06:00"}, {"descanso_min": 480}, {"descanso_min": "x"},
])
def test_crear_un_turno_invalido_da_error(turnos, empresa, cambios):
    datos = {**MANANA, **cambios}
    with pytest.raises(ValidationError):
        turnos.crear_turno(datos, empresa.admin)


def test_solo_el_administrador_gestiona_turnos(turnos, empresa):
    with pytest.raises(ProhibidoError):
        turnos.crear_turno(MANANA, empresa.ana)


def test_listar_por_hora_de_inicio_y_solo_los_de_mi_empresa(turnos, empresa, otra_empresa, tarde, manana):
    turnos.crear_turno(MANANA, otra_empresa.admin)
    assert [t["nombre"] for t in turnos.listar_turnos(empresa.admin)] == ["Mañana", "Tarde"]


def test_editar_un_turno_cambia_solo_lo_que_llega(turnos, empresa, manana):
    editado = turnos.editar_turno(manana["id"], {"hora_fin": "15:00"}, empresa.admin)
    assert editado["hora_fin"] == "15:00"
    assert editado["nombre"] == "Mañana"
    assert editado["capacidad_min"] == 480
    assert turnos.listar_turnos(empresa.admin)[0]["hora_fin"] == "15:00"


@pytest.mark.parametrize("datos", [{}, {"descanso_min": -1}, {"hora_inicio": "14:00"}])
def test_editar_un_turno_valida_sus_datos(turnos, empresa, manana, datos):
    with pytest.raises(ValidationError):
        turnos.editar_turno(manana["id"], datos, empresa.admin)


def test_un_turno_de_otra_empresa_no_existe_para_mi(turnos, otra_empresa, manana):
    with pytest.raises(NotFoundError):
        turnos.editar_turno(manana["id"], {"nombre": "Ajeno"}, otra_empresa.admin)


def test_la_asignacion_sigue_al_turno_editado(turnos, empresa, manana):
    turnos.asignar_turno(empresa.admin, empresa.ana["id"], manana["id"])
    turnos.editar_turno(manana["id"], {"descanso_min": 0}, empresa.admin)
    assert turnos.capacidad_de(empresa.ana["id"], HOY) == 480


# ---------- Turno de cada operario ----------

def test_asignar_un_turno_rige_desde_hoy_por_defecto(turnos, empresa, manana):
    asignacion = turnos.asignar_turno(empresa.admin, empresa.ana["id"], manana["id"])
    assert asignacion["desde"] == HOY
    assert asignacion["turno"]["nombre"] == "Mañana"
    assert turnos.turno_de(empresa.ana["id"], HOY).nombre == "Mañana"
    assert turnos.turno_de(empresa.ana["id"], "2026-10-09") is None


def test_cambiar_de_turno_conserva_el_anterior(turnos, empresa, manana, tarde, db, reloj):
    turnos.asignar_turno(empresa.admin, empresa.ana["id"], manana["id"])
    turnos.asignar_turno(empresa.admin, empresa.ana["id"], tarde["id"], "2026-10-12")

    assert turnos.turno_de(empresa.ana["id"], HOY).nombre == "Mañana"
    assert turnos.turno_de(empresa.ana["id"], "2026-10-11").nombre == "Mañana"
    assert turnos.turno_de(empresa.ana["id"], "2026-10-12").nombre == "Tarde"
    historial = AsignacionTurnoRepository(db).find_de_usuario(empresa.ana["id"])
    assert [a["desde"] for a in historial] == [HOY, "2026-10-12"]
    assert historial[0]["asignado_por_id"] == empresa.admin["id"]
    assert historial[0]["fecha_registro"].replace(tzinfo=timezone.utc) == reloj.ahora


def test_dos_cambios_el_mismo_dia_rige_el_ultimo(turnos, empresa, manana, tarde, reloj):
    turnos.asignar_turno(empresa.admin, empresa.ana["id"], manana["id"])
    reloj.avanzar(5)
    turnos.asignar_turno(empresa.admin, empresa.ana["id"], tarde["id"])
    assert turnos.turno_de(empresa.ana["id"], HOY).nombre == "Tarde"


@pytest.mark.parametrize("desde", ["2026-10-09", "10/12/2026"])
def test_no_se_asigna_desde_un_dia_que_ya_paso_ni_con_fecha_invalida(turnos, empresa, manana, desde):
    with pytest.raises(ValidationError):
        turnos.asignar_turno(empresa.admin, empresa.ana["id"], manana["id"], desde)


def test_hoy_es_el_dia_de_la_empresa(turnos, empresa, manana, reloj):
    # A las 03:00 UTC del 11 todavía son las 22:00 del 10 en Bogotá: el 10 no ha pasado.
    reloj.ahora = datetime(2026, 10, 11, 3, 0, tzinfo=timezone.utc)
    assert turnos.asignar_turno(empresa.admin, empresa.ana["id"], manana["id"], HOY)["desde"] == HOY


def test_el_operario_debe_ser_un_operario_de_mi_empresa(turnos, empresa, otra_empresa, manana):
    for usuario in (otra_empresa.ivan, empresa.admin):
        with pytest.raises(NotFoundError):
            turnos.asignar_turno(empresa.admin, usuario["id"], manana["id"])


def test_el_turno_debe_ser_de_mi_empresa(turnos, empresa, otra_empresa):
    ajeno = turnos.crear_turno(MANANA, otra_empresa.admin)
    with pytest.raises(NotFoundError):
        turnos.asignar_turno(empresa.admin, empresa.ana["id"], ajeno["id"])


def test_asignar_exige_el_turno(turnos, empresa):
    with pytest.raises(ValidationError):
        turnos.asignar_turno(empresa.admin, empresa.ana["id"], None)


def test_el_operario_no_se_asigna_turno(turnos, empresa, manana):
    with pytest.raises(ProhibidoError):
        turnos.asignar_turno(empresa.ana, empresa.ana["id"], manana["id"])


# ---------- Capacidad desde el turno ----------

def test_sin_turno_la_capacidad_sigue_siendo_la_provisional(turnos, empresa):
    assert turnos.capacidad_de(empresa.ana["id"], HOY) == 420


def test_la_carga_usa_la_capacidad_del_turno_de_cada_operario(servicios, turnos, empresa, crear_actividad):
    corto = turnos.crear_turno({"nombre": "Corto", "hora_inicio": "06:00", "hora_fin": "12:00"}, empresa.admin)
    turnos.asignar_turno(empresa.admin, empresa.ana["id"], corto["id"])
    crear_actividad([empresa.ana, empresa.luis], tiempo_estimado_min=400)

    carga = servicios.carga.consultar(HOY, HOY, empresa.admin)
    jornadas = {o["nombre"]: o["jornadas"][0] for o in carga["operarios"]}
    assert carga["capacidad_min"] == 420
    assert jornadas["Ana"]["capacidad_min"] == 360
    assert jornadas["Ana"]["sobrecarga"] is True
    assert jornadas["Luis"]["capacidad_min"] == 420
    assert jornadas["Luis"]["sobrecarga"] is False


def test_la_alerta_al_asignar_usa_la_capacidad_del_turno(servicios, turnos, empresa):
    corto = turnos.crear_turno({"nombre": "Corto", "hora_inicio": "06:00", "hora_fin": "08:00"}, empresa.admin)
    turnos.asignar_turno(empresa.admin, empresa.ana["id"], corto["id"])
    alertas = servicios.carga.sobrecargas(empresa.id, HOY, [empresa.ana["id"], empresa.luis["id"]])
    assert alertas == []
    servicios.actividades.crear_actividad({
        "titulo": "Lubricar", "ubicacion": "Línea 1", "categoria": "MANTENIMIENTO", "tiempo_estimado_min": 180,
        "fecha_programada": HOY, "operario_ids": [empresa.ana["id"], empresa.luis["id"]],
        "requerimiento_id": empresa.requerimiento_id,
    }, empresa.admin)
    alertas = servicios.carga.sobrecargas(empresa.id, HOY, [empresa.ana["id"], empresa.luis["id"]])
    assert [(a["operario"], a["capacidad_min"]) for a in alertas] == [("Ana", 120)]


def test_la_programacion_usa_la_capacidad_y_el_horario_del_turno(servicios, turnos, empresa):
    # De 02:00 a 10:00 en Bogotá (07:00 a 15:00 UTC); a las 03:00 de Bogotá está en su turno.
    madrugada = turnos.crear_turno(
        {"nombre": "Madrugada", "hora_inicio": "02:00", "hora_fin": "10:00", "descanso_min": 30}, empresa.admin)
    turnos.asignar_turno(empresa.admin, empresa.ana["id"], madrugada["id"])

    programacion = servicios.programacion.consultar(empresa.ana)
    assert programacion["resumen"]["capacidad_min"] == 450
    assert programacion["turno"] == {
        "nombre": "Madrugada", "hora_inicio": "02:00", "hora_fin": "10:00",
        "inicio": datetime(2026, 10, 10, 7, 0, tzinfo=timezone.utc),
        "fin": datetime(2026, 10, 10, 15, 0, tzinfo=timezone.utc), "capacidad_min": 450,
    }
    assert programacion["en_turno"] is True
    assert programacion["asistencia"] is None


def test_fuera_del_horario_del_turno_no_esta_en_turno(servicios, turnos, empresa, tarde):
    turnos.asignar_turno(empresa.admin, empresa.ana["id"], tarde["id"])
    assert servicios.programacion.consultar(empresa.ana)["en_turno"] is False


def test_sin_turno_la_programacion_sigue_con_la_capacidad_provisional(servicios, empresa):
    programacion = servicios.programacion.consultar(empresa.ana)
    assert programacion["resumen"]["capacidad_min"] == 420
    assert programacion["turno"] is None
    assert programacion["en_turno"] is False


# ---------- Por la API ----------

def test_la_api_de_turnos(cliente_de, empresa, otra_empresa):
    marta = cliente_de(empresa.admin)
    assert marta.post("/turnos", json={**MANANA, "hora_fin": "25:00"}, headers=PROPIA).status_code == 400
    creado = marta.post("/turnos", json=MANANA, headers=PROPIA)
    assert creado.status_code == 201
    turno_id = creado.get_json()["id"]

    assert [t["nombre"] for t in marta.get("/turnos").get_json()] == ["Mañana"]
    editado = marta.put(f"/turnos/{turno_id}", json={"nombre": "Mañana larga"}, headers=PROPIA)
    assert editado.get_json()["nombre"] == "Mañana larga"
    assert cliente_de(otra_empresa.admin).put(f"/turnos/{turno_id}", json={"nombre": "X"},
                                              headers=PROPIA).status_code == 404
    assert cliente_de(empresa.ana).get("/turnos").status_code == 403


def test_la_api_asigna_el_turno_y_la_lista_de_usuarios_lo_trae(cliente_de, empresa, turnos, manana):
    marta = cliente_de(empresa.admin)
    respuesta = marta.put(f"/usuarios/{empresa.ana['id']}/turno", json={"turno_id": manana["id"]}, headers=PROPIA)
    assert respuesta.status_code == 200
    assert respuesta.get_json()["desde"] == HOY

    usuarios = {u["nombre"]: u for u in marta.get("/usuarios").get_json()}
    assert usuarios["Ana"]["turno"] == {"id": manana["id"], "nombre": "Mañana", "hora_inicio": "06:00",
                                        "hora_fin": "14:00"}
    assert usuarios["Luis"]["turno"] is None
    assert "turno" not in usuarios["Marta"]


def test_la_api_rechaza_asignar_turno_con_datos_malos(cliente_de, empresa, manana):
    marta = cliente_de(empresa.admin)
    ruta = f"/usuarios/{empresa.ana['id']}/turno"
    assert marta.put(ruta, json={"turno_id": manana["id"], "desde": "2026-10-01"}, headers=PROPIA).status_code == 400
    assert marta.put(ruta, data="no es json", headers=PROPIA).status_code == 400
    assert cliente_de(empresa.ana).put(ruta, json={"turno_id": manana["id"]}, headers=PROPIA).status_code == 403


def test_la_lista_de_usuarios_lee_los_turnos_de_todos_de_una_vez(cliente_de, empresa, manana, monkeypatch):
    llamadas = []
    original = AsignacionTurnoRepository.find_de_usuarios

    def contar(self, usuario_ids):
        llamadas.append(list(usuario_ids))
        return original(self, usuario_ids)
    monkeypatch.setattr(AsignacionTurnoRepository, "find_de_usuarios", contar)

    cliente_de(empresa.admin).get("/usuarios")
    assert len(llamadas) == 1
    assert sorted(llamadas[0]) == sorted([empresa.ana["id"], empresa.luis["id"]])
