from enum import Enum


class Rol(str, Enum):
    SUPERADMIN = "SUPERADMIN"
    ADMINISTRADOR = "ADMINISTRADOR"
    OPERARIO = "OPERARIO"


class Prioridad(str, Enum):
    BAJA = "BAJA"
    MEDIA = "MEDIA"
    ALTA = "ALTA"
    URGENTE = "URGENTE"  # Interrumpe la actividad que el operario tenga en curso.

    @property
    def peso(self) -> int:
        """Orden numérico de la prioridad: se ordena por este valor, nunca comparando textos."""
        return _PESO_PRIORIDAD[self.value]


_PESO_PRIORIDAD = {"BAJA": 1, "MEDIA": 2, "ALTA": 3, "URGENTE": 4}


class Categoria(str, Enum):
    PRODUCCION = "PRODUCCION"
    MANTENIMIENTO = "MANTENIMIENTO"
    CALIDAD = "CALIDAD"
    LIMPIEZA = "LIMPIEZA"
    LOGISTICA = "LOGISTICA"


class EstadoRequerimiento(str, Enum):
    ABIERTO = "ABIERTO"
    EN_PROCESO = "EN_PROCESO"
    CERRADO = "CERRADO"


class EstadoActividad(str, Enum):
    PENDIENTE = "PENDIENTE"            # Sin operarios asignados.
    ASIGNADA = "ASIGNADA"              # Con operarios; ninguno la tiene en curso ni pausada.
    EN_EJECUCION = "EN_EJECUCION"      # Al menos un operario la tiene en curso.
    PAUSADA = "PAUSADA"                # Nadie la tiene en curso y al menos uno la pausó.
    DEVUELTA = "DEVUELTA"              # El último operario asignado la devolvió al Administrador.
    COMPLETADA = "COMPLETADA"          # Final: todos los asignados la finalizaron.
    NO_REALIZADA = "NO_REALIZADA"      # Final: era de hora fija y no se terminó en su día.
    CANCELADA = "CANCELADA"            # Final: la canceló el Administrador, con motivo.

    @property
    def es_final(self) -> bool:
        """Un estado final ya no cambia: la actividad no se edita, no se reasigna y no se cancela."""
        return self in (EstadoActividad.COMPLETADA, EstadoActividad.NO_REALIZADA, EstadoActividad.CANCELADA)


class EstadoEjecucion(str, Enum):
    """La ejecución nace cuando el operario inicia, por eso no existe un estado "no iniciada"."""
    EN_PROGRESO = "EN_PROGRESO"
    PAUSADA = "PAUSADA"
    FINALIZADA = "FINALIZADA"          # El operario la terminó.
    CERRADA = "CERRADA"                # Terminó sin completarse: actividad cancelada, no realizada u operario retirado.

    @property
    def esta_abierta(self) -> bool:
        return self in (EstadoEjecucion.EN_PROGRESO, EstadoEjecucion.PAUSADA)


class EstadoAsignacion(str, Enum):
    """Una asignación no se borra: se cierra, y queda como historial."""
    ACTIVA = "ACTIVA"
    DEVUELTA = "DEVUELTA"              # El operario devolvió la actividad antes de iniciarla.
    RETIRADA = "RETIRADA"              # El Administrador le quitó la actividad.


# Motivos de pausa que el sistema conoce. Los demás los escribe el operario en "Otro" y quedan
# guardados en el catálogo de su empresa (alcance, Sección 5.1).
MOTIVO_PAUSA_URGENTE = "Actividad urgente"
MOTIVO_PAUSA_HORA_FIJA = "Actividad de hora fija"
MOTIVO_PAUSA_FIN_JORNADA = "Fin de jornada"
MOTIVOS_PAUSA_FIJOS = (MOTIVO_PAUSA_URGENTE, MOTIVO_PAUSA_HORA_FIJA, MOTIVO_PAUSA_FIN_JORNADA)

# Motivos para devolver una actividad. Esta lista es fija; con "Otro" el operario escribe el suyo.
MOTIVOS_DEVOLUCION = (
    "Falta información",
    "Me la asignaron por error",
    "Falta herramienta o material",
    "El equipo no está disponible",
)


class TipoCatalogo(str, Enum):
    """Listas desplegables por empresa que se van llenando con lo que se escribe en "Otro"."""
    MOTIVO_PAUSA = "MOTIVO_PAUSA"
    MOTIVO_CANCELACION = "MOTIVO_CANCELACION"
