"""Programación dinámica del día de un operario (alcance, Sección 5.1).

La estimación y la ejecución son cosas distintas. Lo terminado ocupa el tiempo que realmente tomó
(de su inicio a su fin); lo que está en curso va de su inicio real a un fin proyectado (lo que le
falta del estimado); y lo pendiente se reacomoda desde que el operario queda libre. Si algo termina
antes, lo siguiente se adelanta; si se demora, se corre. Las de hora fija no se mueven.

El tiempo trabajado se atribuye a la jornada en que se trabajó: solo cuenta lo que cae dentro de la
ventana de la jornada, de su medianoche a su cierre (el mayor entre la medianoche siguiente y el fin
del turno). Así una actividad que empezó en una jornada y terminó en otra reparte su tiempo.

Es una función pura: recibe las actividades ya presentadas para el operario y la hora, y devuelve
la programación. No lee la base de datos ni el reloj."""
from datetime import timedelta

from app.models.ejecucion import minutos_trabajados_en
from app.models.enums import EstadoActividad, Prioridad
from app.models.pausa import en_utc
from app.utils.reloj import fin_del_dia, momento_local

FINALIZADA = "FINALIZADA"
EN_CURSO = "EN_CURSO"
PENDIENTE = "PENDIENTE"
ESTADOS_PENDIENTES = (EstadoActividad.ASIGNADA.value, EstadoActividad.PAUSADA.value)


def _minutos(cantidad) -> timedelta:
    return timedelta(minutes=cantidad)


def _trabajado(actividad: dict) -> int:
    """Minutos reales que el operario lleva en la actividad (0 si no la ha iniciado)."""
    return (actividad.get("ejecucion") or {}).get("tiempo_real_min") or 0


def _trabajado_en(actividad: dict, ventana: tuple, ahora) -> int:
    """Minutos que el operario trabajó en la actividad dentro de la ventana (desde, hasta) de la
    jornada. Sin hora de inicio registrada (datos anteriores), se usa su tiempo real completo."""
    ejecucion = actividad.get("ejecucion") or {}
    if not ejecucion.get("fecha_inicio"):
        return _trabajado(actividad)
    pausas = [(pausa["inicio"], pausa.get("fin")) for pausa in ejecucion.get("pausas") or []]
    return minutos_trabajados_en(ejecucion["fecha_inicio"], ejecucion.get("fecha_fin") or ahora, pausas, *ventana)


def _restante(actividad: dict) -> int:
    """Minutos que le faltan según el estimado. Lo que ya se pasó del estimado no resta: queda en 0."""
    return max(0, actividad["tiempo_estimado_min"] - _trabajado(actividad))


def _tramo(actividad: dict, tipo: str, inicio, fin, **datos) -> dict:
    return {
        "actividad_id": actividad["id"], "tipo": tipo, "inicio": inicio, "fin": fin,
        "hora_fija": bool(actividad.get("hora_programada")), "aproximada": False, "vencida": False,
        "interrumpe": False, "siguiente": False, **datos,
    }


def _tramo_finalizado(actividad: dict, fecha: str, zona, desde) -> dict:
    """Lo terminado ocupa sus horas reales, pero solo desde que empieza la jornada: si se inició en
    una jornada anterior, se dibuja la parte que cae en esta."""
    ejecucion = actividad.get("ejecucion") or {}
    if ejecucion.get("fecha_inicio") and ejecucion.get("fecha_fin"):
        inicio = max(en_utc(ejecucion["fecha_inicio"]), desde)
        return _tramo(actividad, FINALIZADA, inicio, max(inicio, en_utc(ejecucion["fecha_fin"])))
    # Datos anteriores, sin registro de tiempo: se ubica en su hora y no ocupa tiempo.
    momento = momento_local(fecha, actividad.get("hora_programada") or "00:00", zona)
    return _tramo(actividad, FINALIZADA, momento, momento)


def _ubicar_urgentes(urgentes: list, en_curso, tramo_en_curso, desde) -> tuple:
    """Las urgentes van primero, desde "desde". Interrumpen lo que el operario lleva, salvo que sea
    de hora fija: en ese caso esperan a que termine. Devuelve sus tramos y el momento en que el
    operario queda libre."""
    cursor = desde
    puede_interrumpir = not (en_curso and en_curso.get("hora_programada"))
    if tramo_en_curso and not puede_interrumpir:
        cursor = tramo_en_curso["fin"]

    tramos = []
    for urgente in urgentes:
        fin = cursor + _minutos(_restante(urgente))
        tramos.append(_tramo(urgente, PENDIENTE, cursor, fin, interrumpe=bool(en_curso) and puede_interrumpir))
        cursor = fin

    if tramo_en_curso and tramos and puede_interrumpir:
        # Lo que estaba en curso se retoma después de las urgentes.
        tramo_en_curso["fin"] = cursor + _minutos(_restante(en_curso))
    if tramo_en_curso:
        cursor = max(cursor, tramo_en_curso["fin"])
    return tramos, cursor


def _ubicar_pendientes(fijas: list, flexibles: list, libre_desde, ahora) -> list:
    """Las de hora fija van en su hora. Las de horario flexible llenan el tiempo que queda, en el
    orden recibido: una flexible entra antes de una fija solo si alcanza a terminar."""
    tramos = [_tramo(fija, PENDIENTE, fija["_inicio"], fija["_inicio"] + _minutos(_restante(fija)), vencida=True)
              for fija in fijas if fija["_inicio"] < ahora]
    futuras = [fija for fija in fijas if fija["_inicio"] >= ahora]
    cursor = libre_desde

    def poner_fija():
        nonlocal cursor
        fija = futuras.pop(0)
        fin = fija["_inicio"] + _minutos(_restante(fija))
        tramos.append(_tramo(fija, PENDIENTE, fija["_inicio"], fin))
        cursor = max(cursor, fin)

    for flexible in flexibles:
        duracion = _minutos(_restante(flexible))
        while futuras and cursor + duracion > futuras[0]["_inicio"]:
            poner_fija()
        tramos.append(_tramo(flexible, PENDIENTE, cursor, cursor + duracion, aproximada=True))
        cursor += duracion
    while futuras:
        poner_fija()
    return tramos


def _resumen(actividades: list, tramos: list, capacidad_min: int, ventana: tuple, ahora) -> dict:
    trabajado = sum(_trabajado_en(actividad, ventana, ahora) for actividad in actividades)
    pendiente = sum(_restante(actividad) for actividad in actividades
                    if actividad["estado"] != EstadoActividad.COMPLETADA.value)
    return {
        "trabajado_min": trabajado,
        "pendiente_min": pendiente,
        "capacidad_min": capacidad_min,
        "disponible_min": max(0, capacidad_min - trabajado - pendiente),
        "fin_proyectado": max((tramo["fin"] for tramo in tramos), default=None),
    }


def programar_dia(actividades: list, orden, ahora, fecha: str, zona, capacidad_min: int, cierre=None,
                  inicio_turno=None) -> dict:
    """Devuelve {"tramos": [...], "resumen": {...}} para la jornada "fecha" de un operario.

    "actividades" son las suyas de esa jornada, presentadas con su estado personal y su ejecución.
    "orden" es su OrdenJornada (el orden que eligió para las de horario flexible).
    "cierre" es el momento (UTC) en que termina la jornada: el mayor entre la medianoche siguiente
    y el fin de su turno. Sin él, la jornada termina a la medianoche siguiente.
    "inicio_turno" es el inicio de su turno (UTC). Si todavía no ha llegado y no hay nada en curso, lo
    pendiente se proyecta desde ahí y no desde ahora: la línea de tiempo sigue el orden de las horas.
    Cada tramo trae actividad_id, tipo (FINALIZADA, EN_CURSO o PENDIENTE), inicio y fin (reales o
    proyectados, en UTC) y estas marcas: hora_fija, aproximada (hora calculada, no fija), vencida
    (hora fija que ya pasó sin iniciarse), interrumpe (urgente que interrumpe lo que está en curso),
    siguiente (la próxima por hacer) y fuera_de_jornada (empezaría después de terminar la jornada).
    El resumen cuenta como trabajado solo lo que cae entre la medianoche de "fecha" y el cierre."""
    ahora = en_utc(ahora)
    ventana = (momento_local(fecha, "00:00", zona), cierre or fin_del_dia(fecha, zona))
    de_la_jornada = [a for a in actividades if a["estado"] in (
        EstadoActividad.COMPLETADA.value, EstadoActividad.EN_EJECUCION.value, *ESTADOS_PENDIENTES)]

    tramos = [_tramo_finalizado(a, fecha, zona, ventana[0]) for a in de_la_jornada
              if a["estado"] == EstadoActividad.COMPLETADA.value]

    en_curso = next((a for a in de_la_jornada if a["estado"] == EstadoActividad.EN_EJECUCION.value), None)
    tramo_en_curso = None
    if en_curso:
        inicio = max(en_utc(en_curso["ejecucion"]["fecha_inicio"]), ventana[0])
        tramo_en_curso = _tramo(en_curso, EN_CURSO, inicio, ahora + _minutos(_restante(en_curso)))
        tramos.append(tramo_en_curso)

    pendientes = [a for a in de_la_jornada if a["estado"] in ESTADOS_PENDIENTES]
    urgentes = [a for a in pendientes if a["prioridad"] == Prioridad.URGENTE.value]
    resto = [a for a in pendientes if a["prioridad"] != Prioridad.URGENTE.value]
    fijas = sorted(({**a, "_inicio": momento_local(fecha, a["hora_programada"], zona)}
                    for a in resto if a.get("hora_programada")), key=lambda a: a["_inicio"])
    flexibles = orden.aplicar([a for a in resto if not a.get("hora_programada")])

    desde = ahora
    if inicio_turno is not None and not en_curso:
        desde = max(ahora, en_utc(inicio_turno))
    tramos_urgentes, libre_desde = _ubicar_urgentes(urgentes, en_curso, tramo_en_curso, desde)
    por_hacer = tramos_urgentes + _ubicar_pendientes(fijas, flexibles, libre_desde, ahora)

    # La siguiente por hacer: la primera pendiente que no esté vencida, en orden de hora.
    vigentes = sorted((tramo for tramo in por_hacer if not tramo["vencida"]), key=lambda tramo: tramo["inicio"])
    if vigentes:
        vigentes[0]["siguiente"] = True

    tramos += por_hacer
    for tramo in tramos:
        tramo["fuera_de_jornada"] = tramo["tipo"] == PENDIENTE and tramo["inicio"] >= ventana[1]
    tramos.sort(key=lambda tramo: tramo["inicio"])
    return {"tramos": tramos, "resumen": _resumen(de_la_jornada, tramos, capacidad_min, ventana, ahora)}
