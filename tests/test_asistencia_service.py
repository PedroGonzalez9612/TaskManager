"""Pruebas del registro de asistencia (alcance, Sección 5.1), por el servicio y por la API.
El reloj empieza el 2026-10-10 a las 08:00 UTC: las 03:00 en Bogotá."""
from datetime import datetime, timezone

import pytest

from app.repositories.asistencia_repository import AsistenciaRepository
from app.utils.errors import NotFoundError, ProhibidoError, ValidationError

from tests.conftest import HOY

PROPIA = {"X-Requested-With": "GestLab"}
NOCHE = {"nombre": "Noche", "hora_inicio": "22:00", "hora_fin": "06:00", "descanso_min": 30}
TARDE = {"nombre": "Tarde", "hora_inicio": "14:00", "hora_fin": "22:00", "descanso_min": 30}


def utc(dia, hora, minuto=0):
    return datetime(2026, 10, dia, hora, minuto, tzinfo=timezone.utc)


def en_utc(momento):
    """MongoDB devuelve las fechas sin zona; están en UTC."""
    return momento.replace(tzinfo=timezone.utc)


@pytest.fixture
def asistencia(servicios):
    return servicios.asistencia


@pytest.fixture
def asistencias(db):
    return AsistenciaRepository(db)


@pytest.fixture
def tarde(servicios, empresa):
    return servicios.turnos.crear_turno(TARDE, empresa.admin)


@pytest.fixture
def jornada_cerrada(asistencia, empresa, reloj):
    """Ana marca entrada a las 03:00 de Bogotá y salida ocho horas después."""
    asistencia.marcar_entrada(empresa.ana)
    reloj.avanzar(480)
    return asistencia.marcar_salida(empresa.ana)


# ---------- Marcas del Operario ----------

def test_marcar_entrada_con_la_hora_del_servidor(asistencia, empresa, reloj):
    marcada = asistencia.marcar_entrada(empresa.ana)
    assert marcada["jornada"] == HOY
    assert marcada["entrada"] == reloj.ahora
    assert marcada["salida"] is None
    assert marcada["estado"] == "REGISTRADA"
    assert marcada["minutos_presente"] == 0


def test_la_entrada_no_se_marca_dos_veces_en_la_jornada(asistencia, empresa, jornada_cerrada):
    with pytest.raises(ValidationError, match="Ya marcaste la entrada"):
        asistencia.marcar_entrada(empresa.ana)


def test_la_entrada_abierta_tampoco_se_repite(asistencia, empresa):
    asistencia.marcar_entrada(empresa.ana)
    with pytest.raises(ValidationError, match="Ya marcaste la entrada"):
        asistencia.marcar_entrada(empresa.ana)


def test_marcar_salida_cierra_la_asistencia(jornada_cerrada, reloj):
    assert jornada_cerrada["salida"] == reloj.ahora
    assert jornada_cerrada["minutos_presente"] == 480


def test_salida_sin_entrada_se_rechaza(asistencia, empresa):
    with pytest.raises(ValidationError, match="marca primero la entrada"):
        asistencia.marcar_salida(empresa.ana)


def test_la_salida_de_un_turno_de_noche_cierra_la_jornada_anterior(asistencia, empresa, reloj):
    reloj.ahora = utc(11, 3)                     # 22:00 del 10 en Bogotá.
    assert asistencia.marcar_entrada(empresa.ana)["jornada"] == HOY
    reloj.ahora = utc(11, 11)                    # 06:00 del 11 en Bogotá.
    cerrada = asistencia.marcar_salida(empresa.ana)
    assert cerrada["jornada"] == HOY
    assert cerrada["minutos_presente"] == 480
    # Cerrada la anterior, ya puede abrir la del 11.
    assert asistencia.marcar_entrada(empresa.ana)["jornada"] == "2026-10-11"


def test_una_salida_pendiente_de_otra_jornada_bloquea_la_entrada(asistencia, empresa, reloj):
    asistencia.marcar_entrada(empresa.ana)
    reloj.avanzar(24 * 60)
    with pytest.raises(ValidationError, match="salida pendiente de la jornada 2026-10-10"):
        asistencia.marcar_entrada(empresa.ana)


def test_el_turno_no_limita_la_entrada(servicios, asistencia, empresa, tarde):
    # Su turno empieza a las 14:00 y marca a las 03:00: se permite.
    servicios.turnos.asignar_turno(empresa.admin, empresa.ana["id"], tarde["id"])
    assert asistencia.marcar_entrada(empresa.ana)["estado"] == "REGISTRADA"


def test_dos_entradas_simultaneas_dejan_una_sola(asistencia, asistencias, empresa, monkeypatch):
    # Las dos peticiones pasan la comprobación del servicio antes de que alguna inserte.
    monkeypatch.setattr(asistencias.__class__, "find_abierta_de_usuario", lambda self, usuario_id: None)
    monkeypatch.setattr(asistencias.__class__, "find_de_usuario_en", lambda self, usuario_id, jornada: None)
    asistencia.marcar_entrada(empresa.ana)
    with pytest.raises(ValidationError, match="Ya marcaste la entrada"):
        asistencia.marcar_entrada(empresa.ana)
    assert asistencias.collection.count_documents({"usuario_id": empresa.ana["id"]}) == 1


def test_el_indice_rechaza_una_segunda_asistencia_de_la_jornada(asistencias):
    documento = {"usuario_id": "u1", "jornada": HOY, "entrada": utc(10, 8), "salida": None}
    assert asistencias.insertar(dict(documento)) is not None
    assert asistencias.insertar(dict(documento)) is None


def test_una_salida_que_otra_peticion_ya_marco_no_se_pisa(asistencia, empresa, reloj, monkeypatch):
    asistencia.marcar_entrada(empresa.ana)
    reloj.avanzar(60)
    monkeypatch.setattr(AsistenciaRepository, "guardar", lambda *args, **kwargs: False)
    with pytest.raises(ValidationError, match="cambió"):
        asistencia.marcar_salida(empresa.ana)


def test_consultar_hoy(asistencia, empresa, reloj):
    assert asistencia.consultar_hoy(empresa.ana) is None
    asistencia.marcar_entrada(empresa.ana)
    reloj.avanzar(90)
    assert asistencia.consultar_hoy(empresa.ana)["minutos_presente"] == 90
    asistencia.marcar_salida(empresa.ana)
    assert asistencia.consultar_hoy(empresa.ana)["salida"] == reloj.ahora


def test_consultar_hoy_trae_la_abierta_de_la_jornada_anterior(asistencia, empresa, reloj):
    reloj.ahora = utc(11, 3)
    asistencia.marcar_entrada(empresa.ana)
    reloj.ahora = utc(11, 8)
    assert asistencia.consultar_hoy(empresa.ana)["jornada"] == HOY


def test_el_administrador_no_marca_asistencia(asistencia, empresa):
    with pytest.raises(ProhibidoError):
        asistencia.marcar_entrada(empresa.admin)


def test_la_programacion_trae_la_asistencia(servicios, asistencia, empresa, reloj):
    marcada = asistencia.marcar_entrada(empresa.ana)
    reloj.avanzar(30)
    en_programacion = servicios.programacion.consultar(empresa.ana)["asistencia"]
    assert en_programacion["id"] == marcada["id"]
    assert en_programacion["minutos_presente"] == 30


# ---------- Revisión del Administrador ----------

def test_validar_una_asistencia(asistencia, empresa, jornada_cerrada, reloj):
    validada = asistencia.validar(empresa.admin, jornada_cerrada["id"])
    assert validada["estado"] == "VALIDADA"
    assert validada["revision"] == {"autor_id": empresa.admin["id"], "fecha": reloj.ahora}


def test_no_se_valida_una_asistencia_abierta(asistencia, empresa):
    abierta = asistencia.marcar_entrada(empresa.ana)
    with pytest.raises(ValidationError):
        asistencia.validar(empresa.admin, abierta["id"])


def test_corregir_exige_motivo(asistencia, empresa, jornada_cerrada):
    with pytest.raises(ValidationError, match="motivo"):
        asistencia.corregir(empresa.admin, jornada_cerrada["id"], "02:50", "11:00", " ")


def test_corregir_conserva_las_marcas_originales(asistencia, asistencias, empresa, jornada_cerrada):
    corregida = asistencia.corregir(empresa.admin, jornada_cerrada["id"], "02:50", "10:30", "Llegó antes")
    assert corregida["estado"] == "CORREGIDA"
    assert corregida["entrada"] == utc(10, 7, 50)
    assert corregida["salida"] == utc(10, 15, 30)
    guardada = asistencias.find_by_id(jornada_cerrada["id"])
    assert en_utc(guardada["revision"]["entrada_original"]) == utc(10, 8)
    assert en_utc(guardada["revision"]["salida_original"]) == utc(10, 16)
    assert guardada["revision"]["motivo"] == "Llegó antes"


def test_una_salida_menor_que_la_entrada_es_del_dia_siguiente(servicios, asistencia, empresa, reloj):
    reloj.ahora = utc(11, 3)
    marcada = asistencia.marcar_entrada(empresa.ana)
    reloj.ahora = utc(11, 12)
    corregida = asistencia.corregir(empresa.admin, marcada["id"], "22:00", "06:00", "Turno de noche")
    assert corregida["entrada"] == utc(11, 3)
    assert corregida["salida"] == utc(11, 11)
    assert corregida["minutos_presente"] == 480


def test_corregir_puede_dejar_la_salida_vacia(asistencia, empresa, jornada_cerrada):
    corregida = asistencia.corregir(empresa.admin, jornada_cerrada["id"], "03:00", None, "Salida marcada por error")
    assert corregida["salida"] is None
    assert corregida["estado"] == "CORREGIDA"


@pytest.mark.parametrize("entrada, salida", [("3 am", "11:00"), ("03:00", "25:00"), ("03:00", "23:00")])
def test_corregir_valida_las_horas(asistencia, empresa, jornada_cerrada, entrada, salida):
    # "23:00" de hoy todavía no ha llegado: una corrección no inventa marcas futuras.
    with pytest.raises(ValidationError):
        asistencia.corregir(empresa.admin, jornada_cerrada["id"], entrada, salida, "Ajuste")


def test_una_revision_que_otra_peticion_cambio_no_se_pisa(asistencia, empresa, jornada_cerrada, monkeypatch):
    monkeypatch.setattr(AsistenciaRepository, "guardar", lambda *args, **kwargs: False)
    with pytest.raises(ValidationError, match="cambió"):
        asistencia.validar(empresa.admin, jornada_cerrada["id"])


def test_una_asistencia_de_otra_empresa_no_existe_para_mi(asistencia, otra_empresa, jornada_cerrada):
    with pytest.raises(NotFoundError):
        asistencia.validar(otra_empresa.admin, jornada_cerrada["id"])


def test_el_operario_no_valida_ni_corrige(asistencia, empresa, jornada_cerrada):
    with pytest.raises(ProhibidoError):
        asistencia.validar(empresa.ana, jornada_cerrada["id"])


def test_la_lista_incluye_a_los_que_no_marcaron(servicios, asistencia, repos, empresa, tarde, reloj):
    for operario in (empresa.ana, empresa.luis):
        servicios.turnos.asignar_turno(empresa.admin, operario["id"], tarde["id"])
    repos.usuarios.insert({"nombre": "Pedro", "correo": "pedro@prueba.co", "rol": "OPERARIO",
                           "empresa_id": empresa.id})           # Sin turno ni marca: no se espera.
    asistencia.marcar_entrada(empresa.ana)
    reloj.avanzar(60)

    filas = {fila["operario"]: fila for fila in asistencia.listar(empresa.admin)}
    assert sorted(filas) == ["Ana", "Luis"]
    assert filas["Ana"]["estado"] == "REGISTRADA"
    assert filas["Ana"]["minutos_presente"] == 60
    assert filas["Ana"]["turno"]["nombre"] == "Tarde"
    assert filas["Luis"]["estado"] == "SIN_MARCA"
    assert filas["Luis"]["id"] is None
    assert filas["Luis"]["usuario_id"] == empresa.luis["id"]


def test_la_lista_muestra_a_quien_marco_sin_turno(asistencia, empresa):
    asistencia.marcar_entrada(empresa.luis)
    filas = asistencia.listar(empresa.admin, HOY)
    assert [(fila["operario"], fila["turno"]) for fila in filas] == [("Luis", None)]


def test_la_lista_es_por_jornada(asistencia, empresa, jornada_cerrada):
    assert asistencia.listar(empresa.admin, "2026-10-09") == []
    assert len(asistencia.listar(empresa.admin, HOY)) == 1


def test_la_lista_valida_la_jornada(asistencia, empresa):
    with pytest.raises(ValidationError):
        asistencia.listar(empresa.admin, "ayer")


def test_el_operario_no_ve_la_lista(asistencia, empresa):
    with pytest.raises(ProhibidoError):
        asistencia.listar(empresa.ana)


# ---------- Por la API ----------

def test_la_api_del_operario(cliente_de, empresa, reloj):
    ana = cliente_de(empresa.ana)
    assert ana.get("/asistencia/hoy").get_json() is None
    assert ana.post("/asistencia/salida", headers=PROPIA).status_code == 400

    entrada = ana.post("/asistencia/entrada", headers=PROPIA)
    assert entrada.status_code == 201
    assert entrada.get_json()["entrada"] == "Sat, 10 Oct 2026 08:00:00 GMT"
    assert ana.post("/asistencia/entrada", headers=PROPIA).status_code == 400

    reloj.avanzar(60)
    salida = ana.post("/asistencia/salida", headers=PROPIA)
    assert salida.status_code == 200
    assert salida.get_json()["minutos_presente"] == 60
    assert ana.get("/asistencia/hoy").get_json()["salida"] == "Sat, 10 Oct 2026 09:00:00 GMT"


def test_la_api_del_administrador(cliente_de, empresa, reloj):
    ana = cliente_de(empresa.ana)
    asistencia_id = ana.post("/asistencia/entrada", headers=PROPIA).get_json()["id"]
    reloj.avanzar(120)
    ana.post("/asistencia/salida", headers=PROPIA)

    marta = cliente_de(empresa.admin)
    filas = marta.get(f"/asistencias?jornada={HOY}").get_json()
    assert [fila["operario"] for fila in filas] == ["Ana"]
    assert marta.get("/asistencias").get_json() == filas
    assert marta.get("/asistencias?jornada=10-10-2026").status_code == 400

    corregir = f"/asistencias/{asistencia_id}/corregir"
    assert marta.post(corregir, json={"entrada": "03:00", "salida": "04:30"}, headers=PROPIA).status_code == 400
    corregida = marta.post(corregir, json={"entrada": "03:00", "salida": "04:30", "motivo": "Ajuste"}, headers=PROPIA)
    assert corregida.get_json()["minutos_presente"] == 90
    assert marta.post(f"/asistencias/{asistencia_id}/validar", headers=PROPIA).get_json()["estado"] == "VALIDADA"
    assert marta.post("/asistencias/no-existe/validar", headers=PROPIA).status_code == 404


def test_la_api_protege_cada_rol(cliente_de, empresa):
    ana, marta = cliente_de(empresa.ana), cliente_de(empresa.admin)
    asistencia_id = ana.post("/asistencia/entrada", headers=PROPIA).get_json()["id"]
    assert ana.get("/asistencias").status_code == 403
    assert ana.post(f"/asistencias/{asistencia_id}/validar", headers=PROPIA).status_code == 403
    assert ana.post(f"/asistencias/{asistencia_id}/corregir", headers=PROPIA).status_code == 403
    assert marta.post("/asistencia/entrada", headers=PROPIA).status_code == 403
    assert cliente_de(None).get("/asistencia/hoy").status_code == 401


def test_la_api_de_programacion_trae_turno_asistencia_y_en_turno(cliente_de, servicios, empresa):
    madrugada = servicios.turnos.crear_turno(
        {"nombre": "Madrugada", "hora_inicio": "02:00", "hora_fin": "10:00", "descanso_min": 30}, empresa.admin)
    servicios.turnos.asignar_turno(empresa.admin, empresa.ana["id"], madrugada["id"])
    ana = cliente_de(empresa.ana)
    ana.post("/asistencia/entrada", headers=PROPIA)

    programacion = ana.get("/programacion-del-dia").get_json()
    assert programacion["turno"]["inicio"] == "Sat, 10 Oct 2026 07:00:00 GMT"
    assert programacion["turno"]["fin"] == "Sat, 10 Oct 2026 15:00:00 GMT"
    assert programacion["asistencia"]["estado"] == "REGISTRADA"
    assert programacion["en_turno"] is True
