from enum import Enum


class Rol(str, Enum):
    SUPERADMIN = "SUPERADMIN"
    ADMINISTRADOR = "ADMINISTRADOR"
    OPERARIO = "OPERARIO"


class Prioridad(str, Enum):
    ALTA = "ALTA"
    MEDIA = "MEDIA"
    BAJA = "BAJA"


class EstadoRequerimiento(str, Enum):
    ABIERTO = "ABIERTO"
    EN_PROCESO = "EN_PROCESO"
    CERRADO = "CERRADO"


class EstadoActividad(str, Enum):
    PENDIENTE = "PENDIENTE"
    ASIGNADA = "ASIGNADA"
    EN_EJECUCION = "EN_EJECUCION"
    COMPLETADA = "COMPLETADA"


class EstadoEjecucion(str, Enum):
    NO_INICIADA = "NO_INICIADA"
    EN_PROGRESO = "EN_PROGRESO"
    FINALIZADA = "FINALIZADA"
