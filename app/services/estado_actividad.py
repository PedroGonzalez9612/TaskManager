"""Regla única del estado de una actividad (alcance, Sección 5.1).

La ejecución pertenece a cada operario asignado, así que el estado de la actividad no se cambia a
mano: se deduce de lo que lleva cada uno. Son funciones puras (no leen la base de datos ni el
reloj), para que la regla esté en un solo lugar y se pueda probar sola."""
from app.models.enums import EstadoActividad, EstadoEjecucion


def calcular_estado_actividad(estado_actual, estados_ejecucion: list, por_devolucion: bool = False) -> EstadoActividad:
    """Estado que le corresponde a la actividad.

    "estados_ejecucion" trae un elemento por cada asignación ACTIVA: el estado de la ejecución de
    ese operario, o None si todavía no ha iniciado. "por_devolucion" indica que se está calculando
    porque un operario acaba de devolver la orden.

    Un estado final ya no cambia. Una actividad queda DEVUELTA cuando el último operario asignado
    la devuelve, y sigue así mientras no tenga a nadie asignado: espera la decisión del
    Administrador. En cuanto él le asigna operarios, se calcula como cualquier otra."""
    estado_actual = EstadoActividad(estado_actual)
    if estado_actual.es_final:
        return estado_actual

    estados = [EstadoEjecucion(estado) if estado else None for estado in estados_ejecucion]
    if not estados:
        if por_devolucion or estado_actual == EstadoActividad.DEVUELTA:
            return EstadoActividad.DEVUELTA
        return EstadoActividad.PENDIENTE
    if all(estado == EstadoEjecucion.FINALIZADA for estado in estados):
        return EstadoActividad.COMPLETADA
    if EstadoEjecucion.EN_PROGRESO in estados:
        return EstadoActividad.EN_EJECUCION
    if EstadoEjecucion.PAUSADA in estados:
        return EstadoActividad.PAUSADA
    # Nadie ha iniciado, o unos ya finalizaron y otros no han iniciado.
    return EstadoActividad.ASIGNADA


_ESTADO_SEGUN_EJECUCION = {
    EstadoEjecucion.EN_PROGRESO: EstadoActividad.EN_EJECUCION,
    EstadoEjecucion.PAUSADA: EstadoActividad.PAUSADA,
    EstadoEjecucion.FINALIZADA: EstadoActividad.COMPLETADA,
}


def estado_para_operario(estado_general, estado_ejecucion) -> EstadoActividad:
    """Cómo ve la actividad UN operario: según su propia ejecución, sin depender de lo que hagan
    sus compañeros. "estado_ejecucion" es None si él todavía no ha iniciado.

    Si la actividad se cerró sin completarse (cancelada o no realizada) o está devuelta, todos
    ven ese mismo estado."""
    estado_general = EstadoActividad(estado_general)
    if estado_general == EstadoActividad.DEVUELTA:
        return estado_general
    if estado_general.es_final and estado_general != EstadoActividad.COMPLETADA:
        return estado_general
    if not estado_ejecucion:
        return EstadoActividad.ASIGNADA
    # Una ejecución CERRADA solo existe cuando la actividad terminó sin completarse.
    return _ESTADO_SEGUN_EJECUCION.get(EstadoEjecucion(estado_ejecucion), estado_general)
