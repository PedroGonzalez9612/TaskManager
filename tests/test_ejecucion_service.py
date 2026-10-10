"""Pruebas de EjecucionService: cada operario tiene su propia ejecución (alcance, Sección 5.1)."""
import pytest

from app.utils.errors import NotFoundError, ProhibidoError, ValidationError


def ver(servicios, actividad, solicitante):
    return servicios.actividades.obtener_actividad(actividad["id"], solicitante)


# ---------- Una sola actividad en curso por operario ----------

def test_la_ejecucion_de_un_companero_no_bloquea_al_otro(servicios, empresa, crear_actividad):
    compartida = crear_actividad([empresa.ana, empresa.luis])
    otra = crear_actividad([empresa.luis], titulo="Limpiar la banda")

    servicios.ejecucion.iniciar(compartida["id"], empresa.ana)
    vista = servicios.ejecucion.iniciar(otra["id"], empresa.luis)

    assert vista["estado"] == "EN_EJECUCION"
    assert ver(servicios, compartida, empresa.luis)["estado"] == "ASIGNADA"


def test_no_se_inicia_otra_con_una_en_curso_y_el_mensaje_la_nombra(servicios, empresa, crear_actividad):
    primera = crear_actividad([empresa.ana], titulo="Calibrar la selladora")
    segunda = crear_actividad([empresa.ana], titulo="Limpiar la banda")
    servicios.ejecucion.iniciar(primera["id"], empresa.ana)

    with pytest.raises(ValidationError) as error:
        servicios.ejecucion.iniciar(segunda["id"], empresa.ana)

    assert primera["codigo"] in str(error.value)
    assert "Calibrar la selladora" in str(error.value)
    assert ver(servicios, segunda, empresa.ana)["ejecucion"] is None


def test_no_se_reanuda_con_otra_en_curso(servicios, empresa, crear_actividad):
    primera = crear_actividad([empresa.ana], titulo="Calibrar la selladora")
    segunda = crear_actividad([empresa.ana], titulo="Limpiar la banda")
    servicios.ejecucion.iniciar(primera["id"], empresa.ana)
    servicios.ejecucion.pausar(primera["id"], empresa.ana, "Actividad urgente")
    servicios.ejecucion.iniciar(segunda["id"], empresa.ana)

    with pytest.raises(ValidationError) as error:
        servicios.ejecucion.reanudar(primera["id"], empresa.ana)

    assert "Limpiar la banda" in str(error.value)
    assert ver(servicios, primera, empresa.ana)["estado"] == "PAUSADA"

    servicios.ejecucion.finalizar(segunda["id"], empresa.ana)
    assert servicios.ejecucion.reanudar(primera["id"], empresa.ana)["estado"] == "EN_EJECUCION"


def test_la_base_de_datos_rechaza_la_segunda_en_curso_aunque_se_salte_la_comprobacion(
        servicios, repos, empresa, crear_actividad, monkeypatch):
    """Dos peticiones a la vez pasan ambas la comprobación previa: aquí se simula anulándola, y es
    el índice único el que deja una sola ejecución en curso."""
    primera = crear_actividad([empresa.ana], titulo="Calibrar la selladora")
    segunda = crear_actividad([empresa.ana], titulo="Limpiar la banda")
    servicios.ejecucion.iniciar(primera["id"], empresa.ana)

    comprobacion = servicios.ejecucion._exigir_sin_otra_en_curso
    llamadas = []

    def solo_la_segunda_vez(solicitante, accion):
        llamadas.append(accion)
        if len(llamadas) > 1:
            comprobacion(solicitante, accion)

    monkeypatch.setattr(servicios.ejecucion, "_exigir_sin_otra_en_curso", solo_la_segunda_vez)
    with pytest.raises(ValidationError) as error:
        servicios.ejecucion.iniciar(segunda["id"], empresa.ana)

    assert "Calibrar la selladora" in str(error.value)
    assert len(repos.ejecuciones.find_abiertas_de_usuario(empresa.ana["id"])) == 1


# ---------- Pausas ----------

def test_pausar_exige_motivo(servicios, empresa, crear_actividad):
    actividad = crear_actividad([empresa.ana])
    servicios.ejecucion.iniciar(actividad["id"], empresa.ana)

    for motivo in (None, "", "   "):
        with pytest.raises(ValidationError):
            servicios.ejecucion.pausar(actividad["id"], empresa.ana, motivo)

    assert ver(servicios, actividad, empresa.ana)["estado"] == "EN_EJECUCION"


def test_una_actividad_de_hora_fija_no_se_pausa(servicios, empresa, crear_actividad):
    actividad = crear_actividad([empresa.ana], hora_programada="10:00")
    servicios.ejecucion.iniciar(actividad["id"], empresa.ana)

    with pytest.raises(ValidationError, match="hora fija"):
        servicios.ejecucion.pausar(actividad["id"], empresa.ana, "Actividad urgente")

    vista = ver(servicios, actividad, empresa.ana)
    assert vista["estado"] == "EN_EJECUCION"
    assert vista["ejecucion"]["pausas"] == []


def test_pausar_y_reanudar_deja_la_pausa_cerrada_y_el_tiempo_la_descuenta(
        servicios, empresa, crear_actividad, reloj):
    actividad = crear_actividad([empresa.ana])
    servicios.ejecucion.iniciar(actividad["id"], empresa.ana)

    reloj.avanzar(10)
    pausada = servicios.ejecucion.pausar(actividad["id"], empresa.ana, "  Falta material  ")
    assert pausada["estado"] == "PAUSADA"
    assert pausada["ejecucion"]["pausas"][0]["fin"] is None

    reloj.avanzar(15)    # Pausada: este tiempo no cuenta.
    assert ver(servicios, actividad, empresa.ana)["ejecucion"]["tiempo_real_min"] == 10

    reanudada = servicios.ejecucion.reanudar(actividad["id"], empresa.ana)
    reloj.avanzar(20)
    final = servicios.ejecucion.finalizar(actividad["id"], empresa.ana)

    assert reanudada["estado"] == "EN_EJECUCION"
    pausa = final["ejecucion"]["pausas"][0]
    assert pausa["motivo"] == "Falta material"
    assert pausa["fin"] is not None
    assert final["ejecucion"]["tiempo_real_min"] == 30    # 45 minutos menos 15 de pausa.
    assert final["tiempo_real_min"] == 30


def test_no_se_pausa_ni_finaliza_lo_que_no_se_ha_iniciado(servicios, empresa, crear_actividad):
    actividad = crear_actividad([empresa.ana])
    with pytest.raises(ValidationError):
        servicios.ejecucion.pausar(actividad["id"], empresa.ana, "Falta material")
    with pytest.raises(ValidationError):
        servicios.ejecucion.reanudar(actividad["id"], empresa.ana)
    with pytest.raises(ValidationError):
        servicios.ejecucion.finalizar(actividad["id"], empresa.ana)


def test_iniciar_una_pausada_pide_reanudarla(servicios, empresa, crear_actividad):
    actividad = crear_actividad([empresa.ana])
    servicios.ejecucion.iniciar(actividad["id"], empresa.ana)
    servicios.ejecucion.pausar(actividad["id"], empresa.ana, "Falta material")

    with pytest.raises(ValidationError, match="reanúdala"):
        servicios.ejecucion.iniciar(actividad["id"], empresa.ana)


# ---------- Estado de la actividad con dos operarios ----------

def test_estado_de_la_actividad_con_dos_operarios(servicios, empresa, crear_actividad, reloj):
    actividad = crear_actividad([empresa.ana, empresa.luis])
    general = lambda: ver(servicios, actividad, empresa.admin)
    assert general()["estado"] == "ASIGNADA"

    servicios.ejecucion.iniciar(actividad["id"], empresa.ana)
    assert general()["estado"] == "EN_EJECUCION"

    reloj.avanzar(5)
    servicios.ejecucion.pausar(actividad["id"], empresa.ana, "Actividad urgente")
    assert general()["estado"] == "PAUSADA"

    servicios.ejecucion.reanudar(actividad["id"], empresa.ana)
    reloj.avanzar(5)
    servicios.ejecucion.finalizar(actividad["id"], empresa.ana)
    vista = general()
    assert vista["estado"] == "ASIGNADA"
    assert (vista["finalizados"], vista["total_asignados"]) == (1, 2)

    servicios.ejecucion.iniciar(actividad["id"], empresa.luis)
    assert general()["estado"] == "EN_EJECUCION"
    reloj.avanzar(20)
    servicios.ejecucion.finalizar(actividad["id"], empresa.luis)

    vista = general()
    assert vista["estado"] == "COMPLETADA"
    assert vista["estado_general"] == "COMPLETADA"
    assert (vista["finalizados"], vista["total_asignados"]) == (2, 2)
    assert vista["tiempo_real_min"] == 30    # 10 de Ana (sin su pausa) más 20 de Luis.
    assert [e["operario_nombre"] for e in vista["ejecuciones"]] == ["Ana", "Luis"]
    assert [o["estado_ejecucion"] for o in vista["operarios"]] == ["FINALIZADA", "FINALIZADA"]


def test_la_pausa_de_uno_no_pausa_al_otro(servicios, empresa, crear_actividad):
    actividad = crear_actividad([empresa.ana, empresa.luis])
    servicios.ejecucion.iniciar(actividad["id"], empresa.ana)
    servicios.ejecucion.iniciar(actividad["id"], empresa.luis)
    servicios.ejecucion.pausar(actividad["id"], empresa.ana, "Falta material")

    assert ver(servicios, actividad, empresa.ana)["estado"] == "PAUSADA"
    assert ver(servicios, actividad, empresa.luis)["estado"] == "EN_EJECUCION"
    assert ver(servicios, actividad, empresa.admin)["estado"] == "EN_EJECUCION"


# ---------- Lo que ve cada quien ----------

def test_vista_del_operario_no_depende_de_sus_companeros(servicios, empresa, crear_actividad):
    actividad = crear_actividad([empresa.ana, empresa.luis])
    servicios.ejecucion.iniciar(actividad["id"], empresa.ana)

    de_luis = ver(servicios, actividad, empresa.luis)
    assert de_luis["estado"] == "ASIGNADA"
    assert de_luis["ejecucion"] is None
    assert de_luis["estado_general"] == "EN_EJECUCION"

    servicios.ejecucion.finalizar(actividad["id"], empresa.ana)
    de_ana = ver(servicios, actividad, empresa.ana)
    assert de_ana["estado"] == "COMPLETADA"
    assert de_ana["estado_general"] == "ASIGNADA"
    assert de_ana["ejecucion"]["usuario_id"] == empresa.ana["id"]

    lista_de_ana = servicios.actividades.listar_actividades({}, empresa.ana)
    assert [a["estado"] for a in lista_de_ana] == ["COMPLETADA"]


def test_vista_del_administrador_trae_la_ejecucion_abierta(servicios, empresa, crear_actividad):
    actividad = crear_actividad([empresa.ana, empresa.luis])
    assert ver(servicios, actividad, empresa.admin)["ejecucion"] is None
    assert [o["estado_ejecucion"] for o in ver(servicios, actividad, empresa.admin)["operarios"]] == [None, None]

    servicios.ejecucion.iniciar(actividad["id"], empresa.ana)
    servicios.ejecucion.finalizar(actividad["id"], empresa.ana)
    servicios.ejecucion.iniciar(actividad["id"], empresa.luis)

    vista = ver(servicios, actividad, empresa.admin)
    assert vista["estado"] == "EN_EJECUCION"
    assert vista["ejecucion"]["usuario_id"] == empresa.luis["id"]    # La abierta, no la primera.
    assert vista["ejecucion"]["fecha_inicio"] is not None
    assert len(vista["ejecuciones"]) == 2


# ---------- Finalizar ----------

def test_finalizar_guarda_la_observacion_y_no_se_repite(servicios, empresa, crear_actividad):
    actividad = crear_actividad([empresa.ana])
    servicios.ejecucion.iniciar(actividad["id"], empresa.ana)

    vista = servicios.ejecucion.finalizar(actividad["id"], empresa.ana, "  Quedó calibrada.  ")
    assert vista["estado"] == "COMPLETADA"
    assert vista["ejecucion"]["observacion"] == "Quedó calibrada."
    assert vista["ejecucion"]["fecha_fin"] is not None

    with pytest.raises(ValidationError):
        servicios.ejecucion.finalizar(actividad["id"], empresa.ana)


def test_no_se_inicia_una_actividad_en_estado_final(servicios, repos, empresa, crear_actividad):
    terminada = crear_actividad([empresa.ana])
    servicios.ejecucion.iniciar(terminada["id"], empresa.ana)
    servicios.ejecucion.finalizar(terminada["id"], empresa.ana)
    with pytest.raises(ValidationError):
        servicios.ejecucion.iniciar(terminada["id"], empresa.ana)

    # Cancelar se construye en un paso posterior: aquí el estado se pone directamente.
    cancelada = crear_actividad([empresa.ana], titulo="Limpiar la banda")
    repos.actividades.update(cancelada["id"], {"estado": "CANCELADA"})
    with pytest.raises(ValidationError):
        servicios.ejecucion.iniciar(cancelada["id"], empresa.ana)
    assert repos.ejecuciones.find_by_actividades([cancelada["id"]]) == []


# ---------- Permisos ----------

def test_solo_quien_la_tiene_asignada_puede_ejecutarla(servicios, repos, empresa, crear_actividad):
    actividad = crear_actividad([empresa.ana])
    with pytest.raises(ProhibidoError):
        servicios.ejecucion.iniciar(actividad["id"], empresa.luis)

    de_otra_empresa = {**empresa.ana, "empresa_id": "otra"}
    with pytest.raises(NotFoundError):
        servicios.ejecucion.iniciar(actividad["id"], de_otra_empresa)
    with pytest.raises(NotFoundError):
        servicios.ejecucion.iniciar("no-es-un-id", empresa.ana)
