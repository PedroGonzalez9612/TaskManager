"""Pruebas de ActividadService y CargaService: las asignaciones no se borran, se retiran."""
import pytest

from app.utils.errors import ProhibidoError, ValidationError

HOY = "2026-10-10"    # La fecha programada de las actividades que crea conftest.py.


def reasignar(servicios, empresa, actividad, operarios):
    datos = {"operario_ids": [operario["id"] for operario in operarios]}
    return servicios.actividades.actualizar_actividad(actividad["id"], datos, empresa.admin)


def asignaciones_por_usuario(repos, actividad):
    historial = repos.asignaciones.find_by_actividad(actividad["id"], incluir_historial=True)
    return {asignacion["usuario_id"]: asignacion for asignacion in historial}


def test_quitar_un_operario_no_borra_su_asignacion(servicios, repos, empresa, crear_actividad, reloj):
    actividad = crear_actividad([empresa.ana, empresa.luis])
    antes = asignaciones_por_usuario(repos, actividad)

    reloj.avanzar(30)
    vista = reasignar(servicios, empresa, actividad, [empresa.ana])

    despues = asignaciones_por_usuario(repos, actividad)
    assert len(despues) == 2
    de_luis = despues[empresa.luis["id"]]
    assert de_luis["estado"] == "RETIRADA"
    assert de_luis["retirada_por_id"] == empresa.admin["id"]
    assert de_luis["fecha_fin"] == reloj.ahora.replace(tzinfo=None)    # Mongo guarda las fechas sin zona.

    de_ana = despues[empresa.ana["id"]]
    assert de_ana["estado"] == "ACTIVA"
    assert de_ana["_id"] == antes[empresa.ana["id"]]["_id"]
    assert de_ana["fecha_asignacion"] == antes[empresa.ana["id"]]["fecha_asignacion"]
    assert de_ana["asignada_por_id"] == empresa.admin["id"]

    assert [operario["nombre"] for operario in vista["operarios"]] == ["Ana"]
    assert vista["total_asignados"] == 1


def test_el_retirado_ya_no_ve_la_actividad_ni_puede_iniciarla(servicios, empresa, crear_actividad):
    actividad = crear_actividad([empresa.ana, empresa.luis])
    reasignar(servicios, empresa, actividad, [empresa.ana])

    assert servicios.actividades.listar_actividades({}, empresa.luis) == []
    with pytest.raises(ProhibidoError):
        servicios.actividades.obtener_actividad(actividad["id"], empresa.luis)
    with pytest.raises(ProhibidoError):
        servicios.ejecucion.iniciar(actividad["id"], empresa.luis)


def test_al_retirar_a_quien_la_tenia_abierta_su_ejecucion_queda_cerrada(
        servicios, repos, empresa, crear_actividad, reloj):
    actividad = crear_actividad([empresa.ana, empresa.luis])
    servicios.ejecucion.iniciar(actividad["id"], empresa.luis)
    reloj.avanzar(12)

    vista = reasignar(servicios, empresa, actividad, [empresa.ana])

    ejecucion = repos.ejecuciones.find_by_actividades([actividad["id"]])[0]
    assert ejecucion["estado"] == "CERRADA"
    assert ejecucion["fecha_fin"] == reloj.ahora.replace(tzinfo=None)
    assert vista["estado"] == "ASIGNADA"       # Ana sigue sin iniciar.
    assert vista["ejecuciones"] == []          # La del retirado queda en el historial, no en la vista.
    # Luis queda libre para iniciar otra actividad.
    otra = crear_actividad([empresa.luis], titulo="Limpiar la banda")
    assert servicios.ejecucion.iniciar(otra["id"], empresa.luis)["estado"] == "EN_EJECUCION"


def test_volver_a_asignar_crea_una_asignacion_nueva(servicios, repos, empresa, crear_actividad):
    actividad = crear_actividad([empresa.ana, empresa.luis])
    reasignar(servicios, empresa, actividad, [empresa.ana])
    reasignar(servicios, empresa, actividad, [empresa.ana, empresa.luis])

    historial = repos.asignaciones.find_by_actividad(actividad["id"], incluir_historial=True)
    de_luis = sorted(a["estado"] for a in historial if a["usuario_id"] == empresa.luis["id"])
    assert de_luis == ["ACTIVA", "RETIRADA"]
    assert servicios.ejecucion.iniciar(actividad["id"], empresa.luis)["estado"] == "EN_EJECUCION"


def test_el_estado_sigue_a_las_asignaciones(servicios, empresa, crear_actividad):
    actividad = crear_actividad([])
    assert actividad["estado"] == "PENDIENTE"
    assert reasignar(servicios, empresa, actividad, [empresa.ana])["estado"] == "ASIGNADA"
    assert reasignar(servicios, empresa, actividad, [])["estado"] == "PENDIENTE"


def test_editar_sin_tocar_operarios_no_cambia_las_asignaciones(servicios, repos, empresa, crear_actividad):
    actividad = crear_actividad([empresa.ana])
    vista = servicios.actividades.actualizar_actividad(actividad["id"], {"titulo": "Otro título"}, empresa.admin)

    assert vista["titulo"] == "Otro título"
    assert len(repos.asignaciones.find_by_actividad(actividad["id"], incluir_historial=True)) == 1


def test_no_se_edita_una_actividad_en_estado_final(servicios, repos, empresa, crear_actividad):
    actividad = crear_actividad([empresa.ana])
    servicios.ejecucion.iniciar(actividad["id"], empresa.ana)
    servicios.ejecucion.finalizar(actividad["id"], empresa.ana)

    with pytest.raises(ValidationError):
        servicios.actividades.actualizar_actividad(actividad["id"], {"titulo": "Otro"}, empresa.admin)
    with pytest.raises(ValidationError):
        reasignar(servicios, empresa, actividad, [empresa.luis])

    assert repos.actividades.find_by_id(actividad["id"])["titulo"] == actividad["titulo"]
    assert list(asignaciones_por_usuario(repos, actividad)) == [empresa.ana["id"]]


# ---------- Carga ----------

def minutos_de(carga, operario):
    fila = next(o for o in carga["operarios"] if o["id"] == operario["id"])
    return sum(jornada["minutos"] for jornada in fila["jornadas"])


def test_la_carga_no_cuenta_al_operario_retirado(servicios, empresa, crear_actividad):
    actividad = crear_actividad([empresa.ana, empresa.luis])
    reasignar(servicios, empresa, actividad, [empresa.ana])

    carga = servicios.carga.consultar(HOY, HOY, empresa.admin)
    assert minutos_de(carga, empresa.ana) == 60
    assert minutos_de(carga, empresa.luis) == 0


def test_la_carga_no_cuenta_las_canceladas_pero_si_las_no_realizadas(servicios, repos, empresa, crear_actividad):
    cancelada = crear_actividad([empresa.ana], titulo="Cancelada", tiempo_estimado_min=30)
    no_realizada = crear_actividad([empresa.ana], titulo="No realizada", tiempo_estimado_min=45)
    crear_actividad([empresa.ana], titulo="Normal", tiempo_estimado_min=60)
    # Cancelar y "no realizada" se construyen en un paso posterior: aquí el estado se pone directamente.
    repos.actividades.update(cancelada["id"], {"estado": "CANCELADA"})
    repos.actividades.update(no_realizada["id"], {"estado": "NO_REALIZADA"})

    carga = servicios.carga.consultar(HOY, HOY, empresa.admin)
    assert minutos_de(carga, empresa.ana) == 105
