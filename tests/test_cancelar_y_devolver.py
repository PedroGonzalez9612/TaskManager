"""Pruebas de cancelar una actividad (Administrador) y devolver una actividad (Operario): alcance, Sección 5.1."""
import pytest

from app.utils.errors import NotFoundError, ProhibidoError, ValidationError

HOY = "2026-10-10"    # La fecha programada de las actividades que crea conftest.py.


def ver(servicios, actividad, solicitante):
    return servicios.actividades.obtener_actividad(actividad["id"], solicitante)


def reasignar(servicios, empresa, actividad, operarios):
    datos = {"operario_ids": [operario["id"] for operario in operarios]}
    return servicios.actividades.actualizar_actividad(actividad["id"], datos, empresa.admin)


def minutos_de(servicios, empresa, operario):
    carga = servicios.carga.consultar(HOY, HOY, empresa.admin)
    fila = next(o for o in carga["operarios"] if o["id"] == operario["id"])
    return sum(jornada["minutos"] for jornada in fila["jornadas"])


# ---------- Cancelar ----------

def test_la_cancelada_queda_consultable_con_motivo_autor_y_fecha(servicios, repos, empresa, crear_actividad, reloj):
    actividad = crear_actividad([empresa.ana])
    reloj.avanzar(15)

    vista = servicios.actividades.cancelar(actividad["id"], empresa.admin, "Otro", "Pedido anulado")

    assert vista["estado"] == vista["estado_general"] == "CANCELADA"
    assert vista["cancelacion"] == {
        "motivo": "Pedido anulado",
        "autor_id": empresa.admin["id"],
        "autor_nombre": "Marta",
        "fecha": reloj.ahora.replace(tzinfo=None),    # Mongo guarda las fechas sin zona.
    }
    # No se borra: sigue en la base de datos y en el listado del Administrador.
    assert repos.actividades.find_by_id(actividad["id"])["titulo"] == actividad["titulo"]
    assert [a["estado"] for a in servicios.actividades.listar_actividades({}, empresa.admin)] == ["CANCELADA"]


def test_cancelar_exige_motivo(servicios, empresa, crear_actividad):
    actividad = crear_actividad([empresa.ana])

    for motivo, detalle in ((None, None), ("  ", None), ("Otro", None), ("Otro", " ")):
        with pytest.raises(ValidationError):
            servicios.actividades.cancelar(actividad["id"], empresa.admin, motivo, detalle)

    assert ver(servicios, actividad, empresa.admin)["estado"] == "ASIGNADA"
    assert ver(servicios, actividad, empresa.admin)["cancelacion"] is None


def test_no_se_cancela_lo_que_alguien_tiene_en_curso(servicios, empresa, crear_actividad):
    actividad = crear_actividad([empresa.ana, empresa.luis])
    servicios.ejecucion.iniciar(actividad["id"], empresa.ana)

    with pytest.raises(ValidationError):
        servicios.actividades.cancelar(actividad["id"], empresa.admin, "Pedido anulado")

    assert ver(servicios, actividad, empresa.admin)["estado"] == "EN_EJECUCION"
    assert ver(servicios, actividad, empresa.ana)["ejecucion"]["estado"] == "EN_PROGRESO"


def test_se_cancela_una_pausada_y_su_ejecucion_queda_cerrada(servicios, repos, empresa, crear_actividad, reloj):
    actividad = crear_actividad([empresa.ana])
    servicios.ejecucion.iniciar(actividad["id"], empresa.ana)
    reloj.avanzar(20)
    servicios.ejecucion.pausar(actividad["id"], empresa.ana, "Falta material")
    reloj.avanzar(40)

    vista = servicios.actividades.cancelar(actividad["id"], empresa.admin, "Pedido anulado")

    assert vista["estado"] == "CANCELADA"
    ejecucion = repos.ejecuciones.find_by_actividades([actividad["id"]])[0]
    assert ejecucion["estado"] == "CERRADA"
    assert ejecucion["fecha_fin"] == reloj.ahora.replace(tzinfo=None)
    assert ejecucion["pausas"][0]["fin"] == reloj.ahora.replace(tzinfo=None)
    assert vista["tiempo_real_min"] == 20    # El tiempo trabajado se conserva.
    # Ana queda libre y ya no puede seguir con la cancelada.
    with pytest.raises(ValidationError):
        servicios.ejecucion.reanudar(actividad["id"], empresa.ana)


def test_no_se_cancela_dos_veces_ni_una_finalizada(servicios, empresa, crear_actividad):
    cancelada = crear_actividad([])
    servicios.actividades.cancelar(cancelada["id"], empresa.admin, "Pedido anulado")
    with pytest.raises(ValidationError):
        servicios.actividades.cancelar(cancelada["id"], empresa.admin, "Otra razón")
    assert ver(servicios, cancelada, empresa.admin)["cancelacion"]["motivo"] == "Pedido anulado"

    finalizada = crear_actividad([empresa.ana])
    servicios.ejecucion.iniciar(finalizada["id"], empresa.ana)
    servicios.ejecucion.finalizar(finalizada["id"], empresa.ana)
    with pytest.raises(ValidationError):
        servicios.actividades.cancelar(finalizada["id"], empresa.admin, "Pedido anulado")


def test_una_cancelada_no_se_edita_ni_se_inicia(servicios, empresa, crear_actividad):
    actividad = crear_actividad([empresa.ana])
    servicios.actividades.cancelar(actividad["id"], empresa.admin, "Pedido anulado")

    with pytest.raises(ValidationError):
        reasignar(servicios, empresa, actividad, [empresa.luis])
    with pytest.raises(ValidationError):
        servicios.ejecucion.iniciar(actividad["id"], empresa.ana)
    with pytest.raises(ValidationError):
        servicios.ejecucion.devolver(actividad["id"], empresa.ana, "Falta información")


def test_la_cancelada_no_suma_a_la_carga_y_el_operario_la_sigue_viendo(servicios, empresa, crear_actividad):
    actividad = crear_actividad([empresa.ana], tiempo_estimado_min=90)
    crear_actividad([empresa.ana], titulo="Limpiar la banda", tiempo_estimado_min=30)
    assert minutos_de(servicios, empresa, empresa.ana) == 120

    servicios.actividades.cancelar(actividad["id"], empresa.admin, "Pedido anulado")

    assert minutos_de(servicios, empresa, empresa.ana) == 30
    estados = {a["titulo"]: a["estado"] for a in servicios.actividades.listar_actividades({}, empresa.ana)}
    assert estados == {"Calibrar la selladora": "CANCELADA", "Limpiar la banda": "ASIGNADA"}
    de_ana = ver(servicios, actividad, empresa.ana)
    assert de_ana["cancelacion"]["motivo"] == "Pedido anulado"
    assert de_ana["cancelacion"]["autor_nombre"] == "Marta"


def test_si_la_actividad_cambia_mientras_se_cancela_no_se_aplica(servicios, repos, empresa, crear_actividad, monkeypatch):
    """Un operario la inicia justo después de que el servicio la leyó: el guardado condicionado no entra."""
    actividad = crear_actividad([empresa.ana])
    leer = repos.actividades.find_by_id.__func__

    def leer_y_luego_cambiar(self, actividad_id):
        doc = leer(self, actividad_id)
        self.collection.update_one({"_id": doc["_id"]}, {"$set": {"estado": "EN_EJECUCION"}})
        return doc

    monkeypatch.setattr(type(repos.actividades), "find_by_id", leer_y_luego_cambiar)
    with pytest.raises(ValidationError) as error:
        servicios.actividades.cancelar(actividad["id"], empresa.admin, "Otro", "Pedido anulado")
    monkeypatch.undo()

    assert "cambió mientras la cancelabas" in str(error.value)
    guardada = repos.actividades.find_by_id(actividad["id"])
    assert guardada["estado"] == "EN_EJECUCION"
    assert guardada.get("cancelacion") is None
    assert servicios.catalogos.listar(empresa.admin, "MOTIVO_CANCELACION") == ["Otro"]


def test_no_se_cancela_la_actividad_de_otra_empresa(servicios, empresa, otra_empresa, crear_actividad):
    actividad = crear_actividad([])
    with pytest.raises(NotFoundError):
        servicios.actividades.cancelar(actividad["id"], otra_empresa.admin, "Pedido anulado")
    assert ver(servicios, actividad, empresa.admin)["estado"] == "PENDIENTE"


def test_ruta_de_cancelar_solo_para_el_administrador(cliente_de, empresa, otra_empresa, crear_actividad):
    actividad = crear_actividad([empresa.ana])
    ruta = f"/actividades/{actividad['id']}/cancelar"
    cuerpo = {"motivo": "Otro", "detalle": "Pedido anulado"}

    assert cliente_de().post(ruta, json=cuerpo).status_code == 401
    assert cliente_de(empresa.ana).post(ruta, json=cuerpo).status_code == 403
    assert cliente_de(otra_empresa.admin).post(ruta, json=cuerpo).status_code == 404
    admin = cliente_de(empresa.admin)
    assert admin.post(ruta).status_code == 400
    assert admin.post(ruta, json={"motivo": "Otro"}).status_code == 400

    cancelada = admin.post(ruta, json=cuerpo)
    assert cancelada.status_code == 200
    assert cancelada.get_json()["estado"] == "CANCELADA"
    assert cancelada.get_json()["cancelacion"]["motivo"] == "Pedido anulado"
    assert cancelada.get_json()["cancelacion"]["autor_nombre"] == "Marta"
    assert admin.post(ruta, json=cuerpo).status_code == 400    # No se cancela dos veces.
    assert admin.get("/catalogos/motivos-cancelacion").get_json() == ["Pedido anulado", "Otro"]


# ---------- Devolver ----------

def test_con_dos_asignados_sale_solo_el_que_devuelve(servicios, repos, empresa, crear_actividad, reloj):
    actividad = crear_actividad([empresa.ana, empresa.luis])
    reloj.avanzar(10)

    constancia = servicios.ejecucion.devolver(actividad["id"], empresa.luis, "Me la asignaron por error")

    assert constancia == {
        "actividad_id": actividad["id"], "devuelta": True,
        "motivo": "Me la asignaron por error", "fecha": reloj.ahora,
    }
    vista = ver(servicios, actividad, empresa.admin)
    assert vista["estado"] == "ASIGNADA"
    assert [operario["nombre"] for operario in vista["operarios"]] == ["Ana"]
    assert vista["devoluciones"] == [{
        "operario_id": empresa.luis["id"], "operario_nombre": "Luis",
        "motivo": "Me la asignaron por error", "fecha": reloj.ahora.replace(tzinfo=None),
    }]
    # La asignación no se borra: queda cerrada, como historial.
    historial = repos.asignaciones.find_by_actividad(actividad["id"], incluir_historial=True)
    assert sorted(a["estado"] for a in historial) == ["ACTIVA", "DEVUELTA"]
    # Ana sigue con la actividad como si nada.
    assert servicios.ejecucion.iniciar(actividad["id"], empresa.ana)["estado"] == "EN_EJECUCION"


def test_si_devuelve_el_unico_asignado_vuelve_al_administrador(servicios, empresa, crear_actividad):
    actividad = crear_actividad([empresa.ana])

    servicios.ejecucion.devolver(actividad["id"], empresa.ana, "Otro", "No tengo el curso de alturas")

    vista = ver(servicios, actividad, empresa.admin)
    assert vista["estado"] == "DEVUELTA"
    assert vista["operarios"] == []
    assert vista["total_asignados"] == 0
    assert vista["devoluciones"][0]["motivo"] == "No tengo el curso de alturas"
    assert vista["devoluciones"][0]["operario_nombre"] == "Ana"


def test_el_que_devolvio_ya_no_la_ve_ni_le_suma_a_la_carga(servicios, empresa, crear_actividad):
    actividad = crear_actividad([empresa.ana, empresa.luis])
    servicios.ejecucion.devolver(actividad["id"], empresa.luis, "Falta información")

    assert servicios.actividades.listar_actividades({}, empresa.luis) == []
    with pytest.raises(ProhibidoError):
        ver(servicios, actividad, empresa.luis)
    with pytest.raises(ProhibidoError):
        servicios.ejecucion.iniciar(actividad["id"], empresa.luis)
    with pytest.raises(ProhibidoError):    # No se devuelve dos veces.
        servicios.ejecucion.devolver(actividad["id"], empresa.luis, "Falta información")
    assert minutos_de(servicios, empresa, empresa.luis) == 0
    assert minutos_de(servicios, empresa, empresa.ana) == 60
    # El compañero no ve por qué la devolvió el otro: eso es para el Administrador.
    assert ver(servicios, actividad, empresa.ana)["devoluciones"] == []


def test_al_reasignarla_vuelve_a_asignada_y_conserva_la_devolucion(servicios, empresa, crear_actividad, reloj):
    actividad = crear_actividad([empresa.ana])
    servicios.ejecucion.devolver(actividad["id"], empresa.ana, "Falta herramienta o material")
    # Editar otro campo, o dejarla sin operarios, no la saca de DEVUELTA.
    assert servicios.actividades.actualizar_actividad(
        actividad["id"], {"titulo": "Calibrar"}, empresa.admin)["estado"] == "DEVUELTA"
    assert reasignar(servicios, empresa, actividad, [])["estado"] == "DEVUELTA"

    reloj.avanzar(30)
    vista = reasignar(servicios, empresa, actividad, [empresa.luis])

    assert vista["estado"] == "ASIGNADA"
    assert [operario["nombre"] for operario in vista["operarios"]] == ["Luis"]
    assert [(d["operario_nombre"], d["motivo"]) for d in vista["devoluciones"]] == [
        ("Ana", "Falta herramienta o material"),
    ]
    assert servicios.ejecucion.iniciar(actividad["id"], empresa.luis)["estado"] == "EN_EJECUCION"


def test_se_le_puede_volver_a_asignar_a_quien_la_devolvio(servicios, empresa, crear_actividad, reloj):
    actividad = crear_actividad([empresa.ana])
    servicios.ejecucion.devolver(actividad["id"], empresa.ana, "Falta información")
    reloj.avanzar(5)
    reasignar(servicios, empresa, actividad, [empresa.ana])
    reloj.avanzar(5)
    servicios.ejecucion.devolver(actividad["id"], empresa.ana, "El equipo no está disponible")

    vista = ver(servicios, actividad, empresa.admin)
    assert vista["estado"] == "DEVUELTA"
    assert [d["motivo"] for d in vista["devoluciones"]] == ["Falta información", "El equipo no está disponible"]


def test_solo_se_devuelve_antes_de_iniciar(servicios, empresa, crear_actividad):
    actividad = crear_actividad([empresa.ana])
    servicios.ejecucion.iniciar(actividad["id"], empresa.ana)

    with pytest.raises(ValidationError) as error:
        servicios.ejecucion.devolver(actividad["id"], empresa.ana, "Falta información")
    assert "antes de iniciarla" in str(error.value)

    servicios.ejecucion.pausar(actividad["id"], empresa.ana, "Falta material")
    with pytest.raises(ValidationError):
        servicios.ejecucion.devolver(actividad["id"], empresa.ana, "Falta información")
    assert ver(servicios, actividad, empresa.ana)["estado"] == "PAUSADA"


def test_puede_devolver_quien_no_ha_iniciado_aunque_el_companero_si(servicios, empresa, crear_actividad):
    actividad = crear_actividad([empresa.ana, empresa.luis])
    servicios.ejecucion.iniciar(actividad["id"], empresa.ana)

    servicios.ejecucion.devolver(actividad["id"], empresa.luis, "Me la asignaron por error")

    assert ver(servicios, actividad, empresa.admin)["estado"] == "EN_EJECUCION"
    assert servicios.ejecucion.finalizar(actividad["id"], empresa.ana)["estado_general"] == "COMPLETADA"


def test_devolver_exige_motivo(servicios, empresa, crear_actividad):
    actividad = crear_actividad([empresa.ana])

    for motivo, detalle in ((None, None), (" ", None), ("Otro", None), ("otro", "  ")):
        with pytest.raises(ValidationError):
            servicios.ejecucion.devolver(actividad["id"], empresa.ana, motivo, detalle)

    assert ver(servicios, actividad, empresa.ana)["estado"] == "ASIGNADA"
    assert ver(servicios, actividad, empresa.admin)["devoluciones"] == []


def test_ruta_de_devolver_solo_para_el_operario_asignado(cliente_de, empresa, otra_empresa, crear_actividad):
    actividad = crear_actividad([empresa.ana])
    ruta = f"/actividades/{actividad['id']}/devolver"
    cuerpo = {"motivo": "Falta información"}

    assert cliente_de().post(ruta, json=cuerpo).status_code == 401
    assert cliente_de(empresa.admin).post(ruta, json=cuerpo).status_code == 403
    assert cliente_de(empresa.luis).post(ruta, json=cuerpo).status_code == 403    # No la tiene asignada.
    assert cliente_de(otra_empresa.ivan).post(ruta, json=cuerpo).status_code == 404
    ana = cliente_de(empresa.ana)
    assert ana.post(ruta).status_code == 400
    assert ana.post(ruta, json={"motivo": "Otro"}).status_code == 400

    devuelta = ana.post(ruta, json=cuerpo)
    assert devuelta.status_code == 200
    assert devuelta.get_json()["motivo"] == "Falta información"
    assert ana.get("/actividades").get_json() == []
    del_admin = cliente_de(empresa.admin).get(f"/actividades/{actividad['id']}").get_json()
    assert del_admin["estado"] == "DEVUELTA"
    assert del_admin["devoluciones"][0]["operario_nombre"] == "Ana"


# ---------- Asignar ----------

def test_si_la_base_rechaza_una_asignacion_repetida_no_falla(servicios, repos, empresa, crear_actividad, monkeypatch):
    """Dos administradores asignan al mismo operario a la vez: el segundo intenta insertar una
    asignación que ya existe. Se simula ocultándole al servicio las asignaciones activas."""
    actividad = crear_actividad([empresa.ana])
    buscar = repos.asignaciones.find_by_actividad.__func__
    llamadas = []

    def vacio_la_primera_vez(self, actividad_id, incluir_historial=False):
        llamadas.append(actividad_id)
        return [] if len(llamadas) == 1 else buscar(self, actividad_id, incluir_historial)

    monkeypatch.setattr(type(repos.asignaciones), "find_by_actividad", vacio_la_primera_vez)
    vista = reasignar(servicios, empresa, actividad, [empresa.ana])
    monkeypatch.undo()

    assert vista["estado"] == "ASIGNADA"
    assert len(repos.asignaciones.find_by_actividad(actividad["id"], incluir_historial=True)) == 1
