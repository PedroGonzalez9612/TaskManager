"""Pruebas del cierre de jornada (alcance, Sección 5.1): al terminar el día, lo que no tiene hora se
reprograma, lo de hora fija queda No realizado y lo que alguien dejó en curso se pausa o se cierra.

El reloj de las pruebas empieza el 10 de octubre a las 08:00 UTC (las 03:00 en Bogotá, la zona por
defecto). El día 10 termina allí a las 05:00 UTC del 11."""
from datetime import datetime, timezone

import pytest

from app.models.ejecucion import Ejecucion
from app.models.pausa import Pausa
from app.services.cierre_jornada_service import momento_de_cierre
from app.utils.errors import ValidationError

HOY = "2026-10-10"          # La fecha programada de las actividades que crea conftest.py.
MANANA = "2026-10-11"
MEDIANOCHE = datetime(2026, 10, 11, 5, 0)    # Fin del día 10 en Bogotá, en UTC. Mongo guarda sin zona.
UN_DIA = 24 * 60
NADA = {"reprogramadas": 0, "no_realizadas": 0, "ejecuciones_pausadas": 0, "ejecuciones_cerradas": 0}


def ver(servicios, actividad, solicitante):
    return servicios.actividades.obtener_actividad(actividad["id"], solicitante)


def iniciar_una_hora_antes_de_la_medianoche(servicios, reloj, actividad, operario):
    """El operario inicia a las 23:00 de Bogotá y no pausa. Deja el reloj a las 03:00 del día 11."""
    reloj.avanzar(20 * 60)
    servicios.ejecucion.iniciar(actividad["id"], operario)
    reloj.avanzar(4 * 60)


# ---------- Horario flexible: actividad reprogramada ----------

def test_una_flexible_que_no_se_hizo_pasa_al_dia_siguiente(servicios, empresa, crear_actividad, reloj):
    actividad = crear_actividad([empresa.ana])
    assert actividad["reprogramada"] is False
    assert actividad["dias_de_retraso"] == 0
    reloj.avanzar(UN_DIA)

    vista = ver(servicios, actividad, empresa.ana)

    assert vista["fecha_programada"] == MANANA
    assert vista["fecha_original"] == HOY
    assert vista["reprogramada"] is True
    assert vista["dias_de_retraso"] == 1
    assert vista["estado"] == "ASIGNADA"
    assert vista["reprogramaciones"] == [
        {"jornada_origen": HOY, "jornada_destino": MANANA, "fecha": reloj.ahora.replace(tzinfo=None)},
    ]


def test_consultar_dos_veces_no_agrega_otra_reprogramacion(servicios, empresa, crear_actividad, reloj):
    actividad = crear_actividad([empresa.ana])
    reloj.avanzar(UN_DIA)

    ver(servicios, actividad, empresa.admin)
    reloj.avanzar(60)
    servicios.actividades.listar_actividades({}, empresa.admin)
    vista = ver(servicios, actividad, empresa.admin)

    assert len(vista["reprogramaciones"]) == 1
    assert vista["dias_de_retraso"] == 1
    assert servicios.cierre_jornada.cerrar_pendientes(empresa.id) == NADA


def test_tres_dias_sin_consultar_dejan_una_sola_reprogramacion(servicios, empresa, crear_actividad, reloj):
    actividad = crear_actividad([])
    reloj.avanzar(3 * UN_DIA)

    vista = servicios.actividades.listar_actividades({}, empresa.admin)[0]

    assert vista["id"] == actividad["id"]
    assert vista["fecha_programada"] == "2026-10-13"
    assert [(a["jornada_origen"], a["jornada_destino"]) for a in vista["reprogramaciones"]] == [(HOY, "2026-10-13")]
    assert vista["dias_de_retraso"] == 3
    assert vista["estado"] == "PENDIENTE"


def test_lo_que_quedo_en_curso_se_pausa_a_la_medianoche_por_fin_de_jornada(servicios, repos, empresa,
                                                                             crear_actividad, reloj):
    actividad = crear_actividad([empresa.ana])
    iniciar_una_hora_antes_de_la_medianoche(servicios, reloj, actividad, empresa.ana)

    vista = ver(servicios, actividad, empresa.ana)

    assert vista["estado"] == "PAUSADA"
    assert vista["estado_general"] == "PAUSADA"
    assert vista["fecha_programada"] == MANANA
    assert vista["reprogramada"] is True
    # La pausa empieza a la medianoche de la empresa, no a la hora en que se consultó.
    assert vista["ejecucion"]["pausas"] == [{"motivo": "Fin de jornada", "inicio": MEDIANOCHE, "fin": None}]
    assert vista["ejecucion"]["tiempo_real_min"] == 60
    assert repos.ejecuciones.find_en_progreso_de_usuario(empresa.ana["id"]) is None
    # "Fin de jornada" es un motivo fijo: no se agrega a la lista de la empresa.
    assert repos.catalogos.collection.count_documents({}) == 0


def test_la_reprogramada_se_puede_reanudar_al_dia_siguiente(servicios, empresa, crear_actividad, reloj):
    actividad = crear_actividad([empresa.ana])
    iniciar_una_hora_antes_de_la_medianoche(servicios, reloj, actividad, empresa.ana)

    reanudada = servicios.ejecucion.reanudar(actividad["id"], empresa.ana)
    reloj.avanzar(30)
    vista = ver(servicios, actividad, empresa.ana)

    assert reanudada["estado"] == "EN_EJECUCION"
    assert vista["ejecucion"]["tiempo_real_min"] == 90
    assert vista["ejecucion"]["pausas"][0]["fin"] is not None


def test_con_la_de_ayer_pausada_el_operario_puede_iniciar_otra(servicios, empresa, crear_actividad, reloj):
    de_ayer = crear_actividad([empresa.ana])
    otra = crear_actividad([empresa.ana], titulo="Limpiar la banda", fecha_programada=MANANA)
    iniciar_una_hora_antes_de_la_medianoche(servicios, reloj, de_ayer, empresa.ana)

    # Iniciar es lo primero que pasa después de la medianoche: el cierre corre ahí mismo.
    iniciada = servicios.ejecucion.iniciar(otra["id"], empresa.ana)

    assert iniciada["estado"] == "EN_EJECUCION"
    assert ver(servicios, de_ayer, empresa.ana)["estado"] == "PAUSADA"


def test_la_pausa_que_hizo_el_operario_se_conserva(servicios, empresa, crear_actividad, reloj):
    actividad = crear_actividad([empresa.ana])
    servicios.ejecucion.iniciar(actividad["id"], empresa.ana)
    reloj.avanzar(10)
    servicios.ejecucion.pausar(actividad["id"], empresa.ana, "Actividad urgente")
    reloj.avanzar(UN_DIA)

    assert servicios.cierre_jornada.cerrar_pendientes(empresa.id) == {**NADA, "reprogramadas": 1}
    vista = ver(servicios, actividad, empresa.ana)

    assert [pausa["motivo"] for pausa in vista["ejecucion"]["pausas"]] == ["Actividad urgente"]
    assert vista["estado"] == "PAUSADA"
    assert vista["fecha_programada"] == MANANA
    assert vista["ejecucion"]["tiempo_real_min"] == 10


def test_con_varios_operarios_se_reprograma_una_sola_vez_para_todos(servicios, empresa, crear_actividad, reloj):
    actividad = crear_actividad([empresa.ana, empresa.luis])
    iniciar_una_hora_antes_de_la_medianoche(servicios, reloj, actividad, empresa.ana)

    assert servicios.cierre_jornada.cerrar_pendientes(empresa.id) == {
        **NADA, "reprogramadas": 1, "ejecuciones_pausadas": 1,
    }
    de_ana = ver(servicios, actividad, empresa.ana)
    de_luis = ver(servicios, actividad, empresa.luis)

    assert de_ana["fecha_programada"] == MANANA
    assert de_luis["fecha_programada"] == MANANA
    assert len(de_luis["reprogramaciones"]) == 1
    assert de_ana["estado"] == "PAUSADA"
    assert de_luis["estado"] == "ASIGNADA"         # Luis no la había iniciado.
    assert de_luis["estado_general"] == "PAUSADA"


def test_un_documento_anterior_sin_estado_ni_fecha_original_tambien_se_reprograma(servicios, repos, empresa, reloj):
    actividad_id = repos.actividades.insert({"titulo": "Vieja", "empresa_id": empresa.id, "fecha_programada": HOY})
    reloj.avanzar(UN_DIA)

    vista = servicios.actividades.obtener_actividad(actividad_id, empresa.admin)

    assert vista["fecha_programada"] == MANANA
    assert vista["fecha_original"] == HOY
    assert vista["dias_de_retraso"] == 1


# ---------- Hora fija: No realizada ----------

def test_una_de_hora_fija_que_no_se_hizo_queda_no_realizada(servicios, empresa, crear_actividad, reloj):
    actividad = crear_actividad([empresa.ana], hora_programada="09:00")
    reloj.avanzar(UN_DIA)

    vista = ver(servicios, actividad, empresa.ana)

    assert vista["estado"] == "NO_REALIZADA"
    assert vista["estado_general"] == "NO_REALIZADA"
    assert vista["fecha_no_realizada"] == reloj.ahora.replace(tzinfo=None)
    assert vista["fecha_programada"] == HOY        # No se reprograma.
    assert vista["reprogramada"] is False
    assert vista["dias_de_retraso"] == 0


def test_una_no_realizada_no_se_inicia(servicios, empresa, crear_actividad, reloj):
    actividad = crear_actividad([empresa.ana], hora_programada="09:00")
    reloj.avanzar(UN_DIA)

    with pytest.raises(ValidationError):
        servicios.ejecucion.iniciar(actividad["id"], empresa.ana)


def test_una_no_realizada_no_se_edita(servicios, empresa, crear_actividad, reloj):
    actividad = crear_actividad([empresa.ana], hora_programada="09:00")
    reloj.avanzar(UN_DIA)

    with pytest.raises(ValidationError):
        servicios.actividades.actualizar_actividad(actividad["id"], {"fecha_programada": MANANA}, empresa.admin)


def test_una_no_realizada_no_se_cancela(servicios, empresa, crear_actividad, reloj):
    actividad = crear_actividad([empresa.ana], hora_programada="09:00")
    reloj.avanzar(UN_DIA)

    with pytest.raises(ValidationError):
        servicios.actividades.cancelar(actividad["id"], empresa.admin, "Otro", "Ya no hace falta")


def test_la_de_hora_fija_en_curso_se_cierra_a_la_medianoche_y_conserva_su_tiempo(servicios, repos, empresa,
                                                                                  crear_actividad, reloj):
    actividad = crear_actividad([empresa.ana], hora_programada="23:00")
    otra = crear_actividad([empresa.ana], titulo="Limpiar la banda", fecha_programada=MANANA)
    iniciar_una_hora_antes_de_la_medianoche(servicios, reloj, actividad, empresa.ana)

    assert servicios.cierre_jornada.cerrar_pendientes(empresa.id) == {
        **NADA, "no_realizadas": 1, "ejecuciones_cerradas": 1,
    }
    vista = ver(servicios, actividad, empresa.admin)
    ejecucion = vista["ejecuciones"][0]

    assert vista["estado"] == "NO_REALIZADA"
    assert ejecucion["estado"] == "CERRADA"
    assert ejecucion["fecha_fin"] == MEDIANOCHE
    assert ejecucion["tiempo_real_min"] == 60
    assert vista["tiempo_real_min"] == 60
    assert ver(servicios, actividad, empresa.ana)["estado"] == "NO_REALIZADA"
    # El operario queda libre: no tiene nada en curso de un día anterior.
    assert repos.ejecuciones.find_en_progreso_de_usuario(empresa.ana["id"]) is None
    assert servicios.ejecucion.iniciar(otra["id"], empresa.ana)["estado"] == "EN_EJECUCION"


# ---------- Lo que el cierre no toca ----------

def test_no_toca_las_terminadas_ni_las_de_hoy(servicios, empresa, crear_actividad, reloj):
    completada = crear_actividad([empresa.ana], titulo="Completada")
    servicios.ejecucion.iniciar(completada["id"], empresa.ana)
    servicios.ejecucion.finalizar(completada["id"], empresa.ana)
    cancelada = crear_actividad([], titulo="Cancelada")
    servicios.actividades.cancelar(cancelada["id"], empresa.admin, "Otro", "Pedido anulado")
    de_hora_fija = crear_actividad([empresa.ana], titulo="Fija", hora_programada="09:00")
    de_manana = crear_actividad([empresa.ana], titulo="De mañana", fecha_programada=MANANA)

    reloj.avanzar(UN_DIA)
    assert servicios.cierre_jornada.cerrar_pendientes(empresa.id) == {**NADA, "no_realizadas": 1}
    # Al día siguiente la No realizada ya es de un día pasado, y la "de mañana" pasó a ser de hoy.
    assert servicios.cierre_jornada.cerrar_pendientes(empresa.id) == NADA

    vistas = {a["titulo"]: a for a in servicios.actividades.listar_actividades({}, empresa.admin)}
    assert [vistas[titulo]["estado"] for titulo in ("Completada", "Cancelada", "Fija", "De mañana")] == [
        "COMPLETADA", "CANCELADA", "NO_REALIZADA", "ASIGNADA",
    ]
    assert [vistas[titulo]["fecha_programada"] for titulo in ("Completada", "Cancelada", "Fija")] == [HOY] * 3
    assert vistas["De mañana"]["id"] == de_manana["id"]
    assert vistas["De mañana"]["reprogramada"] is False
    assert vistas["Fija"]["id"] == de_hora_fija["id"]
    assert not any(vista["reprogramada"] for vista in vistas.values())


def actividad_de(servicios, admin, titulo="Ajena"):
    datos = {"titulo": titulo, "ubicacion": "Bodega", "categoria": "LOGISTICA", "tiempo_estimado_min": 30,
             "fecha_programada": HOY}
    return servicios.actividades.crear_actividad(datos, admin)


def test_no_toca_las_actividades_de_otra_empresa(servicios, repos, empresa, otra_empresa, reloj):
    ajena = actividad_de(servicios, otra_empresa.admin)
    reloj.avanzar(UN_DIA)

    assert servicios.cierre_jornada.cerrar_pendientes(empresa.id) == NADA
    servicios.actividades.listar_actividades({}, empresa.admin)

    guardada = repos.actividades.find_by_id(ajena["id"])
    assert guardada["fecha_programada"] == HOY
    assert guardada["reprogramaciones"] == []


def test_sin_empresa_no_hay_nada_que_cerrar(servicios):
    assert servicios.cierre_jornada.cerrar_pendientes(None) == NADA


def test_cada_empresa_cierra_el_dia_a_su_propia_medianoche(servicios, repos, empresa, otra_empresa,
                                                           crear_actividad, reloj):
    repos.empresas.update(empresa.id, {"zona_horaria": "Asia/Tokyo"})    # El día 10 termina a las 15:00 UTC.
    en_tokio = crear_actividad([empresa.ana])
    en_bogota = actividad_de(servicios, otra_empresa.admin)

    reloj.avanzar(6 * 60)       # 14:00 UTC: las 23:00 del día 10 en Tokio.
    assert ver(servicios, en_tokio, empresa.admin)["fecha_programada"] == HOY

    reloj.avanzar(2 * 60)       # 16:00 UTC: la 01:00 del día 11 en Tokio y las 11:00 del día 10 en Bogotá.
    assert ver(servicios, en_tokio, empresa.admin)["fecha_programada"] == MANANA
    assert ver(servicios, en_bogota, otra_empresa.admin)["fecha_programada"] == HOY


def test_en_otra_zona_la_pausa_queda_a_la_medianoche_de_esa_zona(servicios, repos, empresa, crear_actividad, reloj):
    repos.empresas.update(empresa.id, {"zona_horaria": "Asia/Tokyo"})
    actividad = crear_actividad([empresa.ana])
    servicios.ejecucion.iniciar(actividad["id"], empresa.ana)      # 08:00 UTC: las 17:00 en Tokio.
    reloj.avanzar(10 * 60)

    vista = ver(servicios, actividad, empresa.ana)

    assert vista["ejecucion"]["pausas"][0]["inicio"] == datetime(2026, 10, 10, 15, 0)
    assert vista["ejecucion"]["tiempo_real_min"] == 7 * 60


# ---------- Dos peticiones a la vez ----------

def test_si_otra_peticion_ya_cerro_la_jornada_esta_no_repite_nada(servicios, empresa, crear_actividad, reloj,
                                                                  monkeypatch):
    flexible = crear_actividad([empresa.ana], titulo="Flexible")
    de_hora_fija = crear_actividad([empresa.luis], titulo="Fija", hora_programada="23:00")
    reloj.avanzar(20 * 60)
    servicios.ejecucion.iniciar(flexible["id"], empresa.ana)
    servicios.ejecucion.iniciar(de_hora_fija["id"], empresa.luis)
    reloj.avanzar(4 * 60)

    # Dos peticiones leen las mismas actividades atrasadas; la otra termina de cerrar primero.
    cierre = servicios.cierre_jornada
    leidas = cierre.actividad_repository.buscar_abiertas_anteriores_a(empresa.id, MANANA)
    assert len(leidas) == 2
    cierre.cerrar_pendientes(empresa.id)
    monkeypatch.setattr(cierre.actividad_repository, "buscar_abiertas_anteriores_a", lambda *_: leidas)

    assert cierre.cerrar_pendientes(empresa.id) == NADA
    assert len(ver(servicios, flexible, empresa.admin)["reprogramaciones"]) == 1
    assert len(ver(servicios, flexible, empresa.ana)["ejecucion"]["pausas"]) == 1
    assert ver(servicios, de_hora_fija, empresa.admin)["ejecuciones"][0]["fecha_fin"] == MEDIANOCHE


def test_si_otra_peticion_ya_pauso_la_ejecucion_no_se_cuenta_dos_veces(servicios, empresa, crear_actividad, reloj,
                                                                       monkeypatch):
    actividad = crear_actividad([empresa.ana])
    iniciar_una_hora_antes_de_la_medianoche(servicios, reloj, actividad, empresa.ana)
    cierre = servicios.cierre_jornada
    # La otra petición guarda la pausa justo antes: la base de datos rechaza la segunda.
    monkeypatch.setattr(cierre.ejecucion_repository, "guardar", lambda *_, **__: False)

    assert cierre.cerrar_pendientes(empresa.id) == {**NADA, "reprogramadas": 1}


# ---------- La hora del cierre ----------

def test_el_cierre_nunca_queda_antes_del_ultimo_evento_de_la_ejecucion():
    inicio = datetime(2026, 10, 11, 6, 0, tzinfo=timezone.utc)
    fin_jornada = MEDIANOCHE.replace(tzinfo=timezone.utc)
    antes = Ejecucion(actividad_id="a1", fecha_inicio=datetime(2026, 10, 10, 20, 0))    # Sin zona, como en Mongo.
    despues = Ejecucion(actividad_id="a1", fecha_inicio=inicio)
    reanudada = Ejecucion(actividad_id="a1", fecha_inicio=datetime(2026, 10, 10, 20, 0),
                          pausas=[Pausa("Otro", inicio=datetime(2026, 10, 10, 21, 0), fin=inicio)])

    assert momento_de_cierre(antes, fin_jornada) == fin_jornada
    assert momento_de_cierre(despues, fin_jornada) == inicio
    assert momento_de_cierre(reanudada, fin_jornada) == inicio


# ---------- No se programa en un día que ya pasó ----------

def test_no_se_crea_una_actividad_en_un_dia_que_ya_paso(empresa, crear_actividad):
    with pytest.raises(ValidationError, match="no puede ser anterior a hoy"):
        crear_actividad([empresa.ana], fecha_programada="2026-10-09")


def test_no_se_mueve_una_actividad_a_un_dia_que_ya_paso(servicios, empresa, crear_actividad):
    actividad = crear_actividad([empresa.ana])
    cambio = {"fecha_programada": "2026-10-08"}
    with pytest.raises(ValidationError, match="no puede ser anterior a hoy"):
        servicios.actividades.actualizar_actividad(actividad["id"], cambio, empresa.admin)
    assert ver(servicios, actividad, empresa.admin)["fecha_programada"] == HOY


def test_si_se_puede_programar_para_hoy_o_para_despues(servicios, empresa, crear_actividad):
    actividad = crear_actividad([empresa.ana])
    movida = servicios.actividades.actualizar_actividad(actividad["id"], {"fecha_programada": MANANA}, empresa.admin)
    assert movida["fecha_programada"] == MANANA


def test_hoy_es_el_dia_de_la_empresa_no_el_del_servidor(servicios, empresa, crear_actividad, reloj):
    # A las 02:00 UTC del día 11 en Bogotá todavía es el día 10: se puede programar para el 10.
    reloj.avanzar(18 * 60)
    assert crear_actividad([empresa.ana], fecha_programada=HOY)["fecha_programada"] == HOY


def test_editar_otro_dato_de_una_actividad_no_revisa_su_fecha(servicios, empresa, crear_actividad):
    actividad = crear_actividad([empresa.ana])
    editada = servicios.actividades.actualizar_actividad(
        actividad["id"], {"titulo": "Calibrar la selladora 2", "fecha_programada": HOY}, empresa.admin)
    assert editada["titulo"] == "Calibrar la selladora 2"


# ---------- Actividades sin operario: el Administrador las consulta aparte ----------

def test_el_administrador_consulta_las_actividades_sin_operario(servicios, empresa, crear_actividad):
    crear_actividad([empresa.ana], titulo="Con operario")
    crear_actividad([], titulo="Nunca asignada")
    devuelta = crear_actividad([empresa.luis], titulo="Devuelta")
    servicios.ejecucion.devolver(devuelta["id"], empresa.luis, "Falta información")

    sin_operario = servicios.actividades.listar_actividades({"sin_asignar": True}, empresa.admin)

    assert sorted(a["titulo"] for a in sin_operario) == ["Devuelta", "Nunca asignada"]
    assert sorted(a["estado"] for a in sin_operario) == ["DEVUELTA", "PENDIENTE"]


# ---------- Editar una reprogramada ----------

def test_cambiarle_el_dia_a_una_reprogramada_conserva_la_marca_y_la_fecha_original(servicios, empresa,
                                                                                crear_actividad, reloj):
    actividad = crear_actividad([empresa.ana])
    reloj.avanzar(UN_DIA)
    reprogramaciones = ver(servicios, actividad, empresa.admin)["reprogramaciones"]

    editada = servicios.actividades.actualizar_actividad(
        actividad["id"], {"fecha_programada": "2026-10-15"}, empresa.admin,
    )

    assert editada["fecha_programada"] == "2026-10-15"
    assert editada["fecha_original"] == HOY
    assert editada["reprogramada"] is True
    assert editada["reprogramaciones"] == reprogramaciones
    assert editada["dias_de_retraso"] == 5


# ---------- Carga y proyectos ----------

def test_la_carga_cuenta_la_reprogramada_en_su_nueva_jornada(servicios, empresa, crear_actividad, reloj):
    crear_actividad([empresa.ana], titulo="Flexible", tiempo_estimado_min=90)
    crear_actividad([empresa.ana], titulo="Fija", tiempo_estimado_min=30, hora_programada="09:00")
    reloj.avanzar(UN_DIA)

    # La carga es lo primero que se consulta: ella misma cierra la jornada.
    carga = servicios.carga.consultar(HOY, MANANA, empresa.admin)
    jornadas = next(o for o in carga["operarios"] if o["id"] == empresa.ana["id"])["jornadas"]

    # La No realizada sigue contando en su día; la reprogramada ya no.
    assert [(jornada["fecha"], jornada["minutos"]) for jornada in jornadas] == [(HOY, 30), (MANANA, 90)]


def test_el_avance_de_un_proyecto_no_cambia_por_reprogramar(servicios, repos, empresa, crear_actividad, reloj):
    proyecto = servicios.proyectos.crear_proyecto({"nombre": "Montaje"}, empresa.admin)
    hecha = crear_actividad([empresa.ana], titulo="Hecha", proyecto_id=proyecto["id"])
    servicios.ejecucion.iniciar(hecha["id"], empresa.ana)
    servicios.ejecucion.finalizar(hecha["id"], empresa.ana)
    pendiente = crear_actividad([empresa.luis], titulo="Pendiente", proyecto_id=proyecto["id"])
    antes = servicios.proyectos.listar_proyectos(empresa.admin)[0]["avance"]
    reloj.avanzar(UN_DIA)

    # Listar los proyectos es lo primero que pasa al día siguiente: ahí corre el cierre.
    despues = servicios.proyectos.listar_proyectos(empresa.admin)[0]["avance"]

    assert repos.actividades.find_by_id(pendiente["id"])["fecha_programada"] == MANANA
    assert despues == antes
    assert despues["porcentaje"] == 50


def test_consultar_un_proyecto_tambien_cierra_la_jornada(servicios, empresa, crear_actividad, reloj):
    proyecto = servicios.proyectos.crear_proyecto({"nombre": "Montaje"}, empresa.admin)
    crear_actividad([empresa.ana], proyecto_id=proyecto["id"], hora_programada="09:00")
    reloj.avanzar(UN_DIA)

    vista = servicios.proyectos.obtener_proyecto(proyecto["id"], empresa.admin)

    assert [a["estado"] for a in vista["actividades"]] == ["NO_REALIZADA"]
    assert vista["avance"]["actividades"] == 1    # La No realizada se queda en el total.


# ---------- Por la API ----------

def test_por_la_api_el_operario_ve_la_reprogramada_con_su_pausa(cliente_de, servicios, empresa, crear_actividad, reloj):
    actividad = crear_actividad([empresa.ana])
    iniciar_una_hora_antes_de_la_medianoche(servicios, reloj, actividad, empresa.ana)
    ana = cliente_de(empresa.ana)

    listado = ana.get("/actividades").get_json()
    carga = ana.get(f"/analisis/carga?desde={HOY}&hasta={MANANA}").get_json()

    assert [(a["fecha_programada"], a["reprogramada"], a["dias_de_retraso"]) for a in listado] == [(MANANA, True, 1)]
    assert listado[0]["ejecucion"]["pausas"][0]["motivo"] == "Fin de jornada"
    assert [jornada["fecha"] for jornada in carga["operarios"][0]["jornadas"]] == [MANANA]
    assert ana.post(f"/actividades/{actividad['id']}/reanudar").get_json()["estado"] == "EN_EJECUCION"
