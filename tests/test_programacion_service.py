"""Pruebas de la programación del día y del orden del día (alcance, Sección 5.1), por el servicio
y por la API. El reloj empieza el 2026-10-10 a las 08:00 UTC: las 03:00 en Bogotá."""
from datetime import datetime, timedelta, timezone

import pytest

from app.repositories.orden_jornada_repository import OrdenJornadaRepository
from app.utils.errors import NotFoundError, ProhibidoError, ValidationError

from tests.conftest import HOY

INICIO = datetime(2026, 10, 10, 8, 0, tzinfo=timezone.utc)


def a_los(minutos):
    return INICIO + timedelta(minutes=minutos)


def orden_de(programacion):
    """Los ids de las actividades en el orden en que quedaron programadas."""
    return [tramo["actividad_id"] for tramo in programacion["tramos"]]


def tramo_de(programacion, actividad):
    return next(tramo for tramo in programacion["tramos"] if tramo["actividad_id"] == actividad["id"])


def horas_de(programacion, actividad):
    tramo = tramo_de(programacion, actividad)
    return tramo["inicio"], tramo["fin"]


@pytest.fixture
def ordenes(db):
    return OrdenJornadaRepository(db)


@pytest.fixture
def tres_flexibles(empresa, crear_actividad):
    """Tres actividades de horario flexible de Ana: de prioridad alta, media y baja."""
    return [
        crear_actividad([empresa.ana], titulo=prioridad, prioridad=prioridad)
        for prioridad in ("ALTA", "MEDIA", "BAJA")
    ]


# ---------- Orden del día ----------

def test_sin_orden_guardado_vale_el_sugerido(servicios, empresa, tres_flexibles):
    alta, media, baja = tres_flexibles
    programacion = servicios.programacion.consultar(empresa.ana)
    assert orden_de(programacion) == [alta["id"], media["id"], baja["id"]]
    assert programacion["orden_personalizado"] is False
    assert programacion["fecha"] == HOY
    assert programacion["operario_id"] == empresa.ana["id"]
    assert {actividad["id"] for actividad in programacion["actividades"]} == {alta["id"], media["id"], baja["id"]}


def test_la_programacion_respeta_el_orden_que_guardo_el_operario(servicios, empresa, tres_flexibles):
    alta, media, baja = tres_flexibles
    elegido = [baja["id"], alta["id"], media["id"]]
    guardada = servicios.programacion.guardar_orden(empresa.ana, elegido)
    assert orden_de(guardada) == elegido
    assert guardada["orden_personalizado"] is True

    consultada = servicios.programacion.consultar(empresa.ana)
    assert orden_de(consultada) == elegido
    assert consultada["orden_personalizado"] is True


def test_el_orden_guarda_la_hora_del_servidor(servicios, empresa, tres_flexibles, ordenes, reloj):
    reloj.avanzar(10)
    servicios.programacion.guardar_orden(empresa.ana, [tres_flexibles[2]["id"]])
    guardado = ordenes.find_de_usuario(empresa.ana["id"], HOY)
    assert guardado["actividad_ids"] == [tres_flexibles[2]["id"]]
    assert guardado["fecha_actualizacion"].replace(tzinfo=timezone.utc) == a_los(10)


def test_al_restablecer_vuelve_el_orden_sugerido(servicios, empresa, tres_flexibles, ordenes):
    alta, media, baja = tres_flexibles
    servicios.programacion.guardar_orden(empresa.ana, [baja["id"], media["id"], alta["id"]])
    restablecida = servicios.programacion.restablecer_orden(empresa.ana)
    assert orden_de(restablecida) == [alta["id"], media["id"], baja["id"]]
    assert restablecida["orden_personalizado"] is False
    assert ordenes.find_de_usuario(empresa.ana["id"], HOY) is None


def test_guardar_una_lista_vacia_equivale_a_restablecer(servicios, empresa, tres_flexibles, ordenes):
    servicios.programacion.guardar_orden(empresa.ana, [tres_flexibles[2]["id"]])
    programacion = servicios.programacion.guardar_orden(empresa.ana, [])
    assert programacion["orden_personalizado"] is False
    assert ordenes.find_de_usuario(empresa.ana["id"], HOY) is None


def test_guardar_otro_orden_reemplaza_el_anterior(servicios, empresa, tres_flexibles, ordenes):
    alta, media, baja = tres_flexibles
    servicios.programacion.guardar_orden(empresa.ana, [baja["id"], alta["id"]])
    programacion = servicios.programacion.guardar_orden(empresa.ana, [media["id"], baja["id"]])
    assert orden_de(programacion) == [media["id"], baja["id"], alta["id"]]
    assert ordenes.collection.count_documents({}) == 1


def test_el_orden_de_un_operario_no_cambia_el_de_otro(servicios, empresa, crear_actividad):
    alta = crear_actividad([empresa.ana, empresa.luis], prioridad="ALTA")
    baja = crear_actividad([empresa.ana, empresa.luis], prioridad="BAJA")
    servicios.programacion.guardar_orden(empresa.ana, [baja["id"], alta["id"]])
    assert orden_de(servicios.programacion.consultar(empresa.ana)) == [baja["id"], alta["id"]]
    de_luis = servicios.programacion.consultar(empresa.luis)
    assert orden_de(de_luis) == [alta["id"], baja["id"]]
    assert de_luis["orden_personalizado"] is False


def test_una_actividad_asignada_despues_va_tras_las_ordenadas(servicios, empresa, crear_actividad):
    primera = crear_actividad([empresa.ana], prioridad="BAJA")
    segunda = crear_actividad([empresa.ana], prioridad="BAJA")
    servicios.programacion.guardar_orden(empresa.ana, [segunda["id"], primera["id"]])
    # Llegan dos más, de mayor prioridad: no desplazan lo que el operario ya acomodó.
    nueva_media = crear_actividad([empresa.ana], prioridad="MEDIA")
    nueva_alta = crear_actividad([empresa.ana], prioridad="ALTA")
    programacion = servicios.programacion.consultar(empresa.ana)
    assert orden_de(programacion) == [segunda["id"], primera["id"], nueva_alta["id"], nueva_media["id"]]


def test_al_dia_siguiente_el_orden_de_ayer_no_aplica(servicios, empresa, tres_flexibles, reloj):
    alta, media, baja = tres_flexibles
    servicios.programacion.guardar_orden(empresa.ana, [baja["id"], media["id"], alta["id"]])
    reloj.avanzar(24 * 60)
    # Las tres quedan reprogramadas para hoy y empiezan otra vez en el orden sugerido.
    programacion = servicios.programacion.consultar(empresa.ana)
    assert programacion["fecha"] == "2026-10-11"
    assert orden_de(programacion) == [alta["id"], media["id"], baja["id"]]
    assert programacion["orden_personalizado"] is False


# ---------- Lo que no se puede ordenar ----------

def _guardar_rechazado(servicios, operario, actividad_ids) -> str:
    with pytest.raises(ValidationError) as error:
        servicios.programacion.guardar_orden(operario, actividad_ids)
    return str(error.value)


def test_no_se_ordena_una_actividad_de_hora_fija(servicios, empresa, crear_actividad, ordenes):
    flexible = crear_actividad([empresa.ana])
    fija = crear_actividad([empresa.ana], hora_programada="14:00")
    mensaje = _guardar_rechazado(servicios, empresa.ana, [flexible["id"], fija["id"]])
    assert mensaje == "Solo se pueden ordenar las actividades de horario flexible"
    assert ordenes.find_de_usuario(empresa.ana["id"], HOY) is None


def test_no_se_ordena_una_actividad_urgente(servicios, empresa, crear_actividad, ordenes):
    urgente = crear_actividad([empresa.ana], prioridad="URGENTE")
    mensaje = _guardar_rechazado(servicios, empresa.ana, [urgente["id"]])
    assert mensaje == "Las actividades urgentes no se reordenan"
    assert ordenes.find_de_usuario(empresa.ana["id"], HOY) is None


def test_no_se_ordena_la_actividad_de_otro_operario(servicios, empresa, crear_actividad, ordenes):
    de_luis = crear_actividad([empresa.luis])
    mensaje = _guardar_rechazado(servicios, empresa.ana, [de_luis["id"]])
    assert mensaje == "Esa actividad no es tuya o no es de hoy"
    assert ordenes.find_de_usuario(empresa.ana["id"], HOY) is None


def test_no_se_ordena_una_actividad_de_otro_dia(servicios, empresa, crear_actividad):
    de_manana = crear_actividad([empresa.ana], fecha_programada="2026-10-11")
    assert _guardar_rechazado(servicios, empresa.ana, [de_manana["id"]]) == "Esa actividad no es tuya o no es de hoy"


def test_no_se_ordena_un_id_que_no_existe(servicios, empresa, tres_flexibles, ordenes):
    mensaje = _guardar_rechazado(servicios, empresa.ana, [tres_flexibles[0]["id"], "no-existe"])
    assert mensaje == "Esa actividad no es tuya o no es de hoy"
    assert ordenes.find_de_usuario(empresa.ana["id"], HOY) is None


def test_no_se_ordena_una_actividad_finalizada(servicios, empresa, crear_actividad, ordenes):
    hecha = crear_actividad([empresa.ana])
    servicios.ejecucion.iniciar(hecha["id"], empresa.ana)
    servicios.ejecucion.finalizar(hecha["id"], empresa.ana)
    mensaje = _guardar_rechazado(servicios, empresa.ana, [hecha["id"]])
    assert mensaje == "Solo se ordena lo que está pendiente"
    assert ordenes.find_de_usuario(empresa.ana["id"], HOY) is None


def test_no_se_ordena_la_actividad_que_esta_en_curso(servicios, empresa, crear_actividad):
    en_curso = crear_actividad([empresa.ana])
    servicios.ejecucion.iniciar(en_curso["id"], empresa.ana)
    assert _guardar_rechazado(servicios, empresa.ana, [en_curso["id"]]) == "Solo se ordena lo que está pendiente"


def test_una_actividad_pausada_si_se_puede_ordenar(servicios, empresa, crear_actividad):
    pausada = crear_actividad([empresa.ana], prioridad="ALTA")
    otra = crear_actividad([empresa.ana], prioridad="BAJA")
    servicios.ejecucion.iniciar(pausada["id"], empresa.ana)
    servicios.ejecucion.pausar(pausada["id"], empresa.ana, "Falta material")
    programacion = servicios.programacion.guardar_orden(empresa.ana, [otra["id"], pausada["id"]])
    assert orden_de(programacion) == [otra["id"], pausada["id"]]


@pytest.mark.parametrize("cuerpo", [None, "abc", {"a": 1}, [1, 2], [""], [None]])
def test_el_orden_debe_ser_una_lista_de_identificadores(servicios, empresa, tres_flexibles, ordenes, cuerpo):
    mensaje = _guardar_rechazado(servicios, empresa.ana, cuerpo)
    assert "lista" in mensaje
    assert ordenes.find_de_usuario(empresa.ana["id"], HOY) is None


def test_un_rechazo_no_cambia_el_orden_que_ya_estaba_guardado(servicios, empresa, tres_flexibles, ordenes):
    alta, media, baja = tres_flexibles
    servicios.programacion.guardar_orden(empresa.ana, [baja["id"], alta["id"]])
    _guardar_rechazado(servicios, empresa.ana, [media["id"], "no-existe"])
    assert ordenes.find_de_usuario(empresa.ana["id"], HOY)["actividad_ids"] == [baja["id"], alta["id"]]


def test_solo_el_operario_guarda_el_orden_del_dia(servicios, empresa):
    with pytest.raises(ProhibidoError):
        servicios.programacion.guardar_orden(empresa.admin, [])


def test_solo_el_operario_restablece_el_orden_del_dia(servicios, empresa):
    with pytest.raises(ProhibidoError):
        servicios.programacion.restablecer_orden(empresa.admin)


# ---------- Programación dinámica ----------

def test_lo_terminado_ocupa_su_tiempo_real_y_lo_siguiente_se_adelanta(servicios, empresa, crear_actividad, reloj):
    larga = crear_actividad([empresa.ana], prioridad="ALTA", tiempo_estimado_min=120)
    siguiente = crear_actividad([empresa.ana], prioridad="MEDIA", tiempo_estimado_min=60)
    servicios.ejecucion.iniciar(larga["id"], empresa.ana)
    reloj.avanzar(45)

    # En curso: va de su inicio real al fin proyectado (le faltan 75 min) y la siguiente espera.
    antes = servicios.programacion.consultar(empresa.ana)
    assert horas_de(antes, larga) == (a_los(0), a_los(120))
    assert tramo_de(antes, larga)["tipo"] == "EN_CURSO"
    assert horas_de(antes, siguiente) == (a_los(120), a_los(180))

    # Estimada en 120 min, se finaliza a los 45: el tiempo real no depende del estimado.
    finalizada = servicios.ejecucion.finalizar(larga["id"], empresa.ana)
    assert finalizada["ejecucion"]["tiempo_real_min"] == 45

    despues = servicios.programacion.consultar(empresa.ana)
    assert horas_de(despues, larga) == (a_los(0), a_los(45))
    assert tramo_de(despues, larga)["tipo"] == "FINALIZADA"
    assert horas_de(despues, siguiente) == (a_los(45), a_los(105))
    assert tramo_de(despues, siguiente)["siguiente"] is True
    presentada = next(a for a in despues["actividades"] if a["id"] == larga["id"])
    assert presentada["ejecucion"]["tiempo_real_min"] == 45


def test_el_tiempo_real_de_lo_finalizado_no_cambia_con_el_paso_de_las_horas(servicios, empresa, crear_actividad, reloj):
    hecha = crear_actividad([empresa.ana], tiempo_estimado_min=120)
    servicios.ejecucion.iniciar(hecha["id"], empresa.ana)
    reloj.avanzar(45)
    servicios.ejecucion.finalizar(hecha["id"], empresa.ana)
    reloj.avanzar(200)
    programacion = servicios.programacion.consultar(empresa.ana)
    assert horas_de(programacion, hecha) == (a_los(0), a_los(45))
    assert programacion["actividades"][0]["ejecucion"]["tiempo_real_min"] == 45
    assert programacion["resumen"]["trabajado_min"] == 45


def test_el_tiempo_real_descuenta_las_pausas_y_el_tramo_va_de_inicio_a_fin(servicios, empresa, crear_actividad, reloj):
    hecha = crear_actividad([empresa.ana], tiempo_estimado_min=120)
    servicios.ejecucion.iniciar(hecha["id"], empresa.ana)
    reloj.avanzar(20)
    servicios.ejecucion.pausar(hecha["id"], empresa.ana, "Falta material")
    reloj.avanzar(15)
    servicios.ejecucion.reanudar(hecha["id"], empresa.ana)
    reloj.avanzar(25)
    servicios.ejecucion.finalizar(hecha["id"], empresa.ana)
    programacion = servicios.programacion.consultar(empresa.ana)
    assert horas_de(programacion, hecha) == (a_los(0), a_los(60))
    assert programacion["resumen"]["trabajado_min"] == 45


def test_lo_que_se_paso_del_estimado_empuja_a_las_siguientes_hasta_ahora(servicios, empresa, crear_actividad, reloj):
    demorada = crear_actividad([empresa.ana], prioridad="ALTA", tiempo_estimado_min=30)
    siguiente = crear_actividad([empresa.ana], prioridad="MEDIA", tiempo_estimado_min=60)
    servicios.ejecucion.iniciar(demorada["id"], empresa.ana)
    reloj.avanzar(50)
    programacion = servicios.programacion.consultar(empresa.ana)
    assert horas_de(programacion, demorada) == (a_los(0), a_los(50))
    assert horas_de(programacion, siguiente) == (a_los(50), a_los(110))

    reloj.avanzar(10)    # Sigue sin terminar: la siguiente se corre otros diez minutos.
    assert horas_de(servicios.programacion.consultar(empresa.ana), siguiente) == (a_los(60), a_los(120))


def test_el_resumen_usa_lo_real_trabajado_y_lo_que_falta(servicios, empresa, crear_actividad, reloj):
    hecha = crear_actividad([empresa.ana], prioridad="ALTA", tiempo_estimado_min=120)
    en_curso = crear_actividad([empresa.ana], prioridad="MEDIA", tiempo_estimado_min=90)
    crear_actividad([empresa.ana], prioridad="BAJA", tiempo_estimado_min=60)
    servicios.ejecucion.iniciar(hecha["id"], empresa.ana)
    reloj.avanzar(45)
    servicios.ejecucion.finalizar(hecha["id"], empresa.ana)          # 45 reales de 120 estimados.
    servicios.ejecucion.iniciar(en_curso["id"], empresa.ana)
    reloj.avanzar(30)                                                # Lleva 30 y le faltan 60.

    resumen = servicios.programacion.consultar(empresa.ana)["resumen"]
    assert resumen == {
        "trabajado_min": 75, "pendiente_min": 120, "capacidad_min": 420, "disponible_min": 225,
        "fin_proyectado": a_los(195),
    }


def test_un_dia_sin_actividades(servicios, empresa):
    programacion = servicios.programacion.consultar(empresa.ana)
    assert programacion["tramos"] == []
    assert programacion["actividades"] == []
    assert programacion["resumen"]["disponible_min"] == 420
    assert programacion["resumen"]["fin_proyectado"] is None


def test_la_hora_fija_va_en_su_hora_y_las_flexibles_la_rodean(servicios, empresa, crear_actividad):
    # Son las 03:00 en Bogotá. La hora fija es a las 05:00 (10:00 UTC).
    fija = crear_actividad([empresa.ana], prioridad="BAJA", hora_programada="05:00", tiempo_estimado_min=60)
    larga = crear_actividad([empresa.ana], prioridad="MEDIA", tiempo_estimado_min=180)
    corta = crear_actividad([empresa.ana], prioridad="ALTA", tiempo_estimado_min=60)
    programacion = servicios.programacion.consultar(empresa.ana)
    # La corta alcanza antes de la hora fija; la larga no, y va después.
    assert orden_de(programacion) == [corta["id"], fija["id"], larga["id"]]
    assert horas_de(programacion, corta) == (a_los(0), a_los(60))
    assert horas_de(programacion, fija) == (a_los(120), a_los(180))
    assert horas_de(programacion, larga) == (a_los(180), a_los(360))
    assert tramo_de(programacion, fija)["hora_fija"] is True
    assert tramo_de(programacion, fija)["aproximada"] is False
    assert tramo_de(programacion, larga)["aproximada"] is True


def test_la_urgente_va_primero_aunque_el_orden_guardado_diga_otra_cosa(servicios, empresa, crear_actividad):
    flexible = crear_actividad([empresa.ana], prioridad="ALTA")
    servicios.programacion.guardar_orden(empresa.ana, [flexible["id"]])
    urgente = crear_actividad([empresa.ana], prioridad="URGENTE")
    assert orden_de(servicios.programacion.consultar(empresa.ana)) == [urgente["id"], flexible["id"]]


def test_solo_entran_las_actividades_de_hoy(servicios, empresa, crear_actividad):
    de_hoy = crear_actividad([empresa.ana])
    crear_actividad([empresa.ana], fecha_programada="2026-10-11")
    programacion = servicios.programacion.consultar(empresa.ana)
    assert orden_de(programacion) == [de_hoy["id"]]
    assert [actividad["id"] for actividad in programacion["actividades"]] == [de_hoy["id"]]


def test_hoy_es_el_dia_de_la_empresa_segun_su_zona_horaria(servicios, empresa, crear_actividad, reloj):
    actividad = crear_actividad([empresa.ana])
    reloj.avanzar(18 * 60)    # 02:00 UTC del día 11: en Bogotá todavía son las 21:00 del día 10.
    programacion = servicios.programacion.consultar(empresa.ana)
    assert programacion["fecha"] == HOY
    assert orden_de(programacion) == [actividad["id"]]


def test_cada_operario_ve_su_propio_avance_en_una_actividad_compartida(servicios, empresa, crear_actividad, reloj):
    compartida = crear_actividad([empresa.ana, empresa.luis], tiempo_estimado_min=60)
    servicios.ejecucion.iniciar(compartida["id"], empresa.ana)
    reloj.avanzar(20)
    assert tramo_de(servicios.programacion.consultar(empresa.ana), compartida)["tipo"] == "EN_CURSO"
    de_luis = servicios.programacion.consultar(empresa.luis)
    assert tramo_de(de_luis, compartida)["tipo"] == "PENDIENTE"
    assert de_luis["resumen"]["trabajado_min"] == 0


# ---------- Quién consulta ----------

def test_el_administrador_consulta_la_programacion_de_un_operario(servicios, empresa, crear_actividad, reloj):
    de_ana = crear_actividad([empresa.ana], tiempo_estimado_min=60)
    crear_actividad([empresa.luis])
    servicios.ejecucion.iniciar(de_ana["id"], empresa.ana)
    reloj.avanzar(20)

    programacion = servicios.programacion.consultar(empresa.admin, empresa.ana["id"])
    assert programacion["operario_id"] == empresa.ana["id"]
    assert orden_de(programacion) == [de_ana["id"]]
    assert tramo_de(programacion, de_ana)["tipo"] == "EN_CURSO"
    # Las actividades vienen con el estado personal de ese operario.
    assert programacion["actividades"][0]["estado"] == "EN_EJECUCION"
    assert programacion["actividades"][0]["ejecucion"]["tiempo_real_min"] == 20


def test_el_administrador_ve_el_orden_que_eligio_el_operario(servicios, empresa, tres_flexibles):
    alta, media, baja = tres_flexibles
    servicios.programacion.guardar_orden(empresa.ana, [baja["id"], media["id"], alta["id"]])
    programacion = servicios.programacion.consultar(empresa.admin, empresa.ana["id"])
    assert orden_de(programacion) == [baja["id"], media["id"], alta["id"]]
    assert programacion["orden_personalizado"] is True


def test_el_administrador_debe_indicar_el_operario(servicios, empresa):
    with pytest.raises(ValidationError):
        servicios.programacion.consultar(empresa.admin)


def test_el_administrador_no_ve_a_un_operario_de_otra_empresa(servicios, empresa, otra_empresa):
    with pytest.raises(NotFoundError):
        servicios.programacion.consultar(empresa.admin, otra_empresa.ivan["id"])


def test_la_programacion_es_solo_de_operarios(servicios, empresa):
    with pytest.raises(NotFoundError):
        servicios.programacion.consultar(empresa.admin, empresa.admin["id"])


@pytest.mark.parametrize("operario_id", ["no-existe", "0123456789abcdef01234567"])
def test_el_administrador_consulta_un_operario_que_no_existe(servicios, empresa, operario_id):
    with pytest.raises(NotFoundError):
        servicios.programacion.consultar(empresa.admin, operario_id)


def test_un_operario_siempre_recibe_su_propia_programacion(servicios, empresa, crear_actividad):
    de_ana = crear_actividad([empresa.ana])
    crear_actividad([empresa.luis])
    programacion = servicios.programacion.consultar(empresa.ana, empresa.luis["id"])
    assert programacion["operario_id"] == empresa.ana["id"]
    assert orden_de(programacion) == [de_ana["id"]]


# ---------- Por la API ----------

def test_la_api_entrega_la_programacion_del_dia(cliente_de, empresa, tres_flexibles):
    alta, media, baja = tres_flexibles
    respuesta = cliente_de(empresa.ana).get("/programacion-del-dia")
    assert respuesta.status_code == 200
    programacion = respuesta.get_json()
    assert set(programacion) == {"fecha", "operario_id", "orden_personalizado", "tramos", "resumen", "actividades",
                                 "turno", "asistencia", "en_turno"}
    assert orden_de(programacion) == [alta["id"], media["id"], baja["id"]]
    assert programacion["tramos"][0]["inicio"] == "Sat, 10 Oct 2026 08:00:00 GMT"
    assert programacion["resumen"]["pendiente_min"] == 180


def test_la_api_guarda_y_restablece_el_orden_del_dia(cliente_de, empresa, tres_flexibles):
    alta, media, baja = tres_flexibles
    ana = cliente_de(empresa.ana)
    elegido = [baja["id"], alta["id"], media["id"]]

    guardada = ana.put("/orden-del-dia", json={"actividad_ids": elegido})
    assert guardada.status_code == 200
    assert orden_de(guardada.get_json()) == elegido
    assert ana.get("/programacion-del-dia").get_json()["orden_personalizado"] is True

    restablecida = ana.delete("/orden-del-dia")
    assert restablecida.status_code == 200
    assert orden_de(restablecida.get_json()) == [alta["id"], media["id"], baja["id"]]
    assert restablecida.get_json()["orden_personalizado"] is False


@pytest.mark.parametrize("cuerpo", [{}, {"actividad_ids": "abc"}, ["suelto"], {"actividad_ids": ["no-existe"]}])
def test_la_api_rechaza_un_orden_que_no_es_valido(cliente_de, empresa, cuerpo):
    respuesta = cliente_de(empresa.ana).put("/orden-del-dia", json=cuerpo)
    assert respuesta.status_code == 400
    assert respuesta.get_json()["error"]


def test_la_api_rechaza_un_orden_sin_cuerpo(cliente_de, empresa):
    assert cliente_de(empresa.ana).put("/orden-del-dia").status_code == 400


def test_la_api_dice_que_regla_impide_ordenar(cliente_de, empresa, crear_actividad):
    urgente = crear_actividad([empresa.ana], prioridad="URGENTE")
    respuesta = cliente_de(empresa.ana).put("/orden-del-dia", json={"actividad_ids": [urgente["id"]]})
    assert respuesta.status_code == 400
    assert respuesta.get_json()["error"] == "Las actividades urgentes no se reordenan"


def test_la_api_entrega_al_administrador_la_programacion_de_un_operario(cliente_de, empresa, otra_empresa,
                                                                         crear_actividad):
    de_ana = crear_actividad([empresa.ana])
    marta = cliente_de(empresa.admin)

    respuesta = marta.get(f"/programacion-del-dia?operario_id={empresa.ana['id']}")
    assert respuesta.status_code == 200
    assert respuesta.get_json()["operario_id"] == empresa.ana["id"]
    assert orden_de(respuesta.get_json()) == [de_ana["id"]]

    assert marta.get("/programacion-del-dia").status_code == 400
    assert marta.get(f"/programacion-del-dia?operario_id={otra_empresa.ivan['id']}").status_code == 404
    assert marta.get(f"/programacion-del-dia?operario_id={empresa.admin['id']}").status_code == 404


def test_la_api_no_deja_que_un_operario_vea_la_programacion_de_otro(cliente_de, empresa, crear_actividad):
    crear_actividad([empresa.luis])
    respuesta = cliente_de(empresa.ana).get(f"/programacion-del-dia?operario_id={empresa.luis['id']}")
    assert respuesta.status_code == 200
    assert respuesta.get_json()["operario_id"] == empresa.ana["id"]
    assert respuesta.get_json()["tramos"] == []


@pytest.mark.parametrize("metodo, ruta", [
    ("get", "/programacion-del-dia"), ("put", "/orden-del-dia"), ("delete", "/orden-del-dia"),
])
def test_la_api_exige_sesion(cliente_de, metodo, ruta):
    respuesta = getattr(cliente_de(), metodo)(ruta)
    assert respuesta.status_code == 401
    assert respuesta.get_json()["error"]


@pytest.mark.parametrize("metodo", ["put", "delete"])
def test_el_administrador_no_cambia_el_orden_del_dia_de_nadie(cliente_de, empresa, metodo):
    respuesta = getattr(cliente_de(empresa.admin), metodo)("/orden-del-dia", json={"actividad_ids": []})
    assert respuesta.status_code == 403


def test_la_api_no_atiende_la_programacion_para_el_superadmin(cliente_de):
    superadmin = {"id": "s1", "nombre": "Sara", "rol": "SUPERADMIN", "empresa_id": None}
    assert cliente_de(superadmin).get("/programacion-del-dia").status_code == 403
