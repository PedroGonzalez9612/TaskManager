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
    PENDIENTE = "PENDIENTE"
    ASIGNADA = "ASIGNADA"
    EN_EJECUCION = "EN_EJECUCION"
    COMPLETADA = "COMPLETADA"


class EstadoEjecucion(str, Enum):
    NO_INICIADA = "NO_INICIADA"
    EN_PROGRESO = "EN_PROGRESO"
    FINALIZADA = "FINALIZADA"
