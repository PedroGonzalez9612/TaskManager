"""Presencia y carga de una persona en su jornada (alcance, Sección 5.1): si está y cuánto trabajo
tiene, con una sola regla para todo el sistema. Las usan la barra del Operario, la asistencia y la
pantalla Hoy del Administrador, así que todas dicen lo mismo con el mismo nombre.

Son funciones puras: no leen la base de datos ni el reloj."""
from app.models.enums import EstadoCarga, EstadoPresencia
from app.models.pausa import en_utc, minutos_entre

# Minutos desde el inicio del turno antes de considerar que la persona llegó tarde.
TOLERANCIA_ENTRADA_MIN = 10
# Tiempo libre desde el que una persona tiene espacio para recibir más trabajo.
ESPACIO_MINIMO_MIN = 60


def _minutos(desde, hasta) -> int:
    return int(minutos_entre(desde, hasta))


def presencia_en_jornada(turno, asistencia, ahora, es_jornada_vigente: bool = True) -> dict:
    """{"estado": EstadoPresencia, "minutos": int} de una persona en una jornada.

    "turno" es (inicio, fin) del turno en esa jornada, en UTC, o None si no tenía. "asistencia" es su
    Asistencia de esa jornada, o None. "es_jornada_vigente" es False para una jornada que ya pasó.
    "minutos" depende del estado: cuánto lleva de llegada tarde, cuánto lleva de tiempo adicional o,
    en una jornada terminada, cuántos minutos antes del fin del turno salió (salida anticipada)."""
    ahora = en_utc(ahora)
    inicio, fin = (en_utc(turno[0]), en_utc(turno[1])) if turno else (None, None)

    if asistencia is not None:
        if asistencia.salida is not None:
            return {"estado": EstadoPresencia.JORNADA_TERMINADA, "minutos": asistencia.minutos_de_salida_anticipada(fin)}
        if not es_jornada_vigente:
            return {"estado": EstadoPresencia.SIN_SALIDA, "minutos": 0}
        if fin is not None and ahora >= fin:
            return {"estado": EstadoPresencia.TIEMPO_ADICIONAL, "minutos": _minutos(fin, ahora)}
        return {"estado": EstadoPresencia.EN_TURNO, "minutos": 0}

    if inicio is None:
        return {"estado": EstadoPresencia.SIN_TURNO, "minutos": 0}
    if ahora >= fin or not es_jornada_vigente:
        return {"estado": EstadoPresencia.NO_VINO, "minutos": 0}
    tarde = _minutos(inicio, ahora)
    if tarde > TOLERANCIA_ENTRADA_MIN:
        return {"estado": EstadoPresencia.LLEGADA_TARDE, "minutos": tarde}
    return {"estado": EstadoPresencia.POR_LLEGAR, "minutos": 0}


def estado_de_carga(minutos: int, capacidad_min: int) -> EstadoCarga:
    """Sobrecargado si el trabajo pasa de su capacidad; con espacio si le queda 1 hora libre o más."""
    if minutos > capacidad_min:
        return EstadoCarga.SOBRECARGADO
    if capacidad_min - minutos >= ESPACIO_MINIMO_MIN:
        return EstadoCarga.CON_ESPACIO
    return EstadoCarga.NORMAL
