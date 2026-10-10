"""Pruebas de las listas de motivos y de la regla de "Otro" (alcance, Sección 5.1)."""
import pytest

from app.services.catalogo_service import (
    MOTIVO_CANCELACION, MOTIVO_DEVOLUCION, MOTIVO_PAUSA, resolver_motivo,
)
from app.utils.errors import NotFoundError, ValidationError

FIJOS_PAUSA = ["Actividad urgente", "Actividad de hora fija", "Fin de jornada"]


def en_curso(servicios, empresa, crear_actividad, operario=None, **campos):
    operario = operario or empresa.ana
    actividad = crear_actividad([operario], **campos)
    servicios.ejecucion.iniciar(actividad["id"], operario)
    return actividad


# ---------- La regla del motivo ----------

def test_un_motivo_de_la_lista_se_guarda_tal_cual_y_el_detalle_se_ignora():
    assert resolver_motivo("Fin de jornada", "no importa") == ("Fin de jornada", False)
    assert resolver_motivo("  Falta   material ") == ("Falta material", False)
    assert resolver_motivo(None) == ("", False)    # Que no esté vacío lo exige quien lo recibe.


@pytest.mark.parametrize("otro", ["Otro", "otro", " OTRO "])
def test_con_otro_se_guarda_lo_que_se_escribio(otro):
    assert resolver_motivo(otro, "  Se fue la luz ") == ("Se fue la luz", True)


@pytest.mark.parametrize("detalle", [None, "", "   ", "otro"])
def test_otro_sin_detalle_es_un_error(detalle):
    with pytest.raises(ValidationError):
        resolver_motivo("Otro", detalle)


# ---------- Motivos de pausa ----------

def test_los_motivos_de_pausa_traen_los_fijos_y_otro_al_final(servicios, empresa):
    assert servicios.catalogos.listar(empresa.ana, MOTIVO_PAUSA) == FIJOS_PAUSA + ["Otro"]
    assert servicios.catalogos.listar(empresa.admin, MOTIVO_PAUSA) == FIJOS_PAUSA + ["Otro"]


def test_pausar_con_otro_guarda_el_detalle_y_lo_agrega_a_la_lista(servicios, empresa, crear_actividad):
    actividad = en_curso(servicios, empresa, crear_actividad)

    vista = servicios.ejecucion.pausar(actividad["id"], empresa.ana, "Otro", "Se fue la luz")

    assert vista["ejecucion"]["pausas"][0]["motivo"] == "Se fue la luz"
    assert servicios.catalogos.listar(empresa.ana, MOTIVO_PAUSA) == FIJOS_PAUSA + ["Se fue la luz", "Otro"]


def test_el_mismo_motivo_con_otras_mayusculas_no_se_repite(servicios, empresa, crear_actividad):
    actividad = en_curso(servicios, empresa, crear_actividad)
    servicios.ejecucion.pausar(actividad["id"], empresa.ana, "Otro", "Se fue la luz")
    servicios.ejecucion.reanudar(actividad["id"], empresa.ana)
    vista = servicios.ejecucion.pausar(actividad["id"], empresa.ana, "otro", "SE FUE LA LUZ")

    assert vista["ejecucion"]["pausas"][1]["motivo"] == "SE FUE LA LUZ"    # La pausa guarda lo que se escribió.
    assert servicios.catalogos.listar(empresa.ana, MOTIVO_PAUSA) == FIJOS_PAUSA + ["Se fue la luz", "Otro"]


def test_pausar_con_otro_sin_detalle_da_error_y_no_pausa(servicios, empresa, crear_actividad):
    actividad = en_curso(servicios, empresa, crear_actividad)

    with pytest.raises(ValidationError):
        servicios.ejecucion.pausar(actividad["id"], empresa.ana, "Otro")
    with pytest.raises(ValidationError):
        servicios.ejecucion.pausar(actividad["id"], empresa.ana, "Otro", "  ")

    assert servicios.actividades.obtener_actividad(actividad["id"], empresa.ana)["estado"] == "EN_EJECUCION"
    assert servicios.catalogos.listar(empresa.ana, MOTIVO_PAUSA) == FIJOS_PAUSA + ["Otro"]


def test_un_motivo_elegido_de_la_lista_no_se_registra(servicios, repos, empresa, crear_actividad):
    actividad = en_curso(servicios, empresa, crear_actividad)
    servicios.ejecucion.pausar(actividad["id"], empresa.ana, "Fin de jornada", "detalle que se ignora")
    servicios.ejecucion.reanudar(actividad["id"], empresa.ana)
    # Escribir en "Otro" un motivo fijo tampoco lo duplica.
    servicios.ejecucion.pausar(actividad["id"], empresa.ana, "Otro", "actividad urgente")

    assert repos.catalogos.listar(empresa.id, MOTIVO_PAUSA) == []
    assert servicios.catalogos.listar(empresa.ana, MOTIVO_PAUSA) == FIJOS_PAUSA + ["Otro"]


def test_una_pausa_que_falla_no_agrega_el_motivo(servicios, empresa, crear_actividad):
    de_hora_fija = en_curso(servicios, empresa, crear_actividad, hora_programada="09:00")

    with pytest.raises(ValidationError):
        servicios.ejecucion.pausar(de_hora_fija["id"], empresa.ana, "Otro", "Se fue la luz")
    assert servicios.catalogos.listar(empresa.ana, MOTIVO_PAUSA) == FIJOS_PAUSA + ["Otro"]


def test_pausar_por_la_api_acepta_motivo_solo_o_con_detalle(cliente_de, empresa, crear_actividad):
    actividad = crear_actividad([empresa.ana])
    ana = cliente_de(empresa.ana)
    base = f"/actividades/{actividad['id']}"
    ana.post(f"{base}/iniciar")

    assert ana.post(f"{base}/pausar", json={"motivo": "Otro"}).status_code == 400
    pausada = ana.post(f"{base}/pausar", json={"motivo": "Otro", "detalle": "Se fue la luz"})
    assert pausada.status_code == 200
    assert pausada.get_json()["ejecucion"]["pausas"][0]["motivo"] == "Se fue la luz"

    ana.post(f"{base}/reanudar")
    sin_detalle = ana.post(f"{base}/pausar", json={"motivo": "Fin de jornada"})
    assert sin_detalle.get_json()["ejecucion"]["pausas"][1]["motivo"] == "Fin de jornada"
    assert ana.get("/catalogos/motivos-pausa").get_json() == FIJOS_PAUSA + ["Se fue la luz", "Otro"]


# ---------- Motivos de cancelación y de devolución ----------

def test_los_motivos_de_cancelacion_empiezan_solo_con_otro_y_se_van_llenando(servicios, empresa, crear_actividad):
    assert servicios.catalogos.listar(empresa.admin, MOTIVO_CANCELACION) == ["Otro"]

    servicios.actividades.cancelar(crear_actividad([])["id"], empresa.admin, "Otro", "Pedido anulado")
    servicios.actividades.cancelar(crear_actividad([])["id"], empresa.admin, "otro", "pedido ANULADO")
    servicios.actividades.cancelar(crear_actividad([])["id"], empresa.admin, "Otro", "Cambio de plan")
    servicios.actividades.cancelar(crear_actividad([])["id"], empresa.admin, "Pedido anulado")

    assert servicios.catalogos.listar(empresa.admin, MOTIVO_CANCELACION) == ["Cambio de plan", "Pedido anulado", "Otro"]
    assert servicios.catalogos.listar(empresa.admin, MOTIVO_PAUSA) == FIJOS_PAUSA + ["Otro"]    # Cada lista es aparte.


def test_los_motivos_de_devolucion_son_fijos(servicios, empresa, crear_actividad):
    esperados = ["Falta información", "Me la asignaron por error", "Falta herramienta o material",
                 "El equipo no está disponible", "Otro"]
    assert servicios.catalogos.listar(empresa.ana, MOTIVO_DEVOLUCION) == esperados

    servicios.ejecucion.devolver(crear_actividad([empresa.ana])["id"], empresa.ana, "Otro", "No es mi turno")
    assert servicios.catalogos.listar(empresa.ana, MOTIVO_DEVOLUCION) == esperados


def test_otra_empresa_no_ve_los_motivos_de_esta(servicios, empresa, otra_empresa, crear_actividad):
    actividad = en_curso(servicios, empresa, crear_actividad)
    servicios.ejecucion.pausar(actividad["id"], empresa.ana, "Otro", "Se fue la luz")
    servicios.actividades.cancelar(crear_actividad([])["id"], empresa.admin, "Otro", "Pedido anulado")

    assert servicios.catalogos.listar(otra_empresa.ivan, MOTIVO_PAUSA) == FIJOS_PAUSA + ["Otro"]
    assert servicios.catalogos.listar(otra_empresa.admin, MOTIVO_CANCELACION) == ["Otro"]


def test_rutas_de_catalogos(cliente_de, empresa):
    assert cliente_de().get("/catalogos/motivos-pausa").status_code == 401
    for usuario in (empresa.admin, empresa.ana):
        cliente = cliente_de(usuario)
        assert cliente.get("/catalogos/motivos-pausa").get_json() == FIJOS_PAUSA + ["Otro"]
        assert cliente.get("/catalogos/motivos-cancelacion").get_json() == ["Otro"]
        assert cliente.get("/catalogos/motivos-devolucion").get_json()[-1] == "Otro"
        assert cliente.get("/catalogos/no-existe").status_code == 404


def test_una_lista_desconocida_no_existe(servicios, empresa):
    with pytest.raises(NotFoundError):
        servicios.catalogos.listar(empresa.admin, "COLORES")
