"""Pruebas del reporte de actividad (alcance, Sección 5.1): el Operario reporta un trabajo que otra
área le pidió directamente; el Administrador lo convierte en actividad o lo descarta con un motivo."""
from datetime import datetime, timezone

import pytest

from app.models.enums import EstadoReporte
from app.models.reporte import Reporte
from app.services.reporte_service import MOTIVO_REPORTE_YA_REVISADO
from app.utils.errors import NotFoundError, ProhibidoError, ValidationError

HOY = "2026-10-10"
AHORA = datetime(2026, 10, 10, 8, 0, tzinfo=timezone.utc)


def reportar(servicios, operario, **campos):
    datos = {"titulo": "Revisar la báscula de despacho", "pedido_por": "Jefe de bodega", **campos}
    return servicios.reportes.reportar(datos, operario)


def datos_de_actividad(operarios, **campos):
    return {
        "titulo": "Revisar la báscula de despacho", "ubicacion": "Bodega", "categoria": "REVISION",
        "prioridad": "MEDIA", "tiempo_estimado_min": 30, "fecha_programada": HOY,
        "operario_ids": [operario["id"] for operario in operarios], **campos,
    }


# ---------- La clase ----------

def nuevo_reporte(**campos):
    datos = {"empresa_id": "e1", "operario_id": "o1", "titulo": "Algo", "pedido_por": "Calidad", "fecha": AHORA}
    return Reporte(**{**datos, **campos})


@pytest.mark.parametrize("campo, mensaje", [("titulo", "qué te pidieron"), ("pedido_por", "quién te lo pidió")])
def test_lo_que_se_pidio_y_quien_lo_pidio_son_obligatorios(campo, mensaje):
    with pytest.raises(ValidationError, match=mensaje):
        nuevo_reporte(**{campo: "   "})


@pytest.mark.parametrize("tiempo", [0, 24 * 60 + 1, "30", 1.5, True])
def test_el_tiempo_estimado_si_viene_es_un_entero_de_minutos_valido(tiempo):
    with pytest.raises(ValidationError):
        nuevo_reporte(tiempo_estimado_min=tiempo)


def test_el_detalle_y_el_tiempo_son_opcionales():
    reporte = nuevo_reporte(detalle="  ", tiempo_estimado_min=None)
    assert reporte.detalle is None and reporte.tiempo_estimado_min is None
    assert reporte.estado == EstadoReporte.PENDIENTE


def test_un_reporte_revisado_no_cambia_mas():
    reporte = nuevo_reporte()
    reporte.descartar("No es de esta área", "a1", AHORA)
    with pytest.raises(ValidationError, match="ya se revisó"):
        reporte.convertir("act1", "a1", AHORA)
    with pytest.raises(ValidationError, match="ya se revisó"):
        reporte.descartar("Otro motivo", "a1", AHORA)


def test_descartar_exige_motivo():
    with pytest.raises(ValidationError, match="por qué descartas"):
        nuevo_reporte().descartar("", "a1", AHORA)


def test_el_reporte_se_reconstruye_igual_desde_su_documento():
    reporte = nuevo_reporte(detalle="Urgente para hoy", tiempo_estimado_min=20)
    reporte.convertir("act1", "a1", AHORA)
    copia = Reporte.desde_documento({"_id": "r1", **reporte.to_dict()})
    assert copia.to_dict() == reporte.to_dict()


# ---------- Reportar (Operario) ----------

def test_el_operario_reporta_y_queda_por_revisar_con_la_hora_del_servidor(servicios, empresa, reloj):
    reporte = reportar(servicios, empresa.ana, detalle="Pesa de más", tiempo_estimado_min=20)

    assert reporte["estado"] == "PENDIENTE"
    assert reporte["operario_id"] == empresa.ana["id"]
    assert reporte["operario_nombre"] == "Ana"
    assert reporte["empresa_id"] == empresa.id
    assert reporte["fecha"] == reloj.ahora.replace(tzinfo=None)    # Mongo guarda las fechas sin zona.
    assert reporte["revision"] is None


def test_solo_un_operario_reporta(servicios, empresa):
    with pytest.raises(ProhibidoError):
        reportar(servicios, empresa.admin)


def test_el_reporte_no_entra_en_la_carga_del_operario(servicios, empresa):
    reportar(servicios, empresa.ana, tiempo_estimado_min=120)

    carga = servicios.carga.consultar(HOY, HOY, empresa.admin)
    fila = next(o for o in carga["operarios"] if o["id"] == empresa.ana["id"])
    assert sum(jornada["minutos"] for jornada in fila["jornadas"]) == 0
    assert servicios.actividades.listar_actividades({}, empresa.admin) == []


# ---------- Listar ----------

def test_el_operario_ve_solo_sus_reportes_del_mas_reciente_al_mas_antiguo(servicios, empresa, reloj):
    primero = reportar(servicios, empresa.ana, titulo="Primero")
    reloj.avanzar(5)
    segundo = reportar(servicios, empresa.ana, titulo="Segundo")
    reportar(servicios, empresa.luis, titulo="De Luis")

    vistos = servicios.reportes.listar(empresa.ana)
    assert [r["id"] for r in vistos] == [segundo["id"], primero["id"]]


def test_el_administrador_ve_los_de_su_empresa_y_puede_pedir_solo_los_por_revisar(
        servicios, empresa, otra_empresa, reloj):
    descartado = reportar(servicios, empresa.ana, titulo="Ya no")
    servicios.reportes.descartar(descartado["id"], "No aplica", empresa.admin)
    reloj.avanzar(5)
    pendiente = reportar(servicios, empresa.luis)
    reportar(servicios, otra_empresa.ivan)

    todos = servicios.reportes.listar(empresa.admin)
    por_revisar = servicios.reportes.listar(empresa.admin, "PENDIENTE")

    assert [r["id"] for r in todos] == [descartado["id"], pendiente["id"]]
    assert [r["id"] for r in por_revisar] == [pendiente["id"]]


def test_un_estado_desconocido_no_se_acepta(servicios, empresa):
    with pytest.raises(ValidationError):
        servicios.reportes.listar(empresa.admin, "BORRADO")


# ---------- Convertir y descartar (Administrador) ----------

def test_convertir_crea_la_actividad_y_deja_el_reporte_convertido(servicios, empresa, reloj):
    reporte = reportar(servicios, empresa.ana)
    reloj.avanzar(10)

    actividad = servicios.reportes.convertir(reporte["id"], datos_de_actividad([empresa.ana]), empresa.admin)

    assert actividad["codigo"].startswith("ACT-")
    assert actividad["estado"] == "ASIGNADA"
    visto = servicios.reportes.listar(empresa.ana)[0]
    assert visto["estado"] == "CONVERTIDO"
    assert visto["revision"]["actividad_id"] == actividad["id"]
    assert visto["revision"]["actividad_codigo"] == actividad["codigo"]
    assert visto["revision"]["autor_id"] == empresa.admin["id"]
    assert visto["revision"]["fecha"] == reloj.ahora.replace(tzinfo=None)


def test_si_los_datos_de_la_actividad_no_son_validos_el_reporte_sigue_por_revisar(servicios, empresa):
    reporte = reportar(servicios, empresa.ana)

    with pytest.raises(ValidationError):
        servicios.reportes.convertir(reporte["id"], datos_de_actividad([empresa.ana], titulo=""), empresa.admin)

    assert servicios.reportes.listar(empresa.ana)[0]["estado"] == "PENDIENTE"
    assert servicios.actividades.listar_actividades({}, empresa.admin) == []


def test_descartar_guarda_el_motivo_que_ve_el_operario(servicios, empresa):
    reporte = reportar(servicios, empresa.ana)

    descartado = servicios.reportes.descartar(reporte["id"], "Lo atiende mantenimiento", empresa.admin)

    assert descartado["estado"] == "DESCARTADO"
    assert servicios.reportes.listar(empresa.ana)[0]["revision"]["motivo"] == "Lo atiende mantenimiento"


def test_un_reporte_revisado_no_se_vuelve_a_convertir(servicios, empresa):
    reporte = reportar(servicios, empresa.ana)
    servicios.reportes.descartar(reporte["id"], "No aplica", empresa.admin)

    with pytest.raises(ValidationError, match="ya se revisó"):
        servicios.reportes.convertir(reporte["id"], datos_de_actividad([empresa.ana]), empresa.admin)
    assert servicios.actividades.listar_actividades({}, empresa.admin) == []


def test_si_otro_lo_revisa_al_mismo_tiempo_la_actividad_que_sobra_queda_cancelada(
        servicios, empresa, repos, monkeypatch):
    reporte = reportar(servicios, empresa.ana)
    crear = servicios.actividades.crear_actividad

    def crear_mientras_otro_descarta(data, solicitante):
        # Entre leer el reporte y guardar la revisión, otro Administrador lo descarta.
        actividad = crear(data, solicitante)
        servicios.reportes.descartar(reporte["id"], "Duplicado", empresa.admin)
        return actividad
    monkeypatch.setattr(servicios.actividades, "crear_actividad", crear_mientras_otro_descarta)

    with pytest.raises(ValidationError, match="mientras tanto"):
        servicios.reportes.convertir(reporte["id"], datos_de_actividad([empresa.ana]), empresa.admin)

    actividad = servicios.actividades.listar_actividades({}, empresa.admin)[0]
    assert actividad["estado"] == "CANCELADA"
    assert actividad["cancelacion"]["motivo"] == MOTIVO_REPORTE_YA_REVISADO
    assert servicios.reportes.listar(empresa.ana)[0]["estado"] == "DESCARTADO"


def test_el_administrador_de_otra_empresa_no_ve_el_reporte(servicios, empresa, otra_empresa):
    reporte = reportar(servicios, empresa.ana)
    with pytest.raises(NotFoundError):
        servicios.reportes.descartar(reporte["id"], "No", otra_empresa.admin)


def test_el_operario_no_revisa_reportes(servicios, empresa):
    reporte = reportar(servicios, empresa.ana)
    with pytest.raises(ProhibidoError):
        servicios.reportes.descartar(reporte["id"], "No", empresa.ana)


# ---------- Rutas ----------

def test_rutas_del_reporte(cliente_de, empresa):
    operario = cliente_de(empresa.ana)
    admin = cliente_de(empresa.admin)

    creado = operario.post("/reportes", json={"titulo": "Mover estibas", "pedido_por": "Despachos"})
    assert creado.status_code == 201
    reporte_id = creado.get_json()["id"]

    assert admin.post("/reportes", json={"titulo": "x", "pedido_por": "y"}).status_code == 403
    assert [r["id"] for r in admin.get("/reportes?estado=PENDIENTE").get_json()] == [reporte_id]
    assert operario.post(f"/reportes/{reporte_id}/descartar", json={"motivo": "x"}).status_code == 403

    convertida = admin.post(f"/reportes/{reporte_id}/convertir", json=datos_de_actividad([empresa.ana]))
    assert convertida.status_code == 201
    assert operario.get("/reportes").get_json()[0]["estado"] == "CONVERTIDO"
    assert admin.post(f"/reportes/{reporte_id}/descartar", json={"motivo": "x"}).status_code == 400
    assert cliente_de(None).get("/reportes").status_code == 401
