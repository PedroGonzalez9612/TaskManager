"""Pruebas de la programación dinámica del día: lo ejecutado se mide con sus horas reales y lo
pendiente se reacomoda. Son funciones puras: no usan base de datos.

La jornada es el 10 de octubre en Bogotá (UTC-5). "Ahora" son las 10:00 de allá (15:00 UTC)."""
from datetime import datetime, timedelta, timezone

from app.models.orden_jornada import OrdenJornada, orden_sugerido
from app.services.programacion_dia import programar_dia

FECHA = "2026-10-10"
ZONA = "America/Bogota"
CAPACIDAD = 420
PESOS = {"BAJA": 1, "MEDIA": 2, "ALTA": 3, "URGENTE": 4}


def hora(texto):
    """Una hora de Bogotá del día de la jornada, como momento en UTC. "10:00" -> 15:00 UTC."""
    horas, minutos = map(int, texto.split(":"))
    return datetime(2026, 10, 10, horas, minutos, tzinfo=timezone.utc) + timedelta(hours=5)


AHORA = hora("10:00")


def actividad(ident, estado="ASIGNADA", estimado=60, prioridad="MEDIA", fija=None, inicio=None, fin=None, real=0):
    ejecucion = None
    if inicio:
        ejecucion = {"fecha_inicio": hora(inicio), "fecha_fin": hora(fin) if fin else None, "tiempo_real_min": real}
    return {"id": ident, "estado": estado, "tiempo_estimado_min": estimado, "prioridad": prioridad,
            "peso_prioridad": PESOS[prioridad], "hora_programada": fija, "dias_de_retraso": 0, "ejecucion": ejecucion}


def programar(actividades, orden_ids=()):
    return programar_dia(actividades, OrdenJornada("carlos", FECHA, orden_ids), AHORA, FECHA, ZONA, CAPACIDAD)


def tramos(resultado):
    """{id: (inicio, fin)} con las horas en texto de Bogotá, para leer las pruebas con facilidad."""
    local = lambda momento: (momento - timedelta(hours=5)).strftime("%H:%M")
    return {t["actividad_id"]: (local(t["inicio"]), local(t["fin"])) for t in resultado["tramos"]}


def tramo(resultado, ident):
    return next(t for t in resultado["tramos"] if t["actividad_id"] == ident)


# ---------- Lo ejecutado: horas reales, no el estimado ----------

def test_lo_terminado_ocupa_el_tiempo_que_realmente_tomo():
    # Estimada en 2 horas, se hizo en 45 minutos.
    hecha = actividad("a", "COMPLETADA", estimado=120, inicio="08:00", fin="08:45", real=45)
    resultado = programar([hecha])
    assert tramos(resultado) == {"a": ("08:00", "08:45")}
    assert tramo(resultado, "a")["tipo"] == "FINALIZADA"
    assert resultado["resumen"]["trabajado_min"] == 45


def test_lo_que_esta_en_curso_va_de_su_inicio_real_a_un_fin_proyectado():
    # Empezó a las 09:30, lleva 30 minutos de 90: le falta una hora.
    en_curso = actividad("a", "EN_EJECUCION", estimado=90, inicio="09:30", real=30)
    resultado = programar([en_curso])
    assert tramos(resultado) == {"a": ("09:30", "11:00")}
    assert tramo(resultado, "a")["tipo"] == "EN_CURSO"


def test_si_se_paso_del_estimado_el_fin_proyectado_es_ahora():
    en_curso = actividad("a", "EN_EJECUCION", estimado=30, inicio="08:00", real=120)
    assert tramos(programar([en_curso])) == {"a": ("08:00", "10:00")}


# ---------- Lo pendiente se reacomoda ----------

def test_sin_nada_en_curso_lo_pendiente_empieza_ahora():
    resultado = programar([actividad("a", estimado=60), actividad("b", estimado=30)])
    assert tramos(resultado) == {"a": ("10:00", "11:00"), "b": ("11:00", "11:30")}
    assert tramo(resultado, "a")["aproximada"] is True


def test_si_una_termina_antes_las_siguientes_se_adelantan():
    siguiente = actividad("b", estimado=60)
    # La primera, estimada en 3 horas, sigue en curso: la siguiente iría a las 12:00.
    lenta = actividad("a", "EN_EJECUCION", estimado=180, inicio="09:00", real=60)
    assert tramos(programar([lenta, siguiente]))["b"] == ("12:00", "13:00")
    # La misma, pero terminó a las 09:40: la siguiente empieza ahora.
    rapida = actividad("a", "COMPLETADA", estimado=180, inicio="09:00", fin="09:40", real=40)
    assert tramos(programar([rapida, siguiente]))["b"] == ("10:00", "11:00")


def test_si_una_se_demora_las_siguientes_se_corren():
    demorada = actividad("a", "EN_EJECUCION", estimado=30, inicio="07:00", real=180)
    siguiente = actividad("b", estimado=60)
    assert tramos(programar([demorada, siguiente]))["b"] == ("10:00", "11:00")


def test_a_una_pausada_solo_le_falta_lo_que_no_se_ha_hecho():
    pausada = actividad("a", "PAUSADA", estimado=90, inicio="08:00", real=60)
    assert tramos(programar([pausada])) == {"a": ("10:00", "10:30")}


# ---------- Hora fija ----------

def test_la_hora_fija_no_se_mueve_y_las_flexibles_la_rodean():
    fija = actividad("fija", estimado=60, fija="11:00")
    corta = actividad("corta", estimado=45, prioridad="BAJA")
    larga = actividad("larga", estimado=120, prioridad="ALTA")
    resultado = programar([fija, corta, larga])
    # La larga (más prioridad) no alcanza antes de las 11:00: va después de la fija. La corta sí alcanza.
    assert tramos(resultado) == {
        "fija": ("11:00", "12:00"), "larga": ("12:00", "14:00"), "corta": ("14:00", "14:45")}
    assert tramo(resultado, "fija")["aproximada"] is False


def test_una_flexible_entra_antes_de_la_fija_si_alcanza_a_terminar():
    fija = actividad("fija", estimado=60, fija="11:00")
    corta = actividad("corta", estimado=45)
    assert tramos(programar([fija, corta])) == {"corta": ("10:00", "10:45"), "fija": ("11:00", "12:00")}


def test_una_hora_fija_que_ya_paso_sin_iniciarse_queda_vencida():
    vencida = actividad("fija", estimado=60, fija="08:00")
    resultado = programar([vencida, actividad("b", estimado=30)])
    assert tramo(resultado, "fija")["vencida"] is True
    assert tramos(resultado)["b"] == ("10:00", "10:30")     # No le quita tiempo a lo que sigue.
    assert tramo(resultado, "b")["siguiente"] is True


# ---------- Urgente ----------

def test_la_urgente_interrumpe_lo_que_esta_en_curso():
    en_curso = actividad("a", "EN_EJECUCION", estimado=120, inicio="09:00", real=60)
    urgente = actividad("u", estimado=30, prioridad="URGENTE")
    resultado = programar([en_curso, urgente, actividad("b", estimado=60)])
    # La urgente empieza ahora; lo que estaba en curso se retoma después y termina media hora más tarde.
    assert tramos(resultado) == {"a": ("09:00", "11:30"), "u": ("10:00", "10:30"), "b": ("11:30", "12:30")}
    assert tramo(resultado, "u")["interrumpe"] is True
    assert tramo(resultado, "u")["siguiente"] is True


def test_la_urgente_no_interrumpe_una_de_hora_fija():
    fija = actividad("fija", "EN_EJECUCION", estimado=60, fija="09:30", inicio="09:30", real=30)
    urgente = actividad("u", estimado=30, prioridad="URGENTE")
    resultado = programar([fija, urgente])
    assert tramos(resultado) == {"fija": ("09:30", "10:30"), "u": ("10:30", "11:00")}
    assert tramo(resultado, "u")["interrumpe"] is False


# ---------- Orden del día ----------

def test_el_orden_sugerido_es_prioridad_luego_hora_luego_retraso():
    baja = actividad("baja", prioridad="BAJA")
    alta = actividad("alta", prioridad="ALTA")
    con_retraso = {**actividad("retraso", prioridad="ALTA"), "dias_de_retraso": 2}
    alta_con_hora = actividad("con_hora", prioridad="ALTA", fija="09:00")
    ordenadas = orden_sugerido([baja, alta, con_retraso, alta_con_hora])
    assert [a["id"] for a in ordenadas] == ["con_hora", "retraso", "alta", "baja"]


def test_el_orden_que_eligio_el_operario_se_respeta():
    a, b, c = actividad("a", prioridad="ALTA"), actividad("b", prioridad="MEDIA"), actividad("c", prioridad="BAJA")
    assert list(tramos(programar([a, b, c]))) == ["a", "b", "c"]                       # Sugerido.
    assert list(tramos(programar([a, b, c], orden_ids=["c", "a", "b"]))) == ["c", "a", "b"]


def test_lo_que_no_esta_en_el_orden_elegido_va_despues_y_los_ids_viejos_se_ignoran():
    a, b, nueva = actividad("a", prioridad="BAJA"), actividad("b", prioridad="BAJA"), actividad("nueva", prioridad="ALTA")
    orden = OrdenJornada("carlos", FECHA, ["b", "ya-no-existe", "a", "b"])
    assert orden.actividad_ids == ["b", "ya-no-existe", "a"]
    assert [x["id"] for x in orden.aplicar([a, b, nueva])] == ["b", "a", "nueva"]
    assert orden.es_personalizado is True
    assert OrdenJornada("carlos", FECHA).es_personalizado is False


def test_el_orden_se_guarda_y_se_reconstruye_igual():
    orden = OrdenJornada("carlos", FECHA, ["b", "a"], fecha_actualizacion=AHORA)
    copia = OrdenJornada.desde_documento({"_id": "x1", **orden.to_dict()})
    assert copia.to_dict() == orden.to_dict()


# ---------- Resumen de la jornada ----------

def test_el_tiempo_disponible_usa_lo_real_trabajado_y_lo_que_falta():
    hecha = actividad("a", "COMPLETADA", estimado=120, inicio="08:00", fin="08:45", real=45)    # 45 reales.
    en_curso = actividad("b", "EN_EJECUCION", estimado=90, inicio="09:30", real=30)              # 30 y faltan 60.
    pendiente = actividad("c", estimado=60)                                                      # Faltan 60.
    resumen = programar([hecha, en_curso, pendiente])["resumen"]
    assert resumen == {
        "trabajado_min": 75, "pendiente_min": 120, "capacidad_min": 420, "disponible_min": 225,
        "fin_proyectado": hora("12:00"),
    }


def test_un_dia_sin_actividades():
    assert programar([]) == {"tramos": [], "resumen": {
        "trabajado_min": 0, "pendiente_min": 0, "capacidad_min": 420, "disponible_min": 420, "fin_proyectado": None}}


def test_lo_que_empezaria_despues_de_la_medianoche_queda_fuera_de_la_jornada():
    resultado = programar([actividad("a", estimado=14 * 60), actividad("b", estimado=60)])
    assert tramo(resultado, "a")["fuera_de_jornada"] is False
    assert tramo(resultado, "b")["fuera_de_jornada"] is True


def test_las_canceladas_y_no_realizadas_no_entran_en_la_programacion():
    cancelada = actividad("x", "CANCELADA")
    no_realizada = actividad("y", "NO_REALIZADA", fija="08:00")
    assert programar([cancelada, no_realizada])["tramos"] == []


def test_una_finalizada_sin_registro_de_tiempo_se_ubica_en_su_hora():
    antigua = actividad("a", "COMPLETADA", fija="07:00")
    assert tramos(programar([antigua])) == {"a": ("07:00", "07:00")}


def test_acepta_las_fechas_sin_zona_que_devuelve_mongo():
    en_curso = actividad("a", "EN_EJECUCION", estimado=90, inicio="09:30", real=30)
    en_curso["ejecucion"]["fecha_inicio"] = en_curso["ejecucion"]["fecha_inicio"].replace(tzinfo=None)
    assert tramos(programar([en_curso])) == {"a": ("09:30", "11:00")}
